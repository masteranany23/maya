# Architecture Decision Record Log

## ADR-0001 — Python backend for cognitive core
Status: Accepted

Reason: fast iteration, rich AI ecosystem, strong typing with Pydantic, straightforward API and evaluation tooling.

## ADR-0002 — Provider-neutral LLM gateway
Status: Accepted

Reason: preserve portability among Gemini, OpenRouter, and OpenAI-compatible/free models; keep domain logic independent from a vendor SDK.

## ADR-0003 — Structured state outside the LLM
Status: Accepted

Reason: persona, memories, affect, and relationship state require auditability and deterministic manipulation.

## ADR-0004 — Modular memory tiers
Status: Accepted

Reason: working, episodic, semantic, profile, and reflective memories serve different retrieval/update behaviors. Inspired by Generative Agents, CoALA, MemGPT, and MemoryBank.

## ADR-0005 — Text first, voice later
Status: Accepted

Reason: voice introduces streaming, latency, interruption, TTS/STT provider, and prosody complexity. Build the cognitive loop first so audio becomes an adapter.

## ADR-0006 — Multi-channel recall replaces single-method search
Status: Accepted

Reason: the original `MemoryStore.search()` used keyword overlap as the sole retrieval mechanism. The architecture promises scoring, ranking, and multiple memory tiers, which cannot be served by a single search method. We separate persistence (`MemoryWriter`/`MemoryReader`/`LinkStore`) from retrieval (`RecallChannel`/`RecallEngine`). Each recall channel implements one strategy (keyword, temporal, entity, topic, emotional, associative, importance). A `MultiChannelRecallEngine` fuses their results.

## ADR-0007 — Rich memory model with emotional/temporal/associative context
Status: Accepted

Reason: the flat `MemoryItem` text blob cannot support multi-dimensional retrieval. We extend it with `EmotionalContext`, `TemporalContext`, `ProvenanceRecord`, `ScoringState`, `MemoryStatus` lifecycle, extracted entities, topics, and an association graph via `MemoryLink`.

## ADR-0008 — Explicit memory lifecycle states
Status: Accepted

Reason: memories need lifecycle management. `MemoryStatus` enum (ACTIVE, DECAYED, CONSOLIDATED, CONTRADICTED, ARCHIVED) enables soft deletion, audit trails, and explicit state transitions. All queries default to ACTIVE. No destructive deletion.

## ADR-0009 — Storage-retrieval separation
Status: Accepted

Reason: coupling persistence and retrieval into one `MemoryStore` protocol prevents independent evolution. Storage backends (in-memory, SQLite, future Postgres) implement `MemoryWriter`/`MemoryReader`. Recall channels are composable strategies that operate on candidate lists, independent of storage format.

## ADR-0010 — No vector database until structured retrieval is proven
Status: Accepted

Reason: vector similarity search introduces infrastructure complexity and makes retrieval opaque. All initial recall channels use structured data (keyword, entity, topic, temporal, emotional, graph links). Vector embeddings will be added as an additional `RecallChannel` later, not as the sole retrieval mechanism.

## ADR-0011 — Multi-channel Cueing + Spreading Activation
Status: Accepted

Reason: Simple 1-hop associative recall is insufficient for complex memory traversal. We adopted a 5-stage pipeline (Candidate Generation -> Cueing -> Spreading Activation -> Ranking -> Reconstruction) inspired by HeLa-Mem and SYNAPSE. Cueing channels generate seed activations, which are propagated through the `MemoryLink` graph using best-first search. To prevent highly-connected generic memories from flooding the network (false memories), we apply degree-normalized inhibition.

## ADR-0012 — SQLite with JSON-encoded domains for Phase P2 Persistence
Status: Accepted

Reason: We needed a persistent database to advance beyond ephemeral testing. `sqlite3` (via `aiosqlite`) provides an embedded, transactional engine with zero operational overhead. Rather than creating highly normalized relational tables for complex domain contexts (ProvenanceRecord, TemporalContext, etc.), we map these sub-models directly to JSON strings within standard tables (`memory_items`, `memory_links`). This preserves the schema flexibility while enabling fast atomic writes.

## ADR-0013 — Non-destructive Contradiction Resolution
Status: Accepted

Reason: Memory consolidation and conflict detection inherently face contradictions (e.g. "I love dogs" vs "I hate dogs"). To preserve auditable cognitive history, we never destructively delete memories. The `ContradictionResolutionPolicy` assigns lifecycle transitions based on the contradiction type: temporal changes supersede the old memory, unsupported inferences archive the new memory, and genuine contradictions weaken both while flagging for user clarification.
