"""Multi-channel cueing and associative spreading activation engine.

Implements a 2-stage retrieval cognitive architecture (e.g., SYNAPSE, HeLa-Mem):
1. Candidate Generation & Cueing: Evaluate multiple retrieval strategies to generate seed activations.
2. Spreading Activation: Propagate activation across the MemoryLink graph.
3. Ranking & Reconstruction: Select the top activated memories.

See docs/DECISIONS.md ADR-0006, and Cueing + Activation.
"""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
from uuid import UUID

from maya.memory.models import MemoryItem, RecallCue, RecallResult
from maya.memory.protocols import ActivationEngine


class FusionStrategy(StrEnum):
    WEIGHTED_SUM = "weighted_sum"
    RANK_FUSION = "rank_fusion"
    MAX_OF = "max_of"


class MultiChannelRecallEngine:
    """Orchestrates candidate generation, cueing, spreading activation, and ranking."""

    def __init__(
        self,
        *,
        channels: list[_Channel],
        reader: _Reader,
        activation_engine: ActivationEngine | None = None,
        weights: dict[str, float] | None = None,
        strategy: FusionStrategy = FusionStrategy.WEIGHTED_SUM,
        salience_threshold: float = 0.05,
    ) -> None:
        self._channels = channels
        self._reader = reader
        self._activation_engine = activation_engine
        self._weights = weights or {}
        self._strategy = strategy
        self._salience_threshold = salience_threshold

    async def recall(self, cue: RecallCue) -> list[RecallResult]:
        # 1. Candidate Generation
        candidates = await self._reader.list_by_user(
            cue.user_id,
            types=cue.memory_types,
        )

        if cue.exclude_ids:
            exclude_set = set(cue.exclude_ids)
            candidates = [c for c in candidates if c.id not in exclude_set]

        if not candidates:
            return []

        # 2. Multi-Channel Cueing (Seed Generation)
        channel_results: dict[str, list[RecallResult]] = {}
        for channel in self._channels:
            results = await channel.recall(cue, candidates)
            channel_results[channel.channel_name] = results

        # Fuse seed scores
        if self._strategy == FusionStrategy.WEIGHTED_SUM:
            seed_results = self._fuse_weighted_sum(channel_results)
        elif self._strategy == FusionStrategy.RANK_FUSION:
            seed_results = self._fuse_rank(channel_results)
        elif self._strategy == FusionStrategy.MAX_OF:
            seed_results = self._fuse_max(channel_results)
        else:
            seed_results = self._fuse_weighted_sum(channel_results)

        seed_activations = {
            r.memory.id: r.relevance_score
            for r in seed_results
            if r.relevance_score > 0
        }
        memory_map = {c.id: c for c in candidates}

        # 3. Spreading Activation
        if self._activation_engine and seed_activations:
            propagated_results = await self._activation_engine.activate(seed_activations)
        else:
            propagated_results = {}

        # 4. Ranking & Trace Reconstruction
        final_results: list[RecallResult] = []
        
        # We need to consider all seeds + all propagated nodes
        all_ids = set(seed_activations.keys()) | set(propagated_results.keys())

        # If ActivationEngine found nodes not in our original candidates list, fetch them.
        missing_ids = [uid for uid in all_ids if uid not in memory_map]
        if missing_ids:
            fetched = await self._reader.get_batch(missing_ids)
            for m in fetched:
                memory_map[m.id] = m

        for uid in all_ids:
            if uid in cue.exclude_ids:
                continue

            memory = memory_map.get(uid)
            if not memory:
                continue

            seed_score = seed_activations.get(uid, 0.0)
            propagated_data = propagated_results.get(uid)
            
            if propagated_data:
                propagated_score, trace = propagated_data
            else:
                propagated_score, trace = 0.0, None

            # Final activation is the max of seed vs propagated
            # If it's a seed, it usually has its own high score, but propagation 
            # might have brought it more activation (rare, due to attenuation).
            final_score = max(seed_score, propagated_score)

            if final_score >= self._salience_threshold:
                # Reconstruct original channel scores if it was a seed
                ch_scores = {}
                for sr in seed_results:
                    if sr.memory.id == uid:
                        ch_scores = sr.channel_scores
                        break

                final_results.append(
                    RecallResult(
                        memory=memory,
                        relevance_score=final_score,
                        seed_score=seed_score,
                        propagated_score=propagated_score,
                        activation_trace=trace,
                        channel_scores=ch_scores,
                        recall_channel="fused_activation",
                    )
                )

        final_results.sort(key=lambda r: r.relevance_score, reverse=True)
        return final_results[: cue.limit]

    def _fuse_weighted_sum(
        self, channel_results: dict[str, list[RecallResult]]
    ) -> list[RecallResult]:
        memory_scores: dict[UUID, dict[str, float]] = defaultdict(dict)
        memory_map: dict[UUID, MemoryItem] = {}

        for ch_name, results in channel_results.items():
            weight = self._weights.get(ch_name, 1.0)
            for r in results:
                memory_scores[r.memory.id][ch_name] = r.relevance_score * weight
                memory_map[r.memory.id] = r.memory

        total_weight = sum(self._weights.get(ch.channel_name, 1.0) for ch in self._channels)
        if total_weight == 0:
            total_weight = 1.0

        fused: list[RecallResult] = []
        for mem_id, scores in memory_scores.items():
            combined = sum(scores.values()) / total_weight
            fused.append(
                RecallResult(
                    memory=memory_map[mem_id],
                    relevance_score=min(1.0, combined),
                    channel_scores=scores,
                    recall_channel="fused_weighted_sum",
                )
            )
        return fused

    def _fuse_rank(
        self, channel_results: dict[str, list[RecallResult]]
    ) -> list[RecallResult]:
        k = 60
        memory_rrf: dict[UUID, float] = defaultdict(float)
        memory_map: dict[UUID, MemoryItem] = {}
        memory_ch_scores: dict[UUID, dict[str, float]] = defaultdict(dict)

        for ch_name, results in channel_results.items():
            for rank, r in enumerate(results):
                memory_rrf[r.memory.id] += 1.0 / (k + rank + 1)
                memory_map[r.memory.id] = r.memory
                memory_ch_scores[r.memory.id][ch_name] = r.relevance_score

        max_score = max(memory_rrf.values()) if memory_rrf else 1.0

        fused: list[RecallResult] = []
        for mem_id, rrf_score in memory_rrf.items():
            fused.append(
                RecallResult(
                    memory=memory_map[mem_id],
                    relevance_score=min(1.0, rrf_score / max_score),
                    channel_scores=memory_ch_scores[mem_id],
                    recall_channel="fused_rrf",
                )
            )
        return fused

    def _fuse_max(
        self, channel_results: dict[str, list[RecallResult]]
    ) -> list[RecallResult]:
        memory_max: dict[UUID, float] = {}
        memory_map: dict[UUID, MemoryItem] = {}
        memory_ch_scores: dict[UUID, dict[str, float]] = defaultdict(dict)

        for ch_name, results in channel_results.items():
            for r in results:
                current = memory_max.get(r.memory.id, 0.0)
                if r.relevance_score > current:
                    memory_max[r.memory.id] = r.relevance_score
                memory_map[r.memory.id] = r.memory
                memory_ch_scores[r.memory.id][ch_name] = r.relevance_score

        fused: list[RecallResult] = []
        for mem_id, max_score in memory_max.items():
            fused.append(
                RecallResult(
                    memory=memory_map[mem_id],
                    relevance_score=max_score,
                    channel_scores=memory_ch_scores[mem_id],
                    recall_channel="fused_max",
                )
            )
        return fused


from typing import Protocol, runtime_checkable

@runtime_checkable
class _Channel(Protocol):
    @property
    def channel_name(self) -> str: ...

    async def recall(
        self, cue: RecallCue, candidates: list[MemoryItem]
    ) -> list[RecallResult]: ...

@runtime_checkable
class _Reader(Protocol):
    async def list_by_user(
        self,
        user_id: UUID,
        *,
        types: list | None = None,
        statuses: list | None = None,
    ) -> list[MemoryItem]: ...

    async def get_batch(self, item_ids: list[UUID]) -> list[MemoryItem]: ...
