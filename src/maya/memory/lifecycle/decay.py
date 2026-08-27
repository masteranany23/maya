"""Decay function implementations.

Provides configurable time-based salience decay for memory items.
See docs/DECISIONS.md ADR-0008.
"""

from __future__ import annotations

import math
from datetime import datetime

from maya.memory.models import ScoringState


class ExponentialDecayFunction:
    """Computes salience using exponential time decay.

    salience = (importance + reinforcement_bonus) * exp(-decay_rate * days_elapsed)
    """

    def compute_salience(self, scoring: ScoringState, now: datetime) -> float:
        return scoring.effective_salience(now)


class StepDecayFunction:
    """Discrete step decay — full salience within threshold, zero after.

    Useful for testing and for working memory with hard cutoffs.
    """

    def __init__(self, max_age_days: float = 30.0) -> None:
        self._max_age_days = max_age_days

    def compute_salience(self, scoring: ScoringState, now: datetime) -> float:
        base = min(1.0, scoring.importance + scoring.reinforcement_bonus)
        if scoring.last_accessed_at is None:
            return base
        elapsed_days = (now - scoring.last_accessed_at).total_seconds() / 86400.0
        return base if elapsed_days <= self._max_age_days else 0.0
