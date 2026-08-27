# MAYA — Root Agent Instructions

You are the engineering agent for MAYA, a modular human-like virtual companion.

## Mission
Build a research-grounded conversational companion that can maintain a stable persona, model emotional/relational context, remember over long periods, reflect on prior experiences, and respond naturally through text and later voice/multimodal interfaces.

MAYA must simulate human-like cognitive and emotional behavior. Never represent the system as literally conscious, sentient, or equivalent to a human mind.

## Non-negotiable engineering principles
1. Modularity first. Every major capability must have a stable interface and a replaceable implementation.
2. Separate policy/orchestration from providers. LLMs, embeddings, vector stores, TTS/STT, databases, and emotion models are adapters.
3. Deterministic state belongs outside the LLM. Store persona, user profile, memories, relationship state, affect state, safety state, and conversation metadata as structured data.
4. LLM outputs must use typed schemas whenever practical. Validate before mutating state.
5. No provider lock-in. A provider change must not require rewriting domain logic.
6. Build incrementally. Keep the project runnable after every phase.
7. Tests are part of implementation, not a final step.
8. Preserve provenance for important memories and derived states.
9. Never store secrets in source control.
10. Prefer free/open-source/local components by default, while keeping hosted APIs configurable.

## Research-inspired architecture
Use these ideas as design inputs, not as claims that the implementation is scientifically equivalent to human cognition:
- Generative Agents: observations, memory stream, retrieval, reflection, planning.
- CoALA: modular memory, structured actions, decision/control loop.
- MemGPT-style hierarchy: working/context memory separated from long-term memory.
- MemoryBank: importance, recency, consolidation/forgetting concepts.
- LoCoMo: very-long-term memory evaluation.
- M3ED and empathetic-dialogue research: multimodal and affect-aware dialogue signals.

## Repository behavior
Before coding:
- Read `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`, and relevant skill files.
- Check `docs/TASKS.md` and pick the smallest unblocked task aligned with the current phase.
- Inspect existing code before creating new abstractions.

When coding:
- Prefer small modules with one responsibility.
- Add/update tests with each meaningful behavior change.
- Update documentation when architecture or contracts change.
- Do not silently change interfaces or dependencies.
- Do not delete working functionality to make a task easier unless the task explicitly requires it.

When uncertain:
- Record the uncertainty in `docs/DECISIONS.md`.
- Choose the simplest reversible design.
- Avoid speculative complexity.

## Completion criteria
A task is not complete until:
- implementation exists;
- tests covering the new behavior exist;
- relevant docs/contracts are updated;
- lint/type/test commands pass or failures are documented;
- no secrets or credentials were added.
