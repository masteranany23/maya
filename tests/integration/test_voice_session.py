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
from maya.voice.planner import SpeechPlanner
from maya.voice.providers.mock import MockSTTProvider, MockTTSProvider, MockVADProvider
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

from maya.voice.models import AudioFrame

async def mock_audio_stream():
    yield AudioFrame(pcm_data=b"hello")
    yield AudioFrame(pcm_data=b" there")

@pytest.mark.asyncio
async def test_voice_session_full_duplex(engine):
    user_id = uuid4()
    
    session = VoiceSession(
        user_id=user_id,
        engine=engine,
        vad=MockVADProvider(),
        stt=MockSTTProvider(),
        tts=MockTTSProvider(),
        planner=SpeechPlanner(),
    )
    
    # Process audio stream
    chunks = []
    async for chunk in session.process_user_audio(mock_audio_stream()):
        chunks.append(chunk)
        
    assert len(chunks) > 0
    # The MockTTS yields the text of the segments as bytes.
    # The LLM mock will output "I have no specific memories about this."
    # The SemanticBuffer will split it into sentences.
    text_output = b"".join([c.pcm_data for c in chunks if not c.is_final])
    assert b"I have no specific memories about this" in text_output
