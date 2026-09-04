import asyncio
from uuid import uuid4

import pytest

from maya.conversation.engine import ConversationEngine
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.manager import DefaultMemoryManager
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter
from maya.persona.in_memory import InMemoryPersonaStore
from maya.voice.models import VADEvent
from maya.voice.planner import SpeechPlanner
from maya.voice.providers.mock import MockSTTProvider, MockTTSProvider
from maya.voice.session import VoiceSession


@pytest.fixture
def memory_manager():
    storage = {}
    writer = InMemoryWriter(storage)
    reader = InMemoryReader(storage)
    link_store = InMemoryLinkStore()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    activation_engine = SpreadingActivationEngine(link_getter=get_links)
    recall_engine = MultiChannelRecallEngine(
        channels=[KeywordRecallChannel()],
        reader=reader,
        activation_engine=activation_engine,
    )
    return DefaultMemoryManager(writer=writer, reader=reader, recall_engine=recall_engine)

@pytest.fixture
def engine(memory_manager):
    persona = InMemoryPersonaStore()
    return ConversationEngine(
        memory_manager=memory_manager,
        persona_store=persona,
        affect_analyzer=KeywordAffectAnalyzer(),
        llm=MockLLMProvider(),
    )

from maya.voice.models import VADEvent, VADEventType, AudioFrame


class InterruptionVADProvider:
    def __init__(self, session_ref=None):
        self.session_ref = session_ref
        
    async def listen(self, audio_stream):
        # Wait until state is SPEAKING
        if self.session_ref:
            while self.session_ref.state != "speaking":
                await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.5)
            
        yield VADEvent(type=VADEventType.SPEECH_STARTED)
        async for _ in audio_stream:
            pass

async def mock_audio_stream():
    yield AudioFrame(pcm_data=b"Interrupt ")
    yield AudioFrame(pcm_data=b"me")
    await asyncio.sleep(0.5)

@pytest.mark.asyncio
async def test_interruption_barge_in(engine):
    user_id = uuid4()
    
    session = VoiceSession(
        user_id=user_id,
        engine=engine,
        vad=InterruptionVADProvider(),
        stt=MockSTTProvider(),
        tts=MockTTSProvider(),
        planner=SpeechPlanner(),
    )
    
    # Inject the session reference so the VAD provider knows when to interrupt
    session.vad.session_ref = session
    
    # Process audio stream - process_user_audio automatically handles VAD routing
    chunks = []
    async for chunk in session.process_user_audio(mock_audio_stream()):
        chunks.append(chunk)
        
    # Since VAD fires SPEECH_STARTED immediately, cancel_event is set.
    # We should get truncated output (maybe 0 or 1 chunk before it cancelled)
    assert len(chunks) < 10 # Meaning it didn't finish the whole sentence
    
    # Let's verify working memory has an interrupted turn
    # Need to wait a tiny bit to ensure the engine finishes writing to memory async if needed
    await asyncio.sleep(0.1)
    wm = await engine.memory_manager.get_working_memory(user_id, session.conversation_id)
    assert len(wm.recent_turns) > 0
    assert wm.recent_turns[-1].interrupted is True
