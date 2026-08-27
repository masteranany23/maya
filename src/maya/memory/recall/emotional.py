"""Emotional recall channel.

Scores memories by emotional similarity — matching valence/arousal ranges
and dominant emotion overlap.
"""

from __future__ import annotations

from maya.memory.models import MemoryItem, RecallCue, RecallResult


class EmotionalRecallChannel:
    """Recall channel that scores by emotional context similarity."""

    @property
    def channel_name(self) -> str:
        return "emotional"

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]:
        if cue.emotional_valence_range is None:
            return []

        v_min, v_max = cue.emotional_valence_range
        results: list[RecallResult] = []

        for item in candidates:
            ec = item.emotional_context
            if ec.affect_source == "unset":
                continue

            # Check if memory's valence falls in the requested range
            if ec.valence < v_min or ec.valence > v_max:
                continue

            # Score: how centered the memory's valence is in the range
            range_width = max(0.01, v_max - v_min)
            center = (v_min + v_max) / 2.0
            distance = abs(ec.valence - center) / (range_width / 2.0)
            score = max(0.0, 1.0 - distance)

            # Arousal bonus: higher arousal memories are more emotionally salient
            score = min(1.0, score + ec.arousal * 0.2)

            results.append(
                RecallResult(
                    memory=item,
                    relevance_score=score,
                    channel_scores={self.channel_name: score},
                    recall_channel=self.channel_name,
                )
            )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results
