"""Cognitive Maintenance Service.

Performs background housekeeping on the memory store, including
decay sweeps, semantic consolidation, and contradiction resolution.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from maya.memory.models import MemoryStatus, MemoryType, _utc_now

logger = logging.getLogger(__name__)

class MemoryMaintenanceService:
    def __init__(
        self,
        reader: Any,
        writer: Any,
        consolidation_engine: Any | None = None,
        contradiction_detector: Any | None = None,
        resolution_policy: Any | None = None,
        decay_threshold: float = 0.1,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.consolidation_engine = consolidation_engine
        self.contradiction_detector = contradiction_detector
        self.resolution_policy = resolution_policy
        self.decay_threshold = decay_threshold

    async def run_decay_sweep(self, user_id: UUID) -> int:
        """Finds memories whose effective salience has fallen below threshold and decays them."""
        active_memories = await self.reader.list_by_user(user_id, statuses=[MemoryStatus.ACTIVE])
        now = _utc_now()
        decayed_count = 0
        
        for mem in active_memories:
            if mem.memory_type == MemoryType.PROFILE:
                continue
                
            salience = mem.scoring.effective_salience(now)
            if salience < self.decay_threshold:
                await self.writer.update_status(mem.id, MemoryStatus.DECAYED)
                decayed_count += 1
                
        logger.info(f"Decay sweep for user {user_id}: decayed {decayed_count} memories.")
        return decayed_count

    async def run_consolidation(self, user_id: UUID, limit: int = 20) -> list[Any]:
        """Runs consolidation on recent episodic memories."""
        if not self.consolidation_engine:
            return []
            
        episodes = await self.reader.list_by_user(
            user_id, 
            types=[MemoryType.EPISODIC],
            statuses=[MemoryStatus.ACTIVE]
        )
        
        if len(episodes) < 2:
            return []
            
        episodes.sort(key=lambda m: m.created_at)
        target_episodes = episodes[:limit]
        
        result = await self.consolidation_engine.consolidate(target_episodes)
        
        if result:
            from maya.memory.models import MemoryItem
            semantic_mem = MemoryItem(
                user_id=user_id,
                memory_type=MemoryType.SEMANTIC,
                content=result.new_semantic_content,
                provenance=result.provenance,
            )
            await self.writer.write(semantic_mem)
            
            for absorbed_id in result.absorbed_ids:
                await self.writer.update_status(absorbed_id, MemoryStatus.SUPERSEDED)
                
            return [result]
        return []

    async def run_contradiction_sweep(self, user_id: UUID) -> list[Any]:
        """Finds contradictions between latest memories and resolves them."""
        if not self.contradiction_detector or not self.resolution_policy:
            return []
            
        memories = await self.reader.list_by_user(user_id, statuses=[MemoryStatus.ACTIVE])
        if len(memories) < 2:
            return []
            
        memories.sort(key=lambda m: m.created_at, reverse=True)
        candidate = memories[0]
        existing = memories[1:]
        
        contradictions = await self.contradiction_detector.detect(existing, candidate)
        resolved_records = []
        
        for record in contradictions:
            mem_a = next((m for m in existing if m.id == record.memory_a_id), None)
            if mem_a:
                resolved = await self.resolution_policy.resolve(record, mem_a, candidate)
                resolved_records.append(resolved)
                
        return resolved_records
