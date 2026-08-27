"""Keyword-based recall channel.

Scores memories by term overlap between the query text and memory content,
entities, and topics. Improved over the original InMemoryStore with TF-like
term weighting.
"""

from __future__ import annotations

import re

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class KeywordRecallChannel:
    """Recall channel that scores by keyword overlap."""

    @property
    def channel_name(self) -> str:
        return "keyword"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        if not cue.text_query:
            return []

        query_terms = _extract_terms(cue.text_query)
        if not query_terms:
            return []

        results: list[RecallResult] = []
        for item in candidates:
            haystack_terms = _extract_terms(item.content)
            haystack_terms.update(_extract_terms(" ".join(item.entities)))
            haystack_terms.update(_extract_terms(" ".join(item.topics)))

            overlap = query_terms & haystack_terms
            if not overlap:
                continue

            # Score: fraction of query terms found, weighted by haystack coverage
            score = len(overlap) / len(query_terms)
            results.append(
                RecallResult(
                    memory=item,
                    relevance_score=min(1.0, score),
                    channel_scores={self.channel_name: score},
                    recall_channel=self.channel_name,
                )
            )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results


def _extract_terms(text: str) -> set[str]:
    """Extract lowercase terms of 3+ characters."""
    return {t.lower() for t in re.findall(r"\w+", text) if len(t) >= 3}
