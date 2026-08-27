"""Unit tests for memory domain models."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from maya.memory.models import (
    AssociationType,
    ConsolidationResult,
    ContradictionRecord,
    EmotionalContext,
    MemoryItem,
    MemoryLink,
    MemoryStatus,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
    RecallResult,
    ReflectionResult,
    ScoringState,
    TemporalContext,
    WorkingMemory,
)

# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestMemoryType:
    def test_all_tiers_present(self) -> None:
        assert set(MemoryType) == {"working", "episodic", "semantic", "profile", "reflective"}

    def test_string_value(self) -> None:
        assert MemoryType.EPISODIC == "episodic"


class TestMemoryStatus:
    def test_all_statuses_present(self) -> None:
        assert set(MemoryStatus) == {
            "active", "weakened", "decayed", "consolidated", "superseded", "contradicted", "archived",
        }


class TestAssociationType:
    def test_all_link_types_present(self) -> None:
        expected = {
            "temporal", "causal", "thematic", "emotional",
            "entity", "contradicts", "supersedes", "derived_from",
        }
        assert set(AssociationType) == expected


# ---------------------------------------------------------------------------
# Sub-model tests
# ---------------------------------------------------------------------------


class TestProvenanceRecord:
    def test_defaults(self) -> None:
        p = ProvenanceRecord(source_type="user_message")
        assert p.source_type == "user_message"
        assert p.source_id is None
        assert p.confidence == 0.5
        assert p.evidence_ids == []
        assert p.method == "direct_observation"

    def test_full_construction(self) -> None:
        src = uuid4()
        ev = [uuid4(), uuid4()]
        p = ProvenanceRecord(
            source_type="reflection",
            source_id=src,
            confidence=0.9,
            evidence_ids=ev,
            method="synthesis",
        )
        assert p.source_id == src
        assert len(p.evidence_ids) == 2
        assert p.method == "synthesis"


class TestEmotionalContext:
    def test_defaults(self) -> None:
        e = EmotionalContext()
        assert e.valence == 0.0
        assert e.arousal == 0.0
        assert e.dominant_emotion is None
        assert e.affect_source == "unset"

    def test_clamped_values(self) -> None:
        e = EmotionalContext(valence=-0.8, arousal=0.9, dominant_emotion="sadness")
        assert e.valence == -0.8
        assert e.arousal == 0.9

    def test_valence_out_of_range(self) -> None:
        with pytest.raises(Exception):
            EmotionalContext(valence=-1.5)

    def test_arousal_out_of_range(self) -> None:
        with pytest.raises(Exception):
            EmotionalContext(arousal=1.5)


class TestTemporalContext:
    def test_defaults(self) -> None:
        t = TemporalContext()
        assert t.duration is None
        assert t.temporal_landmarks == []
        assert t.sequence_prev is None

    def test_with_duration(self) -> None:
        t = TemporalContext(duration=timedelta(hours=2))
        assert t.duration == timedelta(hours=2)

    def test_with_chain(self) -> None:
        prev_id = uuid4()
        next_id = uuid4()
        t = TemporalContext(sequence_prev=prev_id, sequence_next=next_id)
        assert t.sequence_prev == prev_id
        assert t.sequence_next == next_id


class TestScoringState:
    def test_defaults(self) -> None:
        s = ScoringState()
        assert s.importance == 0.5
        assert s.access_count == 0
        assert s.decay_rate == 0.01

    def test_effective_salience_never_accessed(self) -> None:
        s = ScoringState(importance=0.8)
        now = datetime.now(UTC)
        # No last_accessed_at → returns base importance
        assert s.effective_salience(now) == 0.8

    def test_effective_salience_recent_access(self) -> None:
        now = datetime.now(UTC)
        s = ScoringState(importance=0.8, last_accessed_at=now)
        # Zero elapsed → base importance
        assert s.effective_salience(now) == 0.8

    def test_effective_salience_decays_over_time(self) -> None:
        now = datetime.now(UTC)
        ten_days_ago = now - timedelta(days=10)
        s = ScoringState(importance=1.0, decay_rate=0.1, last_accessed_at=ten_days_ago)
        salience = s.effective_salience(now)
        expected = math.exp(-0.1 * 10)
        assert abs(salience - expected) < 0.001

    def test_reinforcement_bonus_increases_salience(self) -> None:
        now = datetime.now(UTC)
        s = ScoringState(importance=0.5, reinforcement_bonus=0.3, last_accessed_at=now)
        assert s.effective_salience(now) == 0.8

    def test_salience_capped_at_one(self) -> None:
        now = datetime.now(UTC)
        s = ScoringState(importance=0.9, reinforcement_bonus=0.5, last_accessed_at=now)
        assert s.effective_salience(now) == 1.0


# ---------------------------------------------------------------------------
# MemoryLink tests
# ---------------------------------------------------------------------------


class TestMemoryLink:
    def test_construction(self) -> None:
        src, tgt = uuid4(), uuid4()
        link = MemoryLink(
            source_id=src, target_id=tgt, link_type=AssociationType.THEMATIC
        )
        assert link.source_id == src
        assert link.target_id == tgt
        assert link.link_type == AssociationType.THEMATIC
        assert link.strength == 1.0

    def test_strength_bounds(self) -> None:
        with pytest.raises(Exception):
            MemoryLink(
                source_id=uuid4(), target_id=uuid4(),
                link_type=AssociationType.CAUSAL, strength=1.5,
            )


# ---------------------------------------------------------------------------
# MemoryItem tests
# ---------------------------------------------------------------------------


def _make_provenance(**kw: object) -> ProvenanceRecord:
    defaults: dict = {"source_type": "user_message", "method": "direct_observation"}
    defaults.update(kw)
    return ProvenanceRecord(**defaults)


def _make_memory(**kw: object) -> MemoryItem:
    defaults: dict = {
        "user_id": uuid4(),
        "memory_type": MemoryType.EPISODIC,
        "content": "test content",
        "provenance": _make_provenance(),
    }
    defaults.update(kw)
    return MemoryItem(**defaults)


class TestMemoryItem:
    def test_minimal_construction(self) -> None:
        m = _make_memory()
        assert m.status == MemoryStatus.ACTIVE
        assert m.entities == []
        assert m.topics == []
        assert m.version == 1

    def test_with_emotional_context(self) -> None:
        m = _make_memory(
            emotional_context=EmotionalContext(valence=0.7, dominant_emotion="joy")
        )
        assert m.emotional_context.valence == 0.7
        assert m.emotional_context.dominant_emotion == "joy"

    def test_with_temporal_context(self) -> None:
        m = _make_memory(
            temporal_context=TemporalContext(
                temporal_landmarks=["morning", "last_tuesday"]
            )
        )
        assert m.temporal_context is not None
        assert "morning" in m.temporal_context.temporal_landmarks

    def test_serialization_roundtrip(self) -> None:
        m = _make_memory(
            entities=["Alice", "Bob"],
            topics=["career"],
            tags=["important"],
        )
        data = m.model_dump(mode="json")
        restored = MemoryItem.model_validate(data)
        assert restored.id == m.id
        assert restored.entities == ["Alice", "Bob"]

    def test_all_memory_types_accepted(self) -> None:
        for mt in MemoryType:
            m = _make_memory(memory_type=mt)
            assert m.memory_type == mt


# ---------------------------------------------------------------------------
# RecallCue / RecallResult tests
# ---------------------------------------------------------------------------


class TestRecallCue:
    def test_minimal(self) -> None:
        cue = RecallCue(user_id=uuid4(), text_query="hello")
        assert cue.limit == 10
        assert cue.memory_types is None

    def test_full(self) -> None:
        now = datetime.now(UTC)
        cue = RecallCue(
            user_id=uuid4(),
            text_query="birthday",
            time_range=(now - timedelta(days=30), now),
            topics=["celebration"],
            entities=["Alice"],
            emotional_valence_range=(0.5, 1.0),
            memory_types=[MemoryType.EPISODIC],
            linked_to=uuid4(),
            limit=5,
        )
        assert cue.limit == 5
        assert cue.memory_types == [MemoryType.EPISODIC]


class TestRecallResult:
    def test_construction(self) -> None:
        m = _make_memory()
        r = RecallResult(memory=m, relevance_score=0.85, recall_channel="keyword")
        assert r.relevance_score == 0.85
        assert r.recall_channel == "keyword"


# ---------------------------------------------------------------------------
# WorkingMemory tests
# ---------------------------------------------------------------------------


class TestWorkingMemory:
    def test_capacity_check(self) -> None:
        wm = WorkingMemory(
            user_id=uuid4(),
            conversation_id=uuid4(),
            recall_results=[RecallResult(memory=_make_memory(), relevance_score=1.0) for _ in range(12)],
            capacity=12,
        )
        assert wm.is_at_capacity()

    def test_under_capacity(self) -> None:
        wm = WorkingMemory(
            user_id=uuid4(),
            conversation_id=uuid4(),
            active_memories=[_make_memory()],
            capacity=12,
        )
        assert not wm.is_at_capacity()


# ---------------------------------------------------------------------------
# Contradiction / Reflection / Consolidation tests
# ---------------------------------------------------------------------------


class TestContradictionRecord:
    def test_defaults(self) -> None:
        c = ContradictionRecord(
            memory_a_id=uuid4(), memory_b_id=uuid4(),
            description="vegetarian vs steak dinner",
        )
        assert c.resolution == "unresolved"
        assert c.resolved_at is None


class TestReflectionResult:
    def test_construction(self) -> None:
        r = ReflectionResult(
            source_memory_ids=[uuid4(), uuid4()],
            insight="User tends to discuss career anxiety on Mondays",
            reflection_type="pattern",
            provenance=_make_provenance(source_type="reflection", method="synthesis"),
        )
        assert r.reflection_type == "pattern"
        assert len(r.source_memory_ids) == 2


class TestConsolidationResult:
    def test_construction(self) -> None:
        c = ConsolidationResult(
            absorbed_ids=[uuid4(), uuid4(), uuid4()],
            new_semantic_content="User jogs regularly in the morning",
            provenance=_make_provenance(source_type="consolidation", method="synthesis"),
        )
        assert len(c.absorbed_ids) == 3
