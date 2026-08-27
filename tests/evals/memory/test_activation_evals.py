"""Evaluations for the spreading activation engine.

Tests multi-hop associative recall, false-memory resistance (degree penalty),
and indirect autobiographical recall.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
)
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.store.in_memory import InMemoryWriter, InMemoryReader, InMemoryLinkStore


def _prov() -> ProvenanceRecord:
    return ProvenanceRecord(source_type="user_message")


UID = uuid4()
NOW = datetime.now(timezone.utc)


class TestSpreadingActivation:
    async def test_multi_hop_recall(self) -> None:
        """Seed -> Node A -> Node B. Node B should be retrieved via 2 hops."""
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)
        link_store = InMemoryLinkStore()

        # Seed memory (User mentioned "project deadline")
        m_seed = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Worried about the project deadline",
            topics=["work"], provenance=_prov(),
        )
        
        # Intermediate node (Linked to project deadline)
        m_a = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="I am using Python for the new project",
            topics=["work", "tech"], provenance=_prov(),
        )

        # Target node (Linked to Python)
        m_b = MemoryItem(
            user_id=UID, memory_type=MemoryType.PROFILE,
            content="I love coding in Python",
            topics=["tech", "preferences"], provenance=_prov(),
        )

        for m in [m_seed, m_a, m_b]:
            await writer.write(m)

        await link_store.add_link(MemoryLink(source_id=m_seed.id, target_id=m_a.id, link_type=AssociationType.THEMATIC, strength=1.0))
        await link_store.add_link(MemoryLink(source_id=m_a.id, target_id=m_b.id, link_type=AssociationType.THEMATIC, strength=1.0))

        async def get_links(mid):
            return await link_store.get_links(mid, direction="both")

        activation_engine = SpreadingActivationEngine(
            link_getter=get_links,
            attenuation_factor=0.9,
            activation_threshold=0.1,
            max_hops=3
        )

        # The cue will only match m_seed via keyword
        engine = MultiChannelRecallEngine(
            channels=[KeywordRecallChannel()],
            reader=reader,
            activation_engine=activation_engine,
        )

        results = await engine.recall(RecallCue(user_id=UID, text_query="project deadline"))
        
        result_ids = {r.memory.id for r in results}
        # Both m_a and m_b should be activated and returned
        assert m_seed.id in result_ids
        assert m_a.id in result_ids
        assert m_b.id in result_ids

        # Check trace
        for r in results:
            if r.memory.id == m_b.id:
                assert r.activation_trace is not None
                assert len(r.activation_trace.path) == 2
                assert r.propagated_score > 0
                assert r.seed_score == 0

    async def test_interference_and_false_memory_resistance(self) -> None:
        """Highly connected 'generic' nodes should be penalized (inhibition) so they don't flood the network."""
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)
        link_store = InMemoryLinkStore()

        # Seed memory
        m_seed = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="I ate an apple today",
            provenance=_prov(),
        )

        # Hub node (very high degree)
        m_hub = MemoryItem(
            user_id=UID, memory_type=MemoryType.SEMANTIC,
            content="Food is something you eat",
            provenance=_prov(),
        )
        
        # Unrelated memories connected only via the hub
        unrelated = []
        for i in range(50):
            m = MemoryItem(
                user_id=UID, memory_type=MemoryType.EPISODIC,
                content=f"I consumed food item {i} a long time ago",
                provenance=_prov()
            )
            unrelated.append(m)

        for m in [m_seed, m_hub] + unrelated:
            await writer.write(m)

        # Connect seed to hub
        await link_store.add_link(MemoryLink(source_id=m_seed.id, target_id=m_hub.id, link_type=AssociationType.THEMATIC, strength=1.0))
        
        # Connect hub to all 50 unrelated memories
        for m in unrelated:
            await link_store.add_link(MemoryLink(source_id=m_hub.id, target_id=m.id, link_type=AssociationType.THEMATIC, strength=1.0))

        async def get_links(mid):
            return await link_store.get_links(mid, direction="both")

        activation_engine = SpreadingActivationEngine(
            link_getter=get_links,
            attenuation_factor=0.8,
            activation_threshold=0.2, # high threshold to ensure weak signals are dropped
            max_hops=2,
            fan_out_limit=50,
        )

        engine = MultiChannelRecallEngine(
            channels=[KeywordRecallChannel()],
            reader=reader,
            activation_engine=activation_engine,
        )

        results = await engine.recall(RecallCue(user_id=UID, text_query="ate an apple today"))
        
        result_ids = {r.memory.id for r in results}
        
        assert m_seed.id in result_ids
        # Hub should be activated (it's 1 hop away from seed)
        assert m_hub.id in result_ids
        
        # Due to degree-normalized inhibition (degree of hub is 51, so div by ~5), 
        # the activation propagating OUT of the hub to the unrelated nodes should be < 0.2
        # Therefore, none of the unrelated nodes should be recalled.
        unrelated_recalled = [u for u in unrelated if u.id in result_ids]
        assert len(unrelated_recalled) == 0

    async def test_indirect_autobiographical_recall(self) -> None:
        """Recall based on a concept closely tied to an autobiographical memory."""
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)
        link_store = InMemoryLinkStore()

        m_concept = MemoryItem(
            user_id=UID, memory_type=MemoryType.SEMANTIC,
            content="Paris is the capital of France",
            provenance=_prov(),
        )

        m_episodic = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="I went to Paris for my honeymoon in 2022",
            provenance=_prov(),
        )

        for m in [m_concept, m_episodic]:
            await writer.write(m)
            
        await link_store.add_link(MemoryLink(source_id=m_concept.id, target_id=m_episodic.id, link_type=AssociationType.THEMATIC, strength=1.0))

        async def get_links(mid):
            return await link_store.get_links(mid, direction="both")

        activation_engine = SpreadingActivationEngine(
            link_getter=get_links,
        )

        engine = MultiChannelRecallEngine(
            channels=[KeywordRecallChannel()],
            reader=reader,
            activation_engine=activation_engine,
        )

        # Querying for the concept should bring up the episodic memory
        results = await engine.recall(RecallCue(user_id=UID, text_query="capital of France"))
        
        result_ids = {r.memory.id for r in results}
        assert m_concept.id in result_ids
        assert m_episodic.id in result_ids
