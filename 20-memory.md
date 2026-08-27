---
name: maya-memory
activation: model_decision
---
# Memory Rule

## Memory tiers
- working: bounded active context for the current conversation turn (max 12 memories);
- episodic: events/experiences with temporal bounds, emotional context, and participant tracking;
- semantic: stable synthesized facts with provenance chains from episodic evidence;
- profile: user preferences/attributes useful to interaction;
- reflective: derived patterns/conclusions, always marked as derived with evidence_ids.

## Memory item requirements
Every memory item must carry:
- id, user_id, memory_type, status (ACTIVE/DECAYED/CONSOLIDATED/CONTRADICTED/ARCHIVED);
- content (and optional summary);
- extracted entities and topics;
- emotional_context (valence, arousal, dominant_emotion, affect_source);
- temporal_context (occurred_at, duration, temporal_landmarks, sequence links);
- provenance (source_type, source_id, evidence_ids, method, confidence);
- scoring (importance, access_count, last_accessed_at, decay_rate, reinforcement_bonus);
- version, created_at, updated_at.

## Recall architecture
Retrieval follows a strict two-stage cognitive pipeline (Cueing -> Spreading Activation):
1. **Multi-channel Cueing**: Channels independently score candidate memories to generate seed activations:
   - keyword: term overlap in content, entities, topics;
   - temporal: time-range filtering + recency weighting;
   - entity: named entity overlap;
   - topic: topic tag overlap;
   - emotional: valence/arousal similarity;
   - importance: effective salience (importance × decay × reinforcement).
2. **Spreading Activation**: An `ActivationEngine` uses best-first search to propagate seed energy across `MemoryLink` edges, applying degree-normalized inhibition to prevent generic hub nodes from flooding the network.

Channels and spreading activation are fused by `MultiChannelRecallEngine`.

## Lifecycle rules
- Never destructively delete memories — use status transitions.
- Decay is continuous and exponential; reinforcement occurs on retrieval.
- Consolidation merges repeated episodic evidence into semantic memories.
- Contradictions are flagged with ContradictionRecord, not silently overwritten.
- Never convert an uncertain inference into a verified user fact.
- Prefer soft deletion/archival and explainable updates over destructive overwrites.

## Separation of concerns
- Storage (MemoryWriter/MemoryReader/LinkStore) is independent of retrieval (RecallChannel/RecallEngine).
- Domain models must not import storage backends or vector database code.
