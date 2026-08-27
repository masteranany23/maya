"""Entity-based recall channel.

Scores memories by overlap between query entities and memory entities.
"""

from __future__ import annotations

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class EntityRecallChannel:
    """Recall channel that scores by named entity overlap."""

    @property
    def channel_name(self) -> str:
        return "entity"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        if not cue.entities:
            return []

        query_entities = {e.lower() for e in cue.entities}
        results: list[RecallResult] = []

        for item in candidates:
            item_entities = {e.lower() for e in item.entities}
            overlap = query_entities & item_entities
            if not overlap:
                continue
            score = len(overlap) / len(query_entities)
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
