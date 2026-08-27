"""Simple consolidation engine.

Merges repeated episodic patterns into semantic memories.
Operates on heuristics (topic/entity co-occurrence frequency).
LLM-powered summarization is a future enhancement.
"""

from __future__ import annotations

from collections import Counter
from uuid import uuid4

from maya.memory.models import (
    ConsolidationResult,
    MemoryItem,
    MemoryType,
    ProvenanceRecord,
    _utc_now,
)


class SimpleConsolidationEngine:
    """Consolidates episodic memories into semantic memories.

    Strategy: if N+ episodic memories share the same topic, they can be
    merged into a single semantic memory. The content is a concatenation
    summary (LLM summarization is future work).
    """

    def __init__(self, min_occurrences: int = 3) -> None:
        self._min_occurrences = min_occurrences

    async def consolidate(
        self, episodic_memories: list[MemoryItem]
    ) -> ConsolidationResult | None:
        # Only process episodic memories
        episodes = [
            m for m in episodic_memories if m.memory_type == MemoryType.EPISODIC
        ]
        if len(episodes) < self._min_occurrences:
            return None

        # Find the most common topic across episodes
        topic_counter: Counter[str] = Counter()
        for m in episodes:
            for topic in m.topics:
                topic_counter[topic.lower()] += 1

        if not topic_counter:
            return None

        dominant_topic, count = topic_counter.most_common(1)[0]
        if count < self._min_occurrences:
            return None

        # Gather memories for the dominant topic
        related = [
            m for m in episodes
            if dominant_topic in {t.lower() for t in m.topics}
        ]

        # Build a simple consolidated summary
        content_parts = [m.content[:100] for m in related[:5]]
        consolidated_content = (
            f"Recurring pattern about '{dominant_topic}': "
            + " | ".join(content_parts)
        )

        return ConsolidationResult(
            consolidated_id=uuid4(),
            absorbed_ids=[m.id for m in related],
            new_semantic_content=consolidated_content,
            provenance=ProvenanceRecord(
                source_type="consolidation",
                evidence_ids=[m.id for m in related],
                confidence=min(1.0, 0.5 + count * 0.1),
                method="synthesis",
                created_at=_utc_now(),
            ),
        )
