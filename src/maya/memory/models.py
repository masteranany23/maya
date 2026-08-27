"""Rich memory domain models for MAYA's human-like memory architecture.

Provides multi-dimensional memory representations with emotional, temporal,
associative, and provenance context. Replaces the flat MemoryItem with a
richly-typed model that enables multi-channel recall.

See docs/DECISIONS.md ADR-0007, ADR-0008.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MemoryType(StrEnum):
    """Tier of memory in the cognitive architecture."""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROFILE = "profile"
    REFLECTIVE = "reflective"


class MemoryStatus(StrEnum):
    """Lifecycle state of a memory item."""

    ACTIVE = "active"
    DECAYED = "decayed"
    CONSOLIDATED = "consolidated"
    CONTRADICTED = "contradicted"
    ARCHIVED = "archived"


class AssociationType(StrEnum):
    """Type of directed link between two memories."""

    TEMPORAL = "temporal"
    CAUSAL = "causal"
    THEMATIC = "thematic"
    EMOTIONAL = "emotional"
    ENTITY = "entity"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"


# ---------------------------------------------------------------------------
# Sub-models (composable context objects)
# ---------------------------------------------------------------------------


class ProvenanceRecord(BaseModel):
    """Tracks how and why a memory was created."""

    source_type: str  # "user_message", "llm_extraction", "reflection", "consolidation"
    source_id: UUID | None = None  # turn_id, parent memory id, reflection job id
    created_at: datetime = Field(default_factory=_utc_now)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_ids: list[UUID] = Field(default_factory=list)
    method: str = "direct_observation"
    # Valid methods: "direct_observation", "inference", "synthesis",
    #               "user_correction", "consolidation", "reflection"


class EmotionalContext(BaseModel):
    """Emotional annotation attached to a memory."""

    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    arousal: float = Field(default=0.0, ge=0.0, le=1.0)
    dominant_emotion: str | None = None
    emotion_scores: dict[str, float] = Field(default_factory=dict)
    affect_source: str = "unset"
    # Valid sources: "user_expressed", "inferred", "contextual", "unset"


class TemporalContext(BaseModel):
    """When the remembered event occurred and its temporal relationships."""

    occurred_at: datetime = Field(default_factory=_utc_now)
    duration: timedelta | None = None
    temporal_landmarks: list[str] = Field(default_factory=list)
    sequence_prev: UUID | None = None
    sequence_next: UUID | None = None


class ScoringState(BaseModel):
    """Mutable scoring metadata that drives salience computation."""

    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    last_accessed_at: datetime | None = None
    decay_rate: float = Field(default=0.01, ge=0.0)
    reinforcement_bonus: float = Field(default=0.0, ge=0.0)

    def effective_salience(self, now: datetime) -> float:
        """Importance adjusted for recency decay and reinforcement.

        Uses exponential decay: salience = (importance + bonus) * exp(-rate * days_since_access).
        If never accessed, days_since_access uses created_at of the parent memory.
        """
        import math

        base = min(1.0, self.importance + self.reinforcement_bonus)
        if self.last_accessed_at is None:
            return base
        elapsed = (now - self.last_accessed_at).total_seconds() / 86400.0
        if elapsed <= 0:
            return base
        return base * math.exp(-self.decay_rate * elapsed)


# ---------------------------------------------------------------------------
# Association graph
# ---------------------------------------------------------------------------


class MemoryLink(BaseModel):
    """Weighted, typed edge between two memory items."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    link_type: AssociationType
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core memory item
# ---------------------------------------------------------------------------


class MemoryItem(BaseModel):
    """Richly-typed memory with emotional, temporal, associative, and provenance context.

    This replaces the earlier flat MemoryItem. Every memory carries sub-models
    that enable multi-channel recall (keyword, temporal, entity, emotional, etc.).
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    memory_type: MemoryType
    status: MemoryStatus = MemoryStatus.ACTIVE

    # Content
    content: str
    summary: str | None = None
    entities: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)

    # Rich context
    emotional_context: EmotionalContext = Field(default_factory=EmotionalContext)
    temporal_context: TemporalContext | None = None
    provenance: ProvenanceRecord
    scoring: ScoringState = Field(default_factory=ScoringState)

    # Reconstruction support
    reconstruction_notes: str | None = None

    # System metadata
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    version: int = Field(default=1, ge=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Recall query and result
# ---------------------------------------------------------------------------


class RecallCue(BaseModel):
    """Multi-dimensional retrieval query sent to the recall engine."""

    user_id: UUID
    text_query: str | None = None
    time_range: tuple[datetime, datetime] | None = None
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    emotional_valence_range: tuple[float, float] | None = None
    memory_types: list[MemoryType] | None = None
    linked_to: UUID | None = None
    exclude_ids: list[UUID] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class ActivationTrace(BaseModel):
    """Rich trace explaining how activation reached a memory via graph traversal."""
    seed_id: UUID
    path: list[dict[str, Any]] = Field(default_factory=list)
    # Example step: {"from": id, "edge": "temporal", "to": id, "strength": 0.8, "inhibition": 0.5, "activation": 0.4}

class RecallResult(BaseModel):
    """A scored memory returned by a recall channel or fusion engine."""

    memory: MemoryItem
    relevance_score: float = Field(ge=0.0)
    seed_score: float = Field(default=0.0)
    propagated_score: float = Field(default=0.0)
    activation_trace: ActivationTrace | None = None
    channel_scores: dict[str, float] = Field(default_factory=dict)
    recall_channel: str = "unknown"


# ---------------------------------------------------------------------------
# Working memory
# ---------------------------------------------------------------------------


class WorkingMemory(BaseModel):
    """Bounded active context for the current conversation.

    This is the 'scratchpad' that the conversation engine assembles
    each turn. It holds recent turns, retrieved memories, and the
    active topic/entity/affect state.
    """

    user_id: UUID
    conversation_id: UUID
    recent_turns: list[Any] = Field(default_factory=list)  # ConversationTurn refs
    active_memories: list[MemoryItem] = Field(default_factory=list)
    active_topics: list[str] = Field(default_factory=list)
    active_entities: list[str] = Field(default_factory=list)
    current_affect: dict[str, Any] = Field(default_factory=dict)
    capacity: int = Field(default=12, ge=1)

    def is_at_capacity(self) -> bool:
        return len(self.active_memories) >= self.capacity


# ---------------------------------------------------------------------------
# Reflection, consolidation, contradiction
# ---------------------------------------------------------------------------


class ContradictionRecord(BaseModel):
    """Records a detected conflict between two memories."""

    id: UUID = Field(default_factory=uuid4)
    memory_a_id: UUID
    memory_b_id: UUID
    description: str
    resolution: str = "unresolved"
    # Valid resolutions: "keep_newer", "keep_both", "flag_for_user", "merged", "unresolved"
    resolved_at: datetime | None = None


class ReflectionResult(BaseModel):
    """Output of a reflection operation over a set of memories."""

    reflection_id: UUID = Field(default_factory=uuid4)
    source_memory_ids: list[UUID] = Field(default_factory=list)
    insight: str
    reflection_type: str  # "pattern", "generalization", "emotional_theme"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    provenance: ProvenanceRecord


class ConsolidationResult(BaseModel):
    """Output of a consolidation operation merging episodic → semantic."""

    consolidated_id: UUID = Field(default_factory=uuid4)
    absorbed_ids: list[UUID] = Field(default_factory=list)
    new_semantic_content: str
    contradictions_found: list[ContradictionRecord] = Field(default_factory=list)
    provenance: ProvenanceRecord
