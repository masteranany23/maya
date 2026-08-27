from uuid import uuid4

from maya.conversation.engine import ConversationEngine
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import RecallCue
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter
from maya.persona.in_memory import InMemoryPersonaStore


async def test_chat_writes_episodic_memory() -> None:
    storage = {}
    writer = InMemoryWriter(storage)
    reader = InMemoryReader(storage)
    link_store = InMemoryLinkStore()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    
    activation_engine = SpreadingActivationEngine(
        link_getter=get_links,
    )
    recall_engine = MultiChannelRecallEngine(
        channels=[KeywordRecallChannel()],
        reader=reader,
        activation_engine=activation_engine,
    )
    memory_manager = DefaultMemoryManager(
        writer=writer,
        reader=reader,
        recall_engine=recall_engine,
    )

    engine = ConversationEngine(
        memory_manager=memory_manager,
        persona_store=InMemoryPersonaStore(),
        affect_analyzer=KeywordAffectAnalyzer(),
        llm=MockLLMProvider(),
    )
    user_id = uuid4()
    conv_id = uuid4()
    response = await engine.chat(user_id=user_id, conversation_id=conv_id, message="hello Maya")
    assert response.text
    
    cue = RecallCue(user_id=user_id, text_query="hello")
    found = await memory_manager.remember(cue)
    assert len(found) == 1
    assert found[0].memory.provenance.source_type == "user_message"
