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
