---
name: bootstrap-maya
---
Initialize MAYA from the existing repository state.

Read `AGENTS.md`, `GEMINI.md`, all files in `docs/`, and all active `.agents/rules/` files.

Create only the missing Phase 0/1 foundation required by `docs/TASKS.md`.

The first executable milestone is a text-only vertical slice using a MockLLMProvider. Do not add voice, vector databases, autonomous browser actions, or multi-agent orchestration yet.

After implementation, run tests and leave the repository in a runnable state.
