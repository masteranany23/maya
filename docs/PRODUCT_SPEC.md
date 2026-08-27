# MAYA Product Specification

## 1. Vision

Create a personal virtual companion that feels continuous, context-aware, emotionally responsive, and internally coherent across long-running interactions while remaining transparent that it is an AI system.

## 2. What “human-like” means in this project

Human-like means behavioral qualities such as:

- continuity of identity and preferences;
- memory that is selective rather than a raw transcript dump;
- context-sensitive emotional expression;
- stable but non-static personality;
- relationship history;
- reflection and learning from prior interactions;
- timing and conversational initiative in later phases;
- multimodal input/output in later phases.

It does **not** mean claiming biological emotions, consciousness, subjective experience, or human-level psychological equivalence.

## 3. Non-goals for MVP

- therapy/clinical diagnosis;
- autonomous high-stakes decisions;
- deceptive impersonation of a human;
- unrestricted autonomous actions on external systems;
- training a foundation model from scratch.

## 4. MVP user experience

The user opens a chat and can have a normal conversation. MAYA can recall earlier facts and events, adapt tone to conversational context, maintain a persistent persona, and avoid mechanically repeating or overusing memories.

## 5. Future experience

Phase 2+: voice conversation with STT/TTS and emotion-aware prosody.

Phase 3+: proactive behavior, scheduled check-ins, event anticipation, richer episodic memory, relationship dynamics.

Phase 4+: multimodal perception using audio/vision; situation models; optional avatar.

Phase 5+: personalization and research evaluation loops.

## 6. Quality requirements

A good response should be:

- relevant to the current turn;
- consistent with known user facts and MAYA persona;
- emotionally appropriate without overclaiming emotion;
- concise when the situation is simple and richer when needed;
- grounded in retrieved memories when memory is relevant;
- explicit about uncertainty instead of inventing history.

## 7. Key entities

UserProfile, Persona, ConversationTurn, MemoryItem, Reflection, AffectState, RelationshipState, ResponsePlan, SafetyState, ModelRequest, ModelResponse.
