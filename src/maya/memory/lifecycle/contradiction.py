"""Contradiction detection for memory items.

Detects conflicts between incoming memories and existing ones using
entity + topic overlap and content-based heuristics.
"""

from __future__ import annotations

import re

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


def _extract_terms(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"\w+", text) if len(t) >= 3}
