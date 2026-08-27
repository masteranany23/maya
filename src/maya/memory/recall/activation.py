"""Spreading activation engine.

Propagates activation across the MemoryLink graph using best-first search.
Includes degree-normalized inhibition to prevent highly-connected generic 
memories from dominating recall.

See docs/DECISIONS.md (Cueing + Activation).
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Awaitable, Callable
from uuid import UUID

from maya.memory.models import ActivationTrace, MemoryLink

# Type alias for link fetcher to avoid circular imports
_LinkGetter = Callable[[UUID], Awaitable[list[MemoryLink]]]


class SpreadingActivationEngine:
    """Best-first spreading activation over the memory graph."""

    def __init__(
        self,
        link_getter: _LinkGetter,
        attenuation_factor: float = 0.8,
        activation_threshold: float = 0.05,
        max_hops: int = 3,
        fan_out_limit: int = 20,
    ) -> None:
        self._link_getter = link_getter
        self._attenuation_factor = attenuation_factor
        self._activation_threshold = activation_threshold
        self._max_hops = max_hops
        self._fan_out_limit = fan_out_limit

    async def activate(
        self, seeds: dict[UUID, float]
    ) -> dict[UUID, tuple[float, ActivationTrace]]:
        
        # Priority queue for best-first traversal. 
        # Stores tuples: (-current_activation, current_hop, node_id, current_trace, current_activation)
        # Using negative activation because heapq is a min-heap.
        # We add id(trace) just to prevent heapq from comparing the trace objects themselves if scores tie.
        pq: list[tuple[float, int, int, UUID, ActivationTrace, float]] = []
        for seed_id, seed_score in seeds.items():
            if seed_score >= self._activation_threshold:
                trace = ActivationTrace(seed_id=seed_id, path=[])
                heapq.heappush(pq, (-seed_score, 0, id(trace), seed_id, trace, seed_score))

        final_activations: dict[UUID, float] = {}
        final_traces: dict[UUID, ActivationTrace] = {}

        while pq:
            neg_act, hop, _, current_id, trace, current_act = heapq.heappop(pq)
            
            # If we've already found a better path to this node, skip
            if current_id in final_activations and final_activations[current_id] >= current_act:
                continue

            # Record this activation
            final_activations[current_id] = current_act
            final_traces[current_id] = trace

            if hop >= self._max_hops:
                continue

            links = await self._link_getter(current_id)
            if not links:
                continue

            # Sort links by strength to respect fan_out_limit with strongest edges first
            links.sort(key=lambda lnk: lnk.strength, reverse=True)
            links = links[:self._fan_out_limit]

            degree = len(links)
            # e.g. degree 1 or 2 -> div by 1.0. degree 10 -> div by 2.0+
            inhibition_factor = math.log1p(max(0, degree - 2)) + 1.0

            for link in links:
                neighbor_id = link.target_id if link.source_id == current_id else link.source_id
                
                # Prevent cycles back to seed
                if neighbor_id == trace.seed_id:
                    continue
                # Simple cycle check
                if any(step.get("to") == neighbor_id for step in trace.path):
                    continue

                # Calculate propagated activation
                propagated = (current_act * self._attenuation_factor * link.strength) / inhibition_factor
                
                if propagated >= self._activation_threshold:
                    # Only add if it improves the known activation (or we haven't visited)
                    if neighbor_id not in final_activations or propagated > final_activations[neighbor_id]:
                        new_path = trace.path.copy()
                        new_path.append({
                            "from": current_id,
                            "edge": link.link_type,
                            "to": neighbor_id,
                            "strength": link.strength,
                            "inhibition": round(inhibition_factor, 3),
                            "activation": round(propagated, 3),
                        })
                        new_trace = ActivationTrace(seed_id=trace.seed_id, path=new_path)
                        heapq.heappush(pq, (-propagated, hop + 1, id(new_trace), neighbor_id, new_trace, propagated))

        return {
            uid: (act, final_traces[uid])
            for uid, act in final_activations.items()
        }
