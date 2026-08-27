"""Memory subsystem protocols — storage, retrieval, and lifecycle.

Separates persistence (MemoryWriter/MemoryReader/LinkStore) from retrieval
(RecallChannel/RecallEngine) and lifecycle operations (ImportanceScorer,
DecayFunction, ReflectionEngine, ConsolidationEngine, ContradictionDetector).

See docs/DECISIONS.md ADR-0006, ADR-0009.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from maya.memory.models import (
    ActivationTrace,
    AssociationType,
    ConsolidationResult,
    ContradictionRecord,
    MemoryItem,
    MemoryLink,
    MemoryStatus,
    MemoryType,
    RecallCue,
    RecallResult,
    ReflectionResult,
    ScoringState,
    WorkingMemory,
)

# ---------------------------------------------------------------------------
# Storage protocols (persistence-agnostic)
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryWriter(Protocol):
    """Writes and updates memory items in a storage backend."""

    async def write(self, item: MemoryItem) -> MemoryItem: ...

    async def update(self, item_id: UUID, **fields: Any) -> MemoryItem: ...

    async def update_status(self, item_id: UUID, status: MemoryStatus) -> None: ...


@runtime_checkable
class MemoryReader(Protocol):
    """Reads memory items from a storage backend."""

    async def get(self, item_id: UUID) -> MemoryItem | None: ...

    async def get_batch(self, item_ids: list[UUID]) -> list[MemoryItem]: ...

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        types: list[MemoryType] | None = None,
        statuses: list[MemoryStatus] | None = None,
    ) -> list[MemoryItem]: ...


@runtime_checkable
class LinkStore(Protocol):
    """Manages association links between memory items."""

    async def add_link(self, link: MemoryLink) -> MemoryLink: ...

    async def get_links(
        self,
        memory_id: UUID,
        *,
        link_types: list[AssociationType] | None = None,
        direction: str = "outgoing",  # "outgoing", "incoming", "both"
    ) -> list[MemoryLink]: ...

    async def remove_link(self, source_id: UUID, target_id: UUID) -> None: ...


# ---------------------------------------------------------------------------
# Recall protocols (composable retrieval)
# ---------------------------------------------------------------------------


@runtime_checkable
class RecallChannel(Protocol):
    """Single retrieval strategy. Many channels are fused by RecallEngine."""

    @property
    def channel_name(self) -> str: ...

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]: ...


@runtime_checkable
class RecallEngine(Protocol):
    """Fuses multiple recall channels into a ranked result list."""

    async def recall(self, cue: RecallCue) -> list[RecallResult]: ...


@runtime_checkable
class ActivationEngine(Protocol):
    """Propagates activation through the memory graph from initial seeds."""

    async def activate(
        self, seeds: dict[UUID, float]
    ) -> dict[UUID, tuple[float, ActivationTrace]]: ...


# ---------------------------------------------------------------------------
# Lifecycle protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class ImportanceScorer(Protocol):
    """Computes importance for a memory item."""

    async def score(self, content: str, context: dict[str, Any]) -> float: ...


@runtime_checkable
class DecayFunction(Protocol):
    """Computes effective salience given scoring state and current time."""

    def compute_salience(self, scoring: ScoringState, now: datetime) -> float: ...


@runtime_checkable
class ReflectionEngine(Protocol):
    """Generates higher-order insights from a set of memories."""

    async def reflect(self, memories: list[MemoryItem]) -> list[ReflectionResult]: ...


@runtime_checkable
class ConsolidationEngine(Protocol):
    """Merges repeated episodic patterns into semantic memories."""

    async def consolidate(
        self, episodic_memories: list[MemoryItem]
    ) -> ConsolidationResult | None: ...


@runtime_checkable
class ContradictionDetector(Protocol):
    """Detects conflicts between an incoming memory and existing ones."""

    async def detect(
        self, existing: list[MemoryItem], candidate: MemoryItem
    ) -> list[ContradictionRecord]: ...


# ---------------------------------------------------------------------------
# High-level facade
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryManager(Protocol):
    """High-level facade used by ConversationEngine.

    Orchestrates storage, recall, reinforcement, and working memory.
    """

    async def remember(self, cue: RecallCue) -> list[RecallResult]: ...

    async def memorize(self, item: MemoryItem) -> MemoryItem: ...

    async def reinforce(self, memory_id: UUID) -> None: ...

    async def get_working_memory(
        self, user_id: UUID, conversation_id: UUID
    ) -> WorkingMemory: ...
