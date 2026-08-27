"""Temporal recall channel.

Scores memories by temporal proximity and recency. Supports time-range
filtering from RecallCue and recency-weighted scoring.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class TemporalRecallChannel:
    """Recall channel that scores by temporal relevance."""

    def __init__(self, recency_half_life_days: float = 7.0) -> None:
        self._half_life_days = recency_half_life_days

    @property
    def channel_name(self) -> str:
        return "temporal"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        now = datetime.now(UTC)
        results: list[RecallResult] = []

        for item in candidates:
            score = self._score_item(item, cue, now)
            if score > 0:
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

    def _score_item(
        self, item: MemoryItem, cue: RecallCue, now: datetime
    ) -> float:
        event_time = (
            item.temporal_context.occurred_at
            if item.temporal_context
            else item.created_at
        )

        # If time_range specified, items outside the range get zero
        if cue.time_range is not None:
            start, end = cue.time_range
            if event_time < start or event_time > end:
                return 0.0
            # Items inside range get a time-range bonus
            range_score = 0.5
        else:
            range_score = 0.0

        # Recency score: exponential decay from now
        days_ago = max(0.0, (now - event_time).total_seconds() / 86400.0)
        decay_constant = math.log(2) / self._half_life_days
        recency_score = math.exp(-decay_constant * days_ago)

        return min(1.0, range_score + recency_score)
