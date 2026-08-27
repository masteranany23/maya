"""Heuristic importance scorer.

Scores memory importance without requiring an LLM call, using content
characteristics like length, entity count, emotional intensity, and keywords.
"""

from __future__ import annotations

from typing import Any


class HeuristicImportanceScorer:
    """Scores importance using content-based heuristics.

    Scoring factors:
    - Content length (longer → more detail → potentially more important)
    - Entity count (more entities → more specific → more important)
    - Emotional intensity (high arousal → more salient)
    - High-signal keywords (names, dates, promises, preferences)
    """

    HIGH_SIGNAL_KEYWORDS = {
        "birthday", "anniversary", "name", "favorite", "hate", "love",
        "promise", "remember", "important", "always", "never",
        "afraid", "dream", "goal", "plan", "died", "born",
        "married", "divorced", "job", "moved", "allergic",
    }

    async def score(self, content: str, context: dict[str, Any]) -> float:
        score = 0.3  # base importance

        # Length factor (logarithmic, caps out)
        word_count = len(content.split())
        if word_count > 20:
            score += 0.1
        if word_count > 50:
            score += 0.05

        # Entity factor
        entity_count = len(context.get("entities", []))
        score += min(0.15, entity_count * 0.05)

        # Emotional intensity
        arousal = context.get("arousal", 0.0)
        score += arousal * 0.15

        # High-signal keyword presence
        content_lower = content.lower()
        keyword_hits = sum(1 for kw in self.HIGH_SIGNAL_KEYWORDS if kw in content_lower)
        score += min(0.15, keyword_hits * 0.05)

        return min(1.0, max(0.0, score))
