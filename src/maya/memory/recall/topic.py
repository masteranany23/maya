"""Topic-based recall channel.

Scores memories by overlap between query topics and memory topics.
"""

from __future__ import annotations

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class TopicRecallChannel:
    """Recall channel that scores by topic tag overlap."""

    @property
    def channel_name(self) -> str:
        return "topic"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        if not cue.topics:
            return []

        query_topics = {t.lower() for t in cue.topics}
        results: list[RecallResult] = []

        for item in candidates:
            item_topics = {t.lower() for t in item.topics}
            overlap = query_topics & item_topics
            if not overlap:
                continue
            score = len(overlap) / len(query_topics)
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
