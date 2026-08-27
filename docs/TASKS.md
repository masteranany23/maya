# MAYA Task Board

## Current phase: Phase 1 — Memory Redesign

### P0 — Foundation (complete)
- [x] P0.1 Define Pydantic domain models for user/profile/persona/memory/affect/response.
- [x] P0.2 Define interfaces for MemoryStore, Retriever, LLMProvider, AffectAnalyzer, PersonaStore.
- [x] P0.3 Implement MockLLMProvider.
- [x] P0.4 Implement in-memory persona and memory stores.
- [x] P0.5 Implement conversation orchestrator with one-turn deterministic flow.
- [x] P0.6 Add FastAPI `/health` and `/v1/chat`.
- [x] P0.7 Add tests for happy path, missing memory, provider failure, invalid generation.

### P1-M — Memory Redesign (in progress)
- [x] P1-M.1 Rich memory domain models (MemoryItem, EmotionalContext, TemporalContext, ProvenanceRecord, ScoringState, MemoryLink, RecallCue, RecallResult, WorkingMemory, lifecycle result types).
- [x] P1-M.2 Memory protocols (MemoryWriter, MemoryReader, LinkStore, RecallChannel, RecallEngine, MemoryManager, ImportanceScorer, DecayFunction, ReflectionEngine, ConsolidationEngine, ContradictionDetector).
- [x] P1-M.3 In-memory storage adapters (InMemoryWriter, InMemoryReader, InMemoryLinkStore) with contract tests.
- [x] P1-M.4 Recall channels (Keyword, Temporal, Entity, Topic, Emotional, Associative, Importance).
- [x] P1-M.5 MultiChannelRecallEngine with fusion strategies (weighted-sum, rank-fusion, max-of).
- [x] P1-M.6 DefaultMemoryManager facade.
- [x] P1-M.7 Lifecycle operations (ExponentialDecay, StepDecay, HeuristicImportanceScorer, HeuristicContradictionDetector, SimpleConsolidationEngine, StubReflectionEngine).
- [x] P1-M.8 Evaluation fixtures (8 scenarios: recall, temporal, emotional, associative, decay, contradiction, consolidation, provenance).
- [x] P1-M.9 ADR-0006 through ADR-0010.
- [x] P1-M.10 Architecture doc updates.
- [x] P1-M.11 Refactor ConversationEngine to use new MemoryManager (integration).
- [x] P1-M.12 Working memory management in conversation flow.
- [x] P1-M.13 Deprecate old MemoryStore protocol.
- [x] P1-M.14 Multi-channel cueing + Spreading activation (ADR-0011).
- [x] P1-M.15 E2E Cognitive Integration and False-Memory Eval.

### P1 — Intelligence
- [x] P1.1 Add memory extraction as a structured LLM operation.
- [x] P1.2 Add memory importance/relevance score (using HeuristicImportanceScorer).
- [x] P1.3 Add retrieval ranking abstraction (done via RecallEngine).
- [ ] P1.4 Add affect state model.
- [ ] P1.5 Add response planning schema.
- [ ] P1.6 Add response validation and hallucinated-memory guard.
- [ ] P1.7 Add persistence adapter.

### P2 — Long-term
- [ ] P2.1 Add decay/reinforcement (decay functions implemented, sweep job pending).
- [x] P2.2 Add reflection engine (stub implemented, LLM-powered pending).
- [x] P2.3 Add semantic consolidation (simple engine implemented, LLM summarization pending).
- [x] P2.4 Add contradiction/overwrite rules (detector implemented, resolution policies pending).
- [x] P2.5 Add LoCoMo-style regression fixtures (8 evaluation fixtures implemented).

### P3 — Voice Integration
- [x] P3.1 Domain Models (ExpressiveSegment, SpeechPlan, TTSCapabilities, AudioChunk).
- [x] P3.2 Protocols (VADProvider, STTProvider, TTSProvider).
- [x] P3.3 Voice Core (SemanticBuffer, SpeechPlanner, VoiceSession).
- [x] P3.4 Conversation Engine streaming and interruption updates.
- [x] P3.5 Mock Providers (MockVAD, MockSTT, MockTTS).
- [x] P3.6 WebSocket API endpoint for streaming.
- [x] P3.7 Architecture Documentation (ADR-0014).
- [ ] P3.8 Tests & Voice Evaluations.

## Definition of done

Each task includes tests and documentation updates. The code remains runnable. Interfaces are dependency-injected. No secret or vendor-specific implementation leaks into domain code.
