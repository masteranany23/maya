"""Importance-weighted recall channel.

Scores memories by their effective salience (importance × decay × reinforcement).
This channel surfaces high-importance memories regardless of textual relevance.
"""

from __future__ import annotations

from datetime import datetime, timezone

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class ImportanceRecallChannel:
    """Recall channel that scores by effective salience."""

    def __init__(self, min_salience: float = 0.1) -> None:
        self._min_salience = min_salience

    @property
    def channel_name(self) -> str:
        return "importance"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        now = datetime.now(timezone.utc)
        results: list[RecallResult] = []

        for item in candidates:
            salience = item.scoring.effective_salience(now)
            if salience < self._min_salience:
                continue
            results.append(
                RecallResult(
                    memory=item,
                    relevance_score=min(1.0, salience),
                    channel_scores={self.channel_name: salience},
                    recall_channel=self.channel_name,
                )
            )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results
