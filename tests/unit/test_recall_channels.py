"""Unit tests for all recall channels."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from maya.memory.models import (
    EmotionalContext,
    MemoryItem,
    MemoryType,
    ProvenanceRecord,
    RecallCue,
    ScoringState,
    TemporalContext,
)
from maya.memory.recall.emotional import EmotionalRecallChannel
from maya.memory.recall.entity import EntityRecallChannel
from maya.memory.recall.importance import ImportanceRecallChannel
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.recall.temporal import TemporalRecallChannel
from maya.memory.recall.topic import TopicRecallChannel


def _prov() -> ProvenanceRecord:
    return ProvenanceRecord(source_type="user_message")


def _mem(user_id: UUID | None = None, **kw) -> MemoryItem:
    defaults = {
        "user_id": user_id or uuid4(),
        "memory_type": MemoryType.EPISODIC,
        "content": "test content",
        "provenance": _prov(),
    }
    defaults.update(kw)
    return MemoryItem(**defaults)


UID = uuid4()


# ---------------------------------------------------------------------------
# Keyword channel
# ---------------------------------------------------------------------------


class TestKeywordRecallChannel:
    async def test_no_query_returns_empty(self) -> None:
        ch = KeywordRecallChannel()
        cue = RecallCue(user_id=UID, text_query=None)
        assert await ch.recall(cue, [_mem()]) == []

    async def test_matching_terms(self) -> None:
        ch = KeywordRecallChannel()
        m = _mem(content="my birthday is in June")
        cue = RecallCue(user_id=UID, text_query="when is your birthday")
        results = await ch.recall(cue, [m])
        assert len(results) == 1
        assert results[0].relevance_score > 0

    async def test_no_match(self) -> None:
        ch = KeywordRecallChannel()
        m = _mem(content="I love pizza")
        cue = RecallCue(user_id=UID, text_query="quantum mechanics")
        results = await ch.recall(cue, [m])
        assert results == []

    async def test_entities_and_topics_searched(self) -> None:
        ch = KeywordRecallChannel()
        m = _mem(content="nothing relevant", entities=["Alice"], topics=["birthday"])
        cue = RecallCue(user_id=UID, text_query="Alice birthday party")
        results = await ch.recall(cue, [m])
        assert len(results) == 1

    async def test_ranking_order(self) -> None:
        ch = KeywordRecallChannel()
        m1 = _mem(content="birthday celebration cake party")
        m2 = _mem(content="birthday only")
        cue = RecallCue(user_id=UID, text_query="birthday celebration cake")
        results = await ch.recall(cue, [m1, m2])
        assert len(results) == 2
        assert results[0].memory.id == m1.id  # More overlap → higher score


# ---------------------------------------------------------------------------
# Temporal channel
# ---------------------------------------------------------------------------


class TestTemporalRecallChannel:
    async def test_recent_memory_scores_high(self) -> None:
        ch = TemporalRecallChannel()
        now = datetime.now(UTC)
        m = _mem(temporal_context=TemporalContext(occurred_at=now))
        cue = RecallCue(user_id=UID)
        results = await ch.recall(cue, [m])
        assert len(results) == 1
        assert results[0].relevance_score > 0.9

    async def test_old_memory_scores_low(self) -> None:
        ch = TemporalRecallChannel(recency_half_life_days=7.0)
        old = datetime.now(UTC) - timedelta(days=30)
        m = _mem(temporal_context=TemporalContext(occurred_at=old))
        cue = RecallCue(user_id=UID)
        results = await ch.recall(cue, [m])
        assert len(results) == 1
        assert results[0].relevance_score < 0.2

    async def test_time_range_filter(self) -> None:
        ch = TemporalRecallChannel()
        now = datetime.now(UTC)
        inside = _mem(temporal_context=TemporalContext(occurred_at=now - timedelta(days=2)))
        outside = _mem(temporal_context=TemporalContext(occurred_at=now - timedelta(days=20)))
        cue = RecallCue(
            user_id=UID,
            time_range=(now - timedelta(days=7), now),
        )
        results = await ch.recall(cue, [inside, outside])
        assert len(results) == 1
        assert results[0].memory.id == inside.id


# ---------------------------------------------------------------------------
# Entity channel
# ---------------------------------------------------------------------------


class TestEntityRecallChannel:
    async def test_no_query_entities(self) -> None:
        ch = EntityRecallChannel()
        cue = RecallCue(user_id=UID, entities=[])
        assert await ch.recall(cue, [_mem(entities=["Alice"])]) == []

    async def test_matching_entity(self) -> None:
        ch = EntityRecallChannel()
        m = _mem(entities=["Alice", "Bob"])
        cue = RecallCue(user_id=UID, entities=["Alice"])
        results = await ch.recall(cue, [m])
        assert len(results) == 1

    async def test_case_insensitive(self) -> None:
        ch = EntityRecallChannel()
        m = _mem(entities=["alice"])
        cue = RecallCue(user_id=UID, entities=["ALICE"])
        results = await ch.recall(cue, [m])
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Topic channel
# ---------------------------------------------------------------------------


class TestTopicRecallChannel:
    async def test_matching_topic(self) -> None:
        ch = TopicRecallChannel()
        m = _mem(topics=["career", "anxiety"])
        cue = RecallCue(user_id=UID, topics=["career"])
        results = await ch.recall(cue, [m])
        assert len(results) == 1

    async def test_no_query_topics(self) -> None:
        ch = TopicRecallChannel()
        cue = RecallCue(user_id=UID, topics=[])
        assert await ch.recall(cue, [_mem(topics=["x"])]) == []


# ---------------------------------------------------------------------------
# Emotional channel
# ---------------------------------------------------------------------------


class TestEmotionalRecallChannel:
    async def test_matching_valence(self) -> None:
        ch = EmotionalRecallChannel()
        m = _mem(
            emotional_context=EmotionalContext(
                valence=0.7, arousal=0.6, affect_source="user_expressed"
            )
        )
        cue = RecallCue(user_id=UID, emotional_valence_range=(0.5, 1.0))
        results = await ch.recall(cue, [m])
        assert len(results) == 1

    async def test_unset_affect_excluded(self) -> None:
        ch = EmotionalRecallChannel()
        m = _mem()  # default: affect_source="unset"
        cue = RecallCue(user_id=UID, emotional_valence_range=(-1.0, 1.0))
        assert await ch.recall(cue, [m]) == []

    async def test_out_of_range_excluded(self) -> None:
        ch = EmotionalRecallChannel()
        m = _mem(
            emotional_context=EmotionalContext(
                valence=-0.8, affect_source="inferred"
            )
        )
        cue = RecallCue(user_id=UID, emotional_valence_range=(0.5, 1.0))
        assert await ch.recall(cue, [m]) == []


# ---------------------------------------------------------------------------
# Importance channel
# ---------------------------------------------------------------------------


class TestImportanceRecallChannel:
    async def test_high_importance_surfaced(self) -> None:
        ch = ImportanceRecallChannel(min_salience=0.1)
        now = datetime.now(UTC)
        m = _mem(scoring=ScoringState(importance=0.9, last_accessed_at=now))
        cue = RecallCue(user_id=UID)
        results = await ch.recall(cue, [m])
        assert len(results) == 1
        assert results[0].relevance_score > 0.8

    async def test_low_salience_filtered(self) -> None:
        ch = ImportanceRecallChannel(min_salience=0.5)
        old = datetime.now(UTC) - timedelta(days=100)
        m = _mem(scoring=ScoringState(importance=0.3, decay_rate=0.1, last_accessed_at=old))
        cue = RecallCue(user_id=UID)
        results = await ch.recall(cue, [m])
        assert results == []
