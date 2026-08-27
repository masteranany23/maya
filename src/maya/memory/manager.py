"""Default MemoryManager implementation.

Orchestrates storage, multi-channel recall, reinforcement, and working memory.
This is the high-level facade used by ConversationEngine.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from maya.memory.models import (
    MemoryItem,
    RecallCue,
    RecallResult,
    WorkingMemory,
    _utc_now,
)


class DefaultMemoryManager:
    """High-level facade over storage + recall + lifecycle.

    Wires together a MemoryWriter, MemoryReader, and RecallEngine into
    the simple interface that ConversationEngine needs.
    """

    def __init__(
        self,
        *,
        writer: _Writer,
        reader: _Reader,
        recall_engine: _RecallEngine,
    ) -> None:
        self._writer = writer
        self._reader = reader
        self._recall_engine = recall_engine
        self._working_memories: dict[tuple[UUID, UUID], WorkingMemory] = {}

    async def remember(self, cue: RecallCue) -> list[RecallResult]:
        """Recall memories matching the cue, then reinforce accessed ones."""
        results = await self._recall_engine.recall(cue)

        # Reinforce: bump access_count and last_accessed_at for recalled memories
        now = _utc_now()
        for r in results:
            await self._reinforce_item(r.memory.id, now)

        return results

    async def memorize(self, item: MemoryItem) -> MemoryItem:
        """Write a new memory item to storage."""
        return await self._writer.write(item)

    async def reinforce(self, memory_id: UUID) -> None:
        """Manually reinforce a memory (e.g., when user references it)."""
        await self._reinforce_item(memory_id, _utc_now())

    async def get_working_memory(
        self, user_id: UUID, conversation_id: UUID
    ) -> WorkingMemory:
        """Get or create the working memory context for a conversation."""
        key = (user_id, conversation_id)
        if key not in self._working_memories:
            self._working_memories[key] = WorkingMemory(
                user_id=user_id,
                conversation_id=conversation_id,
            )
        return self._working_memories[key]

    async def _reinforce_item(self, memory_id: UUID, now: datetime) -> None:
        """Bump access_count and last_accessed_at for a memory."""
        item = await self._reader.get(memory_id)
        if item is None:
            return
        scoring = item.scoring
        await self._writer.update(
            memory_id,
            scoring={
                **scoring.model_dump(),
                "access_count": scoring.access_count + 1,
                "last_accessed_at": now.isoformat(),
                "reinforcement_bonus": min(
                    1.0, scoring.reinforcement_bonus + 0.05
                ),
            },
        )


# Type aliases (protocol-compatible without importing protocols module)
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _Writer(Protocol):
    async def write(self, item: MemoryItem) -> MemoryItem: ...
    async def update(self, item_id: UUID, **fields: Any) -> MemoryItem: ...


@runtime_checkable
class _Reader(Protocol):
    async def get(self, item_id: UUID) -> MemoryItem | None: ...


@runtime_checkable
class _RecallEngine(Protocol):
    async def recall(self, cue: RecallCue) -> list[RecallResult]: ...
