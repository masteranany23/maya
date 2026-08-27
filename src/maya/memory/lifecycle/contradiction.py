"""Contradiction detection for memory items.

Detects conflicts between incoming memories and existing ones using
entity + topic overlap and content-based heuristics.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from maya.core.protocols import LLMProvider
from maya.memory.models import ContradictionRecord, MemoryItem, MemoryType

# Patterns that indicate factual assertions (simple heuristic)
_FACT_INDICATORS = re.compile(
    r"\b(i am|i'm|my .+ is|i have|i don't|i never|i always|i hate|i love)\b",
    re.IGNORECASE,
)

# Contradiction signal pairs
_OPPOSING_PAIRS = [
    ({"vegetarian", "vegan"}, {"meat", "steak", "chicken", "pork", "beef", "bacon"}),
    ({"single", "alone"}, {"married", "engaged", "partner", "spouse", "wife", "husband"}),
    ({"employed", "job", "work"}, {"unemployed", "fired", "laid off", "quit"}),
    ({"love", "adore", "enjoy"}, {"hate", "despise", "loathe", "detest"}),
]


class HeuristicContradictionDetector:
    """Detects contradictions between memories using heuristics.

    Checks for:
    1. Entity overlap with opposing factual content
    2. Profile-type memories with conflicting values
    3. Known opposing-pair keywords
    """

    async def detect(
        self, existing: list[MemoryItem], candidate: MemoryItem
    ) -> list[ContradictionRecord]:
        contradictions: list[ContradictionRecord] = []

        # Only check factual memory types
        factual_types = {MemoryType.PROFILE, MemoryType.SEMANTIC, MemoryType.EPISODIC}
        if candidate.memory_type not in factual_types:
            return contradictions

        candidate_terms = _extract_terms(candidate.content)

        for existing_item in existing:
            if existing_item.memory_type not in factual_types:
                continue
            if existing_item.id == candidate.id:
                continue

            # Check entity overlap (same subject)
            shared_entities = set(e.lower() for e in existing_item.entities) & set(
                e.lower() for e in candidate.entities
            )
            shared_topics = set(t.lower() for t in existing_item.topics) & set(
                t.lower() for t in candidate.topics
            )

            if not shared_entities and not shared_topics:
                continue

            # Check for opposing keyword pairs
            existing_terms = _extract_terms(existing_item.content)
            for set_a, set_b in _OPPOSING_PAIRS:
                a_in_existing = bool(existing_terms & set_a)
                b_in_candidate = bool(candidate_terms & set_b)
                a_in_candidate = bool(candidate_terms & set_a)
                b_in_existing = bool(existing_terms & set_b)

                if (a_in_existing and b_in_candidate) or (b_in_existing and a_in_candidate):
                    contradictions.append(
                        ContradictionRecord(
                            memory_a_id=existing_item.id,
                            memory_b_id=candidate.id,
                            description=(
                                f"Opposing content detected between "
                                f"'{existing_item.content[:60]}...' and "
                                f"'{candidate.content[:60]}...'"
                            ),
                            resolution="unresolved",
                        )
                    )
                    break  # One contradiction per pair is enough

        return contradictions


class ContradictionOutput(BaseModel):
    contradictions: list[dict[str, Any]] = Field(
        description="List of detected contradictions. Each dict should have 'existing_id' (UUID), 'description' (str), and 'conflict_type' (str: contradiction, temporal_change, contextual_exception, ambiguity, unsupported_inference)."
    )

class LLMContradictionDetector:
    """Intelligent contradiction detection using an LLM.

    Classifies conflicts into categories: actual contradiction, temporal change,
    contextual exception, ambiguity, or unsupported inference.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def detect(
        self, existing: list[MemoryItem], candidate: MemoryItem
    ) -> list[ContradictionRecord]:
        factual_types = {MemoryType.PROFILE, MemoryType.SEMANTIC, MemoryType.EPISODIC}
        if candidate.memory_type not in factual_types:
            return []

        # Filter existing memories to those sharing entities or topics to reduce context window
        candidate_entities = set(e.lower() for e in candidate.entities)
        candidate_topics = set(t.lower() for t in candidate.topics)
        
        relevant_existing = []
        for ex in existing:
            if ex.memory_type not in factual_types or ex.id == candidate.id:
                continue
            ex_entities = set(e.lower() for e in ex.entities)
            ex_topics = set(t.lower() for t in ex.topics)
            
            if candidate_entities & ex_entities or candidate_topics & ex_topics:
                relevant_existing.append(ex)
                
        if not relevant_existing:
            return []

        # Prepare prompt
        existing_text = "\n".join(
            f"- [ID: {m.id}] {m.content}" for m in relevant_existing
        )
        
        system_prompt = (
            "You are a contradiction detector for a cognitive architecture. "
            "Compare the new candidate memory against the existing memories. "
            "Identify any conflicts and classify them strictly as one of: "
            "'contradiction', 'temporal_change', 'contextual_exception', "
            "'ambiguity', or 'unsupported_inference'. If there is no conflict, "
            "return an empty list."
        )
        
        user_prompt = (
            f"Candidate Memory: {candidate.content}\n"
            f"Existing Memories:\n{existing_text}"
        )

        try:
            output = await self.llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=ContradictionOutput,
            )
            if not isinstance(output, ContradictionOutput):
                raise ValueError("Invalid schema returned.")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Contradiction detection failed: {e}")
            return []

        contradictions: list[ContradictionRecord] = []
        for item in output.contradictions:
            existing_id_str = item.get("existing_id")
            if not existing_id_str:
                continue
            
            try:
                from uuid import UUID
                existing_id = UUID(str(existing_id_str))
            except ValueError:
                continue

            c_type = item.get("conflict_type", "contradiction")
            desc = item.get("description", f"Detected {c_type}")

            contradictions.append(
                ContradictionRecord(
                    memory_a_id=existing_id,
                    memory_b_id=candidate.id,
                    description=f"[{c_type.upper()}] {desc}",
                    resolution="unresolved",
                )
            )

        return contradictions


def _extract_terms(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"\w+", text) if len(t) >= 3}
