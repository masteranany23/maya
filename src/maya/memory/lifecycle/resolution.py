"""Contradiction Resolution Policy.

Implements rules for resolving contradictions without destructively deleting memories.
Resolutions update memory states to SUPERSEDED, WEAKENED, or keep them ACTIVE,
while recording the resolution in the ContradictionRecord.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from maya.memory.models import ContradictionRecord, MemoryItem, MemoryStatus, _utc_now


class _Writer(Protocol):
    async def update_status(self, item_id: UUID, status: MemoryStatus) -> None: ...

class ContradictionResolutionPolicy:
    """Provider-independent policy for resolving contradictions."""

    def __init__(self, writer: _Writer) -> None:
        self.writer = writer

    async def resolve(
        self, record: ContradictionRecord, memory_a: MemoryItem, memory_b: MemoryItem
    ) -> ContradictionRecord:
        """Resolves the contradiction and updates memory states.
        
        Rules:
        - TEMPORAL_CHANGE: Older memory (memory_a) becomes SUPERSEDED. New is ACTIVE.
        - CONTRADICTION: Both are kept ACTIVE, but WEAKENED, flagged for user clarification.
        - CONTEXTUAL_EXCEPTION: Both kept ACTIVE.
        - UNSUPPORTED_INFERENCE: The newer memory (memory_b) is ARCHIVED.
        - AMBIGUITY: Both kept ACTIVE.
        """
        if record.resolution != "unresolved":
            return record

        desc = record.description.upper()
        now = _utc_now()
        
        if "[TEMPORAL_CHANGE]" in desc:
            await self.writer.update_status(memory_a.id, MemoryStatus.SUPERSEDED)
            record.resolution = "keep_newer"
            
        elif "[CONTRADICTION]" in desc:
            await self.writer.update_status(memory_a.id, MemoryStatus.WEAKENED)
            await self.writer.update_status(memory_b.id, MemoryStatus.WEAKENED)
            record.resolution = "flag_for_user"
            
        elif "[UNSUPPORTED_INFERENCE]" in desc:
            await self.writer.update_status(memory_b.id, MemoryStatus.ARCHIVED)
            record.resolution = "rejected_newer"
            
        else:
            # CONTEXTUAL_EXCEPTION, AMBIGUITY, or unknown
            record.resolution = "keep_both"
            
        record.resolved_at = now
        return record
