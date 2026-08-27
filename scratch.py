import asyncio
from uuid import uuid4

from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
)
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter


async def main():
    storage = {}
    writer = InMemoryWriter(storage)
    reader = InMemoryReader(storage)
    link_store = InMemoryLinkStore()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    
    act_eng = SpreadingActivationEngine(link_getter=get_links, attenuation_factor=0.9, activation_threshold=0.1)
    rec_eng = MultiChannelRecallEngine(channels=[KeywordRecallChannel()], reader=reader, activation_engine=act_eng)
    manager = DefaultMemoryManager(writer=writer, reader=reader, recall_engine=rec_eng)
    
    user_id = uuid4()
    m1 = MemoryItem(user_id=user_id, memory_type=MemoryType.EPISODIC, content="I failed the robotics competition", provenance=ProvenanceRecord(source_type="test"))
    m2 = MemoryItem(user_id=user_id, memory_type=MemoryType.EPISODIC, content="I felt so embarrassed afterward", provenance=ProvenanceRecord(source_type="test"))
    m3 = MemoryItem(user_id=user_id, memory_type=MemoryType.EPISODIC, content="I considered quitting robotics completely", provenance=ProvenanceRecord(source_type="test"))
    m4 = MemoryItem(user_id=user_id, memory_type=MemoryType.EPISODIC, content="I decided to return to robotics", provenance=ProvenanceRecord(source_type="test"))
    
    for m in [m1, m2, m3, m4]: await manager.memorize(m)
    await link_store.add_link(MemoryLink(source_id=m1.id, target_id=m2.id, link_type=AssociationType.CAUSAL, strength=1.0))
    await link_store.add_link(MemoryLink(source_id=m2.id, target_id=m3.id, link_type=AssociationType.CAUSAL, strength=1.0))
    await link_store.add_link(MemoryLink(source_id=m3.id, target_id=m4.id, link_type=AssociationType.THEMATIC, strength=1.0))
    
    cue = RecallCue(user_id=user_id, text_query="I'm thinking about entering another competition.", limit=5)
    results = await manager.remember(cue)
    for r in results:
        print(f"ID: {r.memory.id}, seed: {r.seed_score:.2f}, prop: {r.propagated_score:.2f}, final: {r.relevance_score:.2f}")

asyncio.run(main())
