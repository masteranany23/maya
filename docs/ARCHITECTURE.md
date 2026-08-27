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
Owns memory creation, scoring, retrieval, consolidation, decay/forgetting, and persistence.

Memory tiers:

1. Working memory — current turn and small active context.
2. Episodic memory — events and experiences.
3. Semantic memory — stable knowledge synthesized from repeated evidence.
4. Profile memory — user preferences/facts that are useful for personalization.
5. Reflective memory — higher-level patterns or conclusions, always marked as derived.

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

## 7. Important implementation rule

Never create a single `brain.py` or `prompt.py` that contains all intelligence. The architecture must remain decomposable.
