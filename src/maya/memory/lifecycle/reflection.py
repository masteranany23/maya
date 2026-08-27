"""Reflection engine stub.

Provides the protocol-compatible interface for generating higher-order
insights from memories. The actual LLM-powered reflection is Phase 2 work;
this stub uses simple heuristics for testing the pipeline.
"""

from __future__ import annotations

from collections import Counter
from uuid import uuid4

from maya.memory.models import (
    MemoryItem,
    ProvenanceRecord,
    ReflectionResult,
    _utc_now,
)


class StubReflectionEngine:
    """Stub reflection engine for pipeline testing.

    Generates simple pattern-based insights from memory topic/entity
    frequency. Will be replaced by LLM-powered reflection in Phase 2.
    """

    def __init__(self, min_memories: int = 3) -> None:
        self._min_memories = min_memories

    async def reflect(self, memories: list[MemoryItem]) -> list[ReflectionResult]:
        if len(memories) < self._min_memories:
            return []

        results: list[ReflectionResult] = []

        # Topic frequency patterns
        topic_counter: Counter[str] = Counter()
        for m in memories:
            for t in m.topics:
                topic_counter[t.lower()] += 1

        for topic, count in topic_counter.most_common(3):
            if count >= self._min_memories:
                source_ids = [
                    m.id for m in memories
                    if topic in {t.lower() for t in m.topics}
                ]
                results.append(
                    ReflectionResult(
                        reflection_id=uuid4(),
                        source_memory_ids=source_ids,
                        insight=f"User frequently discusses '{topic}' ({count} times).",
                        reflection_type="pattern",
                        confidence=min(1.0, 0.4 + count * 0.1),
                        provenance=ProvenanceRecord(
                            source_type="reflection",
                            evidence_ids=source_ids,
                            method="synthesis",
                            confidence=min(1.0, 0.4 + count * 0.1),
                            created_at=_utc_now(),
                        ),
                    )
                )

        # Emotional theme patterns
        emotion_counter: Counter[str] = Counter()
        for m in memories:
            if m.emotional_context.dominant_emotion:
                emotion_counter[m.emotional_context.dominant_emotion] += 1

        for emotion, count in emotion_counter.most_common(2):
            if count >= self._min_memories:
                source_ids = [
                    m.id for m in memories
                    if m.emotional_context.dominant_emotion == emotion
                ]
                results.append(
                    ReflectionResult(
                        reflection_id=uuid4(),
                        source_memory_ids=source_ids,
                        insight=f"Recurring emotional theme: '{emotion}' ({count} occurrences).",
                        reflection_type="emotional_theme",
                        confidence=min(1.0, 0.3 + count * 0.1),
                        provenance=ProvenanceRecord(
                            source_type="reflection",
                            evidence_ids=source_ids,
                            method="synthesis",
                            confidence=min(1.0, 0.3 + count * 0.1),
                            created_at=_utc_now(),
                        ),
                    )
                )

        return results
