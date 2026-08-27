from __future__ import annotations

from maya.core.models import AffectState, ConversationTurn


class KeywordAffectAnalyzer:
    async def analyze(self, turn: ConversationTurn) -> AffectState:
        text = turn.text.lower()
        positive = {"happy", "great", "excited", "love", "thanks", "awesome"}
        negative = {"sad", "angry", "upset", "terrible", "hate", "lonely", "worried"}
        p = sum(word in text for word in positive)
        n = sum(word in text for word in negative)
        if p == n == 0:
            return AffectState(confidence=0.1)
        valence = max(-1.0, min(1.0, (p - n) / max(1, p + n)))
        label = "positive" if valence > 0 else "negative"
        return AffectState(
            valence=valence,
            arousal=min(1.0, 0.25 + 0.15 * (p + n)),
            emotions={label: abs(valence)},
            confidence=0.45,
            trigger="keyword heuristic",
        )
