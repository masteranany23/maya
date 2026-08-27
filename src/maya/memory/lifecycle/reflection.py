"""Reflection engine stub.

Provides the protocol-compatible interface for generating higher-order
insights from memories. The actual LLM-powered reflection is Phase 2 work;
this stub uses simple heuristics for testing the pipeline.
"""

from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from maya.core.protocols import LLMProvider
from maya.memory.models import (
    MemoryItem,
    ProvenanceRecord,
    ReflectionResult,
    _utc_now,
)


class ReflectionOutput(BaseModel):
    insights: list[dict[str, Any]] = Field(
        description="List of insights. Each dict should have 'insight' (str), 'reflection_type' (str), and 'confidence' (float 0-1)."
    )

class LLMReflectionEngine:
    """LLM-backed reflection engine.
    
    Retrieves clusters of memories, provides evidence to the LLM,
    and generates structured candidate insights.
    """
    
    def __init__(self, llm: LLMProvider, min_memories: int = 3) -> None:
        self.llm = llm
        self._min_memories = min_memories

    async def reflect(self, memories: list[MemoryItem]) -> list[ReflectionResult]:
        if len(memories) < self._min_memories:
            return []

        # P1.4: Provide evidence to the reasoning provider
        evidence_text = "\n".join(
            f"- [ID: {m.id}] {m.content} (Topics: {m.topics})"
            for m in memories
        )
        
        system_prompt = (
            "You are a reflection engine for a cognitive architecture. "
            "Analyze the provided memories and generate higher-order insights, "
            "patterns, or emotional themes. Return a structured list of insights. "
            "Types can be 'pattern', 'generalization', or 'emotional_theme'."
        )
        user_prompt = f"Memories:\n{evidence_text}"

        try:
            # P1.4: Generate candidate insights and validate structured output
            output = await self.llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=ReflectionOutput,
            )
            if not isinstance(output, ReflectionOutput):
                raise ValueError("LLM did not return ReflectionOutput")
        except Exception as e:
            # fallback or ignore on failure
            import logging
            logging.getLogger(__name__).error(f"Reflection failed: {e}")
            return []

        results: list[ReflectionResult] = []
        source_ids = [m.id for m in memories]
        
        for item in output.insights:
            insight_text = item.get("insight", "")
            r_type = item.get("reflection_type", "pattern")
            confidence = item.get("confidence", 0.5)
            
            if not insight_text:
                continue

            # P1.4: Attach supporting memory IDs, assign confidence, store provenance
            results.append(
                ReflectionResult(
                    reflection_id=uuid4(),
                    source_memory_ids=source_ids,
                    insight=insight_text,
                    reflection_type=r_type,
                    confidence=confidence,
                    provenance=ProvenanceRecord(
                        source_type="reflection",
                        evidence_ids=source_ids,
                        method="synthesis",
                        confidence=confidence,
                        created_at=_utc_now(),
                    ),
                )
            )

        return results

class StubReflectionEngine:
    """Stub reflection engine for pipeline testing.
    
    Generates simple pattern-based insights from memory topic/entity
    frequency. Kept for fallback/testing.
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

