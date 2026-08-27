"""Memory evaluation fixtures.

LoCoMo-inspired regression tests that exercise recall accuracy, temporal
reasoning, emotional retrieval, associative recall, decay/reinforcement,
contradiction detection, consolidation, and provenance correctness.

Each fixture builds a realistic memory scenario and validates the expected
retrieval behavior end-to-end through the recall engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from maya.memory.models import (
    AssociationType,
    EmotionalContext,
    MemoryItem,
    MemoryLink,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
    ScoringState,
    TemporalContext,
)
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.recall.temporal import TemporalRecallChannel
from maya.memory.recall.entity import EntityRecallChannel
from maya.memory.recall.topic import TopicRecallChannel
from maya.memory.recall.emotional import EmotionalRecallChannel
from maya.memory.recall.importance import ImportanceRecallChannel
from maya.memory.recall.engine import MultiChannelRecallEngine, FusionStrategy
from maya.memory.store.in_memory import InMemoryWriter, InMemoryReader, InMemoryLinkStore
from maya.memory.lifecycle.contradiction import HeuristicContradictionDetector
from maya.memory.lifecycle.consolidation import SimpleConsolidationEngine


def _prov(**kw) -> ProvenanceRecord:
    defaults = {"source_type": "user_message", "method": "direct_observation"}
    defaults.update(kw)
    return ProvenanceRecord(**defaults)


UID = uuid4()
NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixture 1: Recall Accuracy
# ---------------------------------------------------------------------------


class TestRecallAccuracy:
    """User tells MAYA about birthday, job, pet across turns.
    Later queries must retrieve the correct memory."""

    async def test_factual_recall(self) -> None:
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)

        birthday = MemoryItem(
            user_id=UID, memory_type=MemoryType.PROFILE,
            content="My birthday is June 15th",
            entities=["user"], topics=["birthday"],
            provenance=_prov(),
            scoring=ScoringState(importance=0.8, last_accessed_at=NOW),
        )
        pet = MemoryItem(
            user_id=UID, memory_type=MemoryType.PROFILE,
            content="My dog's name is Max",
            entities=["user", "Max"], topics=["pet"],
            provenance=_prov(),
            scoring=ScoringState(importance=0.7, last_accessed_at=NOW),
        )
        job = MemoryItem(
            user_id=UID, memory_type=MemoryType.PROFILE,
            content="I just started a new job as a software engineer",
            entities=["user"], topics=["career", "job"],
            provenance=_prov(),
            scoring=ScoringState(importance=0.6, last_accessed_at=NOW),
        )
        for m in [birthday, pet, job]:
            await writer.write(m)

        engine = MultiChannelRecallEngine(
            channels=[KeywordRecallChannel(), EntityRecallChannel(), TopicRecallChannel()],
            reader=reader,
            strategy=FusionStrategy.MAX_OF,
        )

        # Query about birthday
        results = await engine.recall(RecallCue(user_id=UID, text_query="when is my birthday"))
        assert len(results) >= 1
        assert any(r.memory.id == birthday.id for r in results)

        # Query about pet
        results = await engine.recall(RecallCue(user_id=UID, text_query="what is my dog's name", entities=["Max"]))
        assert any(r.memory.id == pet.id for r in results)


# ---------------------------------------------------------------------------
# Fixture 2: Temporal Reasoning
# ---------------------------------------------------------------------------


class TestTemporalReasoning:
    """Events in sequence: Monday meeting → Tuesday argument → Wednesday resolution.
    Temporal retrieval should order correctly and filter by range."""

    async def test_temporal_ordering(self) -> None:
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)

        monday = NOW - timedelta(days=3)
        tuesday = NOW - timedelta(days=2)
        wednesday = NOW - timedelta(days=1)

        m1 = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Had a team meeting about the project deadline",
            temporal_context=TemporalContext(occurred_at=monday, temporal_landmarks=["monday"]),
            topics=["work"], provenance=_prov(),
        )
        m2 = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Had an argument with coworker about priorities",
            temporal_context=TemporalContext(occurred_at=tuesday, temporal_landmarks=["tuesday"]),
            topics=["work", "conflict"], provenance=_prov(),
        )
        m3 = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Resolved the conflict, agreed on new approach",
            temporal_context=TemporalContext(occurred_at=wednesday, temporal_landmarks=["wednesday"]),
            topics=["work", "resolution"], provenance=_prov(),
        )

        for m in [m1, m2, m3]:
            await writer.write(m)

        engine = MultiChannelRecallEngine(
            channels=[TemporalRecallChannel()],
            reader=reader,
        )

        # Query: what happened before the resolution (Mon-Tue range)
        results = await engine.recall(RecallCue(
            user_id=UID,
            time_range=(monday - timedelta(hours=1), tuesday + timedelta(hours=23)),
        ))
        result_ids = {r.memory.id for r in results}
        assert m1.id in result_ids
        assert m2.id in result_ids
        assert m3.id not in result_ids


# ---------------------------------------------------------------------------
# Fixture 3: Emotional Context Retrieval
# ---------------------------------------------------------------------------


class TestEmotionalRetrieval:
    """Joyful and sad events. Recalling 'happy memories' should rank joyful higher."""

    async def test_emotional_filter(self) -> None:
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)

        joyful = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Got promoted at work, so excited!",
            emotional_context=EmotionalContext(
                valence=0.9, arousal=0.8, dominant_emotion="joy", affect_source="user_expressed"
            ),
            provenance=_prov(),
        )
        sad = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="My grandmother passed away",
            emotional_context=EmotionalContext(
                valence=-0.9, arousal=0.7, dominant_emotion="grief", affect_source="user_expressed"
            ),
            provenance=_prov(),
        )
        await writer.write(joyful)
        await writer.write(sad)

        engine = MultiChannelRecallEngine(
            channels=[EmotionalRecallChannel()],
            reader=reader,
        )

        # Query happy memories
        results = await engine.recall(RecallCue(
            user_id=UID, emotional_valence_range=(0.5, 1.0)
        ))
        assert len(results) == 1
        assert results[0].memory.id == joyful.id


# ---------------------------------------------------------------------------
# Fixture 5: Decay & Reinforcement
# ---------------------------------------------------------------------------


class TestDecayAndReinforcement:
    """Two memories with identical importance. Recently accessed should rank higher."""

    async def test_recency_ranking(self) -> None:
        storage: dict = {}
        writer = InMemoryWriter(storage)
        reader = InMemoryReader(storage)

        recent = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Recently discussed topic",
            scoring=ScoringState(importance=0.5, last_accessed_at=NOW, access_count=3),
            provenance=_prov(),
        )
        stale = MemoryItem(
            user_id=UID, memory_type=MemoryType.EPISODIC,
            content="Old forgotten topic",
            scoring=ScoringState(
                importance=0.5, decay_rate=0.02,
                last_accessed_at=NOW - timedelta(days=30), access_count=1,
            ),
            provenance=_prov(),
        )
        await writer.write(recent)
        await writer.write(stale)

        engine = MultiChannelRecallEngine(
            channels=[ImportanceRecallChannel(min_salience=0.01)],
            reader=reader,
        )
        results = await engine.recall(RecallCue(user_id=UID))
        assert len(results) == 2
        assert results[0].memory.id == recent.id  # Higher salience


# ---------------------------------------------------------------------------
# Fixture 6: Contradiction Detection
# ---------------------------------------------------------------------------


class TestContradictionFixture:
    """User says 'I'm vegetarian' then 'I had a great steak dinner'."""

    async def test_contradiction_detected(self) -> None:
        detector = HeuristicContradictionDetector()
        uid = uuid4()
        existing = MemoryItem(
            user_id=uid, memory_type=MemoryType.PROFILE,
            content="I am vegetarian and have been for years",
            entities=["user"], topics=["diet", "food"],
            provenance=_prov(),
        )
        candidate = MemoryItem(
            user_id=uid, memory_type=MemoryType.EPISODIC,
            content="Had a great steak dinner last night with friends",
            entities=["user"], topics=["diet", "food"],
            provenance=_prov(),
        )
        contradictions = await detector.detect([existing], candidate)
        assert len(contradictions) >= 1
        assert contradictions[0].memory_a_id == existing.id
        assert contradictions[0].memory_b_id == candidate.id


