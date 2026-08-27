from uuid import uuid4

import pytest

from maya.core.models import ConversationTurn
from maya.llm.mock import MockLLMProvider
from maya.memory.association import AssociationEngine, SharedEntityStrategy
from maya.memory.extraction import LLMMemoryEncoder
from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
    RecallResult,
    WorkingMemory,
)
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter


@pytest.mark.asyncio
async def test_association_duplication():
    # Test 1: Deduplication
    link_store = InMemoryLinkStore()
    engine = AssociationEngine(link_store=link_store, strategies=[SharedEntityStrategy()])
    
    mem1 = MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="A", entities=["X"], provenance=ProvenanceRecord(source_type="user"))
    mem2 = MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="B", entities=["X"], provenance=ProvenanceRecord(source_type="user"))
    
    # First call
    links1 = await engine.associate(new_memory=mem2, context_memories=[mem1])
    assert len(links1) == 2  # Bidirectional from SharedEntityStrategy
    
    # Second call with same inputs should not duplicate
    links2 = await engine.associate(new_memory=mem2, context_memories=[mem1])
    assert len(links2) == 0
    assert len(link_store.links) == 2

@pytest.mark.asyncio
async def test_llm_failure_handling():
    class BrokenLLMProvider(MockLLMProvider):
        async def generate_structured(self, **kwargs):
            raise TimeoutError("LLM timed out")
            
    encoder = LLMMemoryEncoder(llm=BrokenLLMProvider())
    turn = ConversationTurn(user_id=uuid4(), text="Hello")
    result = await encoder.encode(turn)
    # The encoder gracefully catches exceptions and returns None
    assert result is None

@pytest.mark.asyncio
async def test_memory_isolation():
    user_a = uuid4()
    user_b = uuid4()
    
    storage = {}
    writer = InMemoryWriter(storage)
    reader = InMemoryReader(storage)
    link_store = InMemoryLinkStore()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    
    activation = SpreadingActivationEngine(link_getter=get_links)
    recall = MultiChannelRecallEngine(channels=[KeywordRecallChannel()], reader=reader, activation_engine=activation)
    manager = DefaultMemoryManager(writer=writer, reader=reader, recall_engine=recall)
    
    mem_a1 = MemoryItem(user_id=user_a, memory_type=MemoryType.EPISODIC, content="I love apples.", provenance=ProvenanceRecord(source_type="user"))
    mem_a2 = MemoryItem(user_id=user_a, memory_type=MemoryType.EPISODIC, content="Apples are red.", provenance=ProvenanceRecord(source_type="user"))
    await manager.memorize(mem_a1)
    await manager.memorize(mem_a2)
    
    mem_b1 = MemoryItem(user_id=user_b, memory_type=MemoryType.EPISODIC, content="I love oranges.", provenance=ProvenanceRecord(source_type="user"))
    await manager.memorize(mem_b1)
    
    # Force a link in the store between A and B (which shouldn't happen natively, but to test isolation)
    await link_store.add_link(MemoryLink(source_id=mem_a1.id, target_id=mem_b1.id, link_type=AssociationType.THEMATIC))
    
    # User B searches for "love"
    cue = RecallCue(user_id=user_b, text_query="love")
    results = await manager.remember(cue)
    
    # B should only see B's memories, even if there's a rogue link.
    for r in results:
        assert r.memory.user_id == user_b
        assert r.memory.id != mem_a1.id

@pytest.mark.asyncio
async def test_recall_traceability():
    # Verify that WorkingMemory preserves RecallResult traces
    wm = WorkingMemory(user_id=uuid4(), conversation_id=uuid4())
    mem = MemoryItem(user_id=wm.user_id, memory_type=MemoryType.EPISODIC, content="test", provenance=ProvenanceRecord(source_type="user"))
    
    rr = RecallResult(
        memory=mem,
        relevance_score=0.9,
        seed_score=0.5,
        propagated_score=0.4
    )
    
    wm.recall_results = [rr]
    assert len(wm.active_memories) == 1
    assert wm.recall_results[0].relevance_score == 0.9
