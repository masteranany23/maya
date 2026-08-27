"""Simple consolidation engine.

Merges repeated episodic patterns into semantic memories.
Operates on heuristics (topic/entity co-occurrence frequency).
LLM-powered summarization is a future enhancement.
"""

from __future__ import annotations

from collections import Counter
from uuid import uuid4

from pydantic import BaseModel, Field

from maya.core.protocols import LLMProvider
from maya.memory.models import (
    ConsolidationResult,
    MemoryItem,
    MemoryType,
    ProvenanceRecord,
    _utc_now,
)


class ConsolidationOutput(BaseModel):
    new_semantic_content: str = Field(description="The consolidated factual summary.")
    confidence: float = Field(default=0.8, description="Confidence in this semantic fact (0 to 1).")

class StructuredConsolidationEngine:
    """Intelligent consolidation engine.

    Uses an LLM to merge repeated episodic patterns into semantic memories.
    Retains source episode IDs and supports superseding rather than overwriting.
    """

    def __init__(self, llm: LLMProvider, min_occurrences: int = 3) -> None:
        self.llm = llm
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

        # Use LLM to consolidate
        evidence_text = "\n".join(
            f"- [ID: {m.id}] {m.content}" for m in related
        )
        
        system_prompt = (
            "You are a memory consolidation engine. Synthesize the provided episodic "
            "memories into a single, cohesive semantic fact or summary. Ensure no details "
            "are hallucinated."
        )
        user_prompt = f"Topic: {dominant_topic}\nMemories:\n{evidence_text}"

        try:
            output = await self.llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=ConsolidationOutput,
            )
            if not isinstance(output, ConsolidationOutput):
                raise ValueError("Invalid schema returned.")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Consolidation failed: {e}")
            return None

        return ConsolidationResult(
            consolidated_id=uuid4(),
            absorbed_ids=[m.id for m in related],
            new_semantic_content=output.new_semantic_content,
            provenance=ProvenanceRecord(
                source_type="consolidation",
                evidence_ids=[m.id for m in related],
                confidence=output.confidence,
                method="synthesis",
                created_at=_utc_now(),
            ),
        )

class SimpleConsolidationEngine:
    """Consolidates episodic memories into semantic memories.

    Strategy: if N+ episodic memories share the same topic, they can be
    merged into a single semantic memory. The content is a concatenation
    summary (LLM summarization is future work). Kept for testing fallback.
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