# ---------------------------------------------------------------------------
# Fixture 7: Consolidation
# ---------------------------------------------------------------------------


class TestConsolidationFixture:
    """User mentions 'morning jog' across 5 episodes → semantic memory."""

    async def test_consolidation_output(self) -> None:
        engine = SimpleConsolidationEngine(min_occurrences=3)
        uid = uuid4()
        episodes = [
            MemoryItem(
                user_id=uid, memory_type=MemoryType.EPISODIC,
                content=f"Went for a morning jog in the park, day {i+1}",
                topics=["exercise", "jogging", "morning_routine"],
                provenance=_prov(),
            )
            for i in range(5)
        ]
        result = await engine.consolidate(episodes)
        assert result is not None
        assert len(result.absorbed_ids) == 5
        assert result.provenance.method == "synthesis"
        assert len(result.provenance.evidence_ids) == 5


# ---------------------------------------------------------------------------
# Fixture 8: Provenance Correctness
# ---------------------------------------------------------------------------


class TestProvenanceFixture:
    """Reflective memory derived from 3 episodic sources must carry correct provenance."""

    async def test_provenance_chain(self) -> None:
        from maya.memory.lifecycle.reflection import StubReflectionEngine

        engine = StubReflectionEngine(min_memories=3)
        source_ids = [uuid4() for _ in range(3)]
        memories = [
            MemoryItem(
                id=sid, user_id=UID, memory_type=MemoryType.EPISODIC,
                content=f"Discussion about career plans {i}",
                topics=["career"],
                provenance=_prov(),
            )
            for i, sid in enumerate(source_ids)
        ]
        results = await engine.reflect(memories)
        assert len(results) >= 1
        r = results[0]
        assert r.provenance.source_type == "reflection"
        assert set(r.provenance.evidence_ids) == set(source_ids)
        assert r.provenance.method == "synthesis"
