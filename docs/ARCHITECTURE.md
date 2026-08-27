# MAYA Architecture

## 1. Architectural principle

The LLM is a reasoning/generation component inside a larger cognitive loop, not the entire system.

## 2. Logical pipeline

```text
                 ┌─────────────────────┐
                 │    User / Client    │
                 └──────────┬──────────┘
                            │
                     Input Adapter
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Conversation Engine │
                 └──────────┬──────────┘
                            │
           ┌────────────────┼─────────────────┐
           ▼                ▼                 ▼
     Understanding     Memory System     Affect System
           │                │                 │
           └────────────────┼─────────────────┘
                            ▼
                     Relationship
                         State
                            │
                            ▼
                      Planner / Policy
                            │
                            ▼
                       LLM Gateway
                            │
                            ▼
                    Response Validator
                            │
                            ▼
                       Output Adapter
                            │
                            ▼
                      User / Client
                            │
                            ▼
                     Memory Write Queue
                            │
             ┌──────────────┴───────────────┐
             ▼                              ▼
      Episodic Memory                 Reflection Engine
             │                              │
             └──────────────┬───────────────┘
                            ▼
                    Semantic / Profile
                         Memory
```

## 3. Modules

### `core`
Stable domain types, interfaces, dependency injection, clocks, IDs, errors.

### `conversation`
Orchestrates a single turn. It must not know how a specific model vendor works.

### `memory`
Owns memory creation, scoring, multi-channel retrieval, lifecycle management, consolidation, decay/forgetting, and persistence.

Memory tiers:

1. Working memory — bounded active context for the current conversation turn.
2. Episodic memory — events and experiences with temporal bounds, emotional context, and participant tracking.
3. Semantic memory — stable knowledge synthesized from repeated episodic evidence, with provenance chains.
4. Profile memory — user preferences/facts useful for personalization.
5. Reflective memory — higher-level patterns or conclusions derived from episodic/semantic memories, always marked as derived.

Retrieval architecture follows a strict 5-stage cognitive pipeline:

1. **Candidate Generation**: Fetching eligible memories from storage.
2. **Cueing (Seed Activation)**: Channels (keyword, temporal, entity, topic, emotional) independently score candidates to generate initial seed activations. (Vector retrieval is one possible channel here).
3. **Spreading Activation**: An `ActivationEngine` propagates seed energy across the `MemoryLink` graph using best-first search, penalized by degree-normalized inhibition to prevent hubs from flooding the network.
4. **Ranking**: Memories are scored based on the maximum of their seed score and propagated activation.
5. **Reconstruction**: Selected memories are loaded into working memory with an `ActivationTrace` explaining their retrieval path.

Memory lifecycle:

Memories transition through states: ACTIVE → DECAYED / CONSOLIDATED / CONTRADICTED / ARCHIVED. Decay is continuous and time-based. Reinforcement occurs on retrieval. Consolidation merges repeated episodic evidence into semantic memories. Contradiction detection flags conflicting memories for resolution.

Association graph:

Memories are connected by typed, weighted links (temporal, causal, thematic, emotional, entity-based, contradiction, supersession, derivation). Associative retrieval walks this graph from anchor memories.

### `emotion`
Estimates conversational affect signals and maintains MAYA's affective response state. This is a computational state model, not a claim of subjective emotion.

### `persona`
Stable identity, values, speaking style, boundaries, preferences, and controlled adaptation rules.

### `llm`
Provider-neutral gateway. Initial implementations: MockProvider, then OpenRouter/Gemini/OpenAI-compatible adapters as configured.

### `audio`
Future STT/TTS interfaces. No audio dependency in the text MVP.

### `observability`
Tracing, turn IDs, latency, token usage, retrieval diagnostics, and evaluation logs without storing secrets.

## 4. Dependency direction

`api → conversation → domain interfaces`

Implementations point inward through interfaces. Domain modules must not import HTTP, vendor SDK, or vector-database code.

## 5. Event-oriented extension points

Future internal events:

- `UserMessageReceived`
- `AffectUpdated`
- `MemoriesRetrieved`
- `ResponseGenerated`
- `ResponseAccepted`
- `MemoryCandidateCreated`
- `ReflectionRequested`
- `MemoryDecayed`
- `MemoryReinforced`
- `MemoryConsolidated`
- `ContradictionDetected`
- `ReflectionCompleted`

## 6. Research mapping

| MAYA | Research inspiration |
|---|---|
| Memory stream + reflection | Generative Agents |
| Modular memory/action/control | CoALA |
| Working vs long-term context | MemGPT |
| Importance/recency/forgetting | MemoryBank |
| Long-term evaluation | LoCoMo |
| Multimodal affect signals | M3ED |
| Empathetic response generation | Emotional Support / empathetic dialogue research |
| Association graph + multi-channel recall | Human memory: spreading activation, context-dependent retrieval |

## 7. Important implementation rule

Never create a single `brain.py` or `prompt.py` that contains all intelligence. The architecture must remain decomposable.
