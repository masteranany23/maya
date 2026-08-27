"""Unit tests for lifecycle operations — decay, importance, contradiction, consolidation, reflection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from maya.memory.lifecycle.consolidation import SimpleConsolidationEngine
from maya.memory.lifecycle.contradiction import HeuristicContradictionDetector
from maya.memory.lifecycle.decay import ExponentialDecayFunction, StepDecayFunction
from maya.memory.lifecycle.importance import HeuristicImportanceScorer
from maya.memory.lifecycle.reflection import StubReflectionEngine
from maya.memory.models import (
    EmotionalContext,
    MemoryItem,
    MemoryType,
    ProvenanceRecord,
    ScoringState,
)


def _prov() -> ProvenanceRecord:
    return ProvenanceRecord(source_type="user_message")


def _mem(**kw) -> MemoryItem:
    defaults = {
        "user_id": uuid4(),
        "memory_type": MemoryType.EPISODIC,
        "content": "test",
        "provenance": _prov(),
    }
    defaults.update(kw)
    return MemoryItem(**defaults)


# ---------------------------------------------------------------------------
# Decay
# ---------------------------------------------------------------------------


class TestExponentialDecay:
    def test_no_access_returns_base(self) -> None:
        fn = ExponentialDecayFunction()
        s = ScoringState(importance=0.7)
        assert fn.compute_salience(s, datetime.now(UTC)) == 0.7

    def test_decays_over_time(self) -> None:
        fn = ExponentialDecayFunction()
        now = datetime.now(UTC)
        s = ScoringState(importance=1.0, decay_rate=0.1, last_accessed_at=now - timedelta(days=10))
        salience = fn.compute_salience(s, now)
        assert 0.3 < salience < 0.4  # exp(-1.0) ≈ 0.368


class TestStepDecay:
    def test_within_threshold(self) -> None:
        fn = StepDecayFunction(max_age_days=30.0)
        now = datetime.now(UTC)
        s = ScoringState(importance=0.8, last_accessed_at=now - timedelta(days=10))
        assert fn.compute_salience(s, now) == 0.8

    def test_beyond_threshold(self) -> None:
        fn = StepDecayFunction(max_age_days=30.0)
        now = datetime.now(UTC)
        s = ScoringState(importance=0.8, last_accessed_at=now - timedelta(days=31))
        assert fn.compute_salience(s, now) == 0.0


# ---------------------------------------------------------------------------
# Importance
# ---------------------------------------------------------------------------


class TestHeuristicImportanceScorer:
    async def test_base_score(self) -> None:
        scorer = HeuristicImportanceScorer()
        score = await scorer.score("hello", {})
        assert 0.2 <= score <= 0.4

    async def test_high_signal_content(self) -> None:
        scorer = HeuristicImportanceScorer()
        score = await scorer.score(
            "My birthday is June 15th and I love hiking, my favorite food is sushi",
            {"entities": ["June 15th", "sushi"], "arousal": 0.7},
        )
        assert score > 0.6

    async def test_scores_capped(self) -> None:
        scorer = HeuristicImportanceScorer()
        score = await scorer.score(
            "birthday anniversary love favorite always remember important goal plan dream name " * 10,
            {"entities": ["a", "b", "c", "d", "e"], "arousal": 1.0},
        )
        assert score <= 1.0


# ---------------------------------------------------------------------------
# Contradiction
# ---------------------------------------------------------------------------


class TestHeuristicContradictionDetector:
    async def test_detects_vegetarian_steak(self) -> None:
        detector = HeuristicContradictionDetector()
        uid = uuid4()
        existing = _mem(
            user_id=uid,
            content="I am vegetarian",
            entities=["user"],
            topics=["diet"],
            memory_type=MemoryType.PROFILE,
        )
        candidate = _mem(
            user_id=uid,
            content="I had a great steak dinner",
            entities=["user"],
            topics=["diet"],
            memory_type=MemoryType.EPISODIC,
        )
        contradictions = await detector.detect([existing], candidate)
        assert len(contradictions) == 1
        assert contradictions[0].resolution == "unresolved"

    async def test_no_contradiction_different_subjects(self) -> None:
        detector = HeuristicContradictionDetector()
        existing = _mem(content="I am vegetarian", entities=["user"], topics=["diet"])
        candidate = _mem(content="My friend eats steak", entities=["friend"], topics=["food"])
        contradictions = await detector.detect([existing], candidate)
        assert contradictions == []

    async def test_no_contradiction_compatible_content(self) -> None:
        detector = HeuristicContradictionDetector()
        existing = _mem(content="I love hiking", entities=["user"], topics=["hobbies"])
        candidate = _mem(content="I also enjoy reading", entities=["user"], topics=["hobbies"])
        contradictions = await detector.detect([existing], candidate)
        assert contradictions == []


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------


class TestSimpleConsolidationEngine:
    async def test_consolidates_repeated_topic(self) -> None:
        engine = SimpleConsolidationEngine(min_occurrences=3)
        uid = uuid4()
        mems = [
            _mem(user_id=uid, content=f"Morning jog day {i}", topics=["exercise", "jogging"])
            for i in range(5)
        ]
        result = await engine.consolidate(mems)
        assert result is not None
        assert len(result.absorbed_ids) == 5
        assert "jogging" in result.new_semantic_content.lower() or "exercise" in result.new_semantic_content.lower()

    async def test_too_few_episodes(self) -> None:
        engine = SimpleConsolidationEngine(min_occurrences=3)
        mems = [_mem(topics=["rare_topic"]) for _ in range(2)]
        result = await engine.consolidate(mems)
        assert result is None

    async def test_ignores_non_episodic(self) -> None:
        engine = SimpleConsolidationEngine(min_occurrences=3)
        mems = [
            _mem(memory_type=MemoryType.SEMANTIC, topics=["exercise"])
            for _ in range(5)
        ]
        result = await engine.consolidate(mems)
        assert result is None


# ---------------------------------------------------------------------------
# Reflection
# ---------------------------------------------------------------------------


class TestStubReflectionEngine:
    async def test_generates_pattern_insights(self) -> None:
        engine = StubReflectionEngine(min_memories=3)
        mems = [
            _mem(topics=["career"]) for _ in range(5)
        ]
        results = await engine.reflect(mems)
        assert len(results) >= 1
        assert any("career" in r.insight.lower() for r in results)
        assert all(r.reflection_type == "pattern" for r in results if "career" in r.insight.lower())

    async def test_emotional_theme_detection(self) -> None:
        engine = StubReflectionEngine(min_memories=3)
        mems = [
            _mem(emotional_context=EmotionalContext(
                dominant_emotion="anxiety", affect_source="inferred"
            ))
            for _ in range(4)
        ]
        results = await engine.reflect(mems)
        assert any(r.reflection_type == "emotional_theme" for r in results)

    async def test_too_few_memories(self) -> None:
        engine = StubReflectionEngine(min_memories=3)
        results = await engine.reflect([_mem()])
        assert results == []

    async def test_provenance_chain(self) -> None:
        engine = StubReflectionEngine(min_memories=3)
        mems = [_mem(topics=["health"]) for _ in range(3)]
        results = await engine.reflect(mems)
        assert len(results) >= 1
        r = results[0]
        assert r.provenance.source_type == "reflection"
        assert len(r.provenance.evidence_ids) == 3
