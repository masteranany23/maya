"""Association Formation Module.

Automatically creates memory links between memories without O(N^2) comparison.
Implements P1.3.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from maya.memory.models import AssociationType, MemoryItem, MemoryLink
from maya.memory.protocols import LinkStore


@runtime_checkable
class AssociationStrategy(Protocol):
    """Protocol for a specific strategy that generates links between a new memory and existing context."""

    async def form_links(
        self, new_memory: MemoryItem, context_memories: list[MemoryItem]
    ) -> list[MemoryLink]:
        """Generate potential links based on this strategy's specific rules."""
        ...


class SharedEntityStrategy:
    """Links memories that share named entities."""

    async def form_links(
        self, new_memory: MemoryItem, context_memories: list[MemoryItem]
    ) -> list[MemoryLink]:
        links = []
        new_entities = set(new_memory.entities)
        if not new_entities:
            return links

        for ctx_mem in context_memories:
            if ctx_mem.id == new_memory.id:
                continue
            shared = new_entities.intersection(ctx_mem.entities)
            if shared:
                # Add an entity link
                links.append(
                    MemoryLink(
                        source_id=new_memory.id,
                        target_id=ctx_mem.id,
                        link_type=AssociationType.ENTITY,
                        strength=min(1.0, 0.3 * len(shared)),
                        metadata={"shared_entities": list(shared)},
                    )
                )
                # Bi-directional? Usually links are directed, but we can rely on queries checking both directions or explicitly link both
                links.append(
                    MemoryLink(
                        source_id=ctx_mem.id,
                        target_id=new_memory.id,
                        link_type=AssociationType.ENTITY,
                        strength=min(1.0, 0.3 * len(shared)),
                        metadata={"shared_entities": list(shared)},
                    )
                )
        return links


class SharedTopicStrategy:
    """Links memories that share topics."""

    async def form_links(
        self, new_memory: MemoryItem, context_memories: list[MemoryItem]
    ) -> list[MemoryLink]:
        links = []
        new_topics = set(new_memory.topics)
        if not new_topics:
            return links

        for ctx_mem in context_memories:
            if ctx_mem.id == new_memory.id:
                continue
            shared = new_topics.intersection(ctx_mem.topics)
            if shared:
                links.append(
                    MemoryLink(
                        source_id=new_memory.id,
                        target_id=ctx_mem.id,
                        link_type=AssociationType.THEMATIC,
                        strength=min(1.0, 0.4 * len(shared)),
                        metadata={"shared_topics": list(shared)},
                    )
                )
        return links


class TemporalProximityStrategy:
    """Links memories that occurred closely in time."""

    def __init__(self, max_minutes: float = 30.0) -> None:
        self.max_minutes = max_minutes

    async def form_links(
        self, new_memory: MemoryItem, context_memories: list[MemoryItem]
    ) -> list[MemoryLink]:
        links = []
        if not new_memory.temporal_context or not new_memory.temporal_context.occurred_at:
            return links
            
        t1 = new_memory.temporal_context.occurred_at

        for ctx_mem in context_memories:
            if ctx_mem.id == new_memory.id or not ctx_mem.temporal_context or not ctx_mem.temporal_context.occurred_at:
                continue
            
            t2 = ctx_mem.temporal_context.occurred_at
            diff_mins = abs((t1 - t2).total_seconds()) / 60.0
            
            if diff_mins <= self.max_minutes:
                # Stronger link for closer events
                strength = max(0.1, 1.0 - (diff_mins / self.max_minutes))
                links.append(
                    MemoryLink(
                        source_id=new_memory.id,
                        target_id=ctx_mem.id,
                        link_type=AssociationType.TEMPORAL,
                        strength=strength,
                        metadata={"time_diff_mins": diff_mins},
                    )
                )
        return links


class AssociationEngine:
    """Engine that runs multiple strategies to form links and persist them."""
    
    def __init__(
        self, 
        link_store: LinkStore, 
        strategies: list[AssociationStrategy] | None = None
    ) -> None:
        self.link_store = link_store
        self.strategies = strategies or [
            SharedEntityStrategy(),
            SharedTopicStrategy(),
            TemporalProximityStrategy(),
        ]

    async def associate(
        self, new_memory: MemoryItem, context_memories: list[MemoryItem]
    ) -> list[MemoryLink]:
        """Runs all configured strategies against a bounded set of context memories."""
        all_links = []
        
        for strategy in self.strategies:
            links = await strategy.form_links(new_memory, context_memories)
            all_links.extend(links)
            
        # Deduplicate links
        existing_links = await self.link_store.get_links(new_memory.id, direction="both")
        existing_signatures = {
            (l.source_id, l.target_id, l.link_type) for l in existing_links
        }
        
        stored_links = []
        seen_signatures = set()
        
        for link in all_links:
            sig = (link.source_id, link.target_id, link.link_type)
            if sig in existing_signatures or sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            
            stored = await self.link_store.add_link(link)
            stored_links.append(stored)
            
        return stored_links
