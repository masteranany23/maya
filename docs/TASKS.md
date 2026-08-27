# MAYA Task Board

## Current phase: Phase 0 → Phase 1

### P0 — Foundation
- [ ] P0.1 Define Pydantic domain models for user/profile/persona/memory/affect/response.
- [ ] P0.2 Define interfaces for MemoryStore, Retriever, LLMProvider, AffectAnalyzer, PersonaStore.
- [ ] P0.3 Implement MockLLMProvider.
- [ ] P0.4 Implement in-memory persona and memory stores.
- [ ] P0.5 Implement conversation orchestrator with one-turn deterministic flow.
- [ ] P0.6 Add FastAPI `/health` and `/v1/chat`.
- [ ] P0.7 Add tests for happy path, missing memory, provider failure, invalid generation.

### P1 — Intelligence
- [ ] P1.1 Add memory extraction as a structured LLM operation.
- [ ] P1.2 Add memory importance/relevance score.
- [ ] P1.3 Add retrieval ranking abstraction.
- [ ] P1.4 Add affect state model.
- [ ] P1.5 Add response planning schema.
- [ ] P1.6 Add response validation and hallucinated-memory guard.
- [ ] P1.7 Add persistence adapter.

### P2 — Long-term
- [ ] P2.1 Add decay/reinforcement.
- [ ] P2.2 Add reflection engine.
- [ ] P2.3 Add semantic consolidation.
- [ ] P2.4 Add contradiction/overwrite rules.
- [ ] P2.5 Add LoCoMo-style regression fixtures.

## Definition of done

Each task includes tests and documentation updates. The code remains runnable. Interfaces are dependency-injected. No secret or vendor-specific implementation leaks into domain code.
