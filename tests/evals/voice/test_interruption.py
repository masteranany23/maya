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

class InterruptionVADProvider:
    async def listen(self, audio_stream):
        yield VADEvent.SPEECH_STARTED

async def mock_audio_stream():
    yield b"Interrupt "
    yield b"me"
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
    
    # We trigger the VAD listener in the background
    asyncio.create_task(session._handle_vad(mock_audio_stream()))
    
    # Process audio stream
    chunks = []
    async for chunk in session.process_user_audio(mock_audio_stream()):
        chunks.append(chunk)
        
    # Since VAD fires SPEECH_STARTED immediately, cancel_event is set.
    # We should get NO output, or very truncated output.
    assert len(chunks) == 0
    
    # Let's verify working memory has an interrupted turn
    wm = await engine.memory_manager.get_working_memory(user_id, session.conversation_id)
    assert len(wm.recent_turns) > 0
    assert wm.recent_turns[-1].interrupted is True
