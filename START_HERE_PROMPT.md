# First Antigravity Prompt

Read `AGENTS.md`, `GEMINI.md`, `docs/GETTING_STARTED_ANTIGRAVITY.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/RESEARCH.md`, `docs/ROADMAP.md`, `docs/TASKS.md`, and the active `.agents/rules/` files.

You are not being asked to redesign MAYA. Continue the existing architecture.

## Objective
Implement the current Phase 0 → Phase 1 vertical slice from `docs/TASKS.md`.

## Required result
A runnable text-only MAYA backend with:
1. typed domain models;
2. provider-neutral LLM interface + MockLLMProvider;
3. in-memory persona/profile store;
4. in-memory episodic memory store;
5. basic affect analyzer behind an interface;
6. conversation engine using the sequence:
   input → persona/profile → affect → memory retrieval → response plan → generation → validation → memory write;
7. FastAPI `/health` and `/v1/chat`;
8. unit + integration tests.

## Important
- Keep each subsystem replaceable.
- Do not add voice, vector DB, external APIs, or autonomous actions yet.
- Do not put all logic in one file.
- Do not claim consciousness or literal emotion.
- Do not invent memories.
- Use deterministic tests with fake/mock providers.
- Preserve provenance on memories.

## Execution loop
1. Inspect the current tree; do not duplicate existing files.
2. State the implementation plan.
3. Implement the smallest coherent change.
4. Run tests/lint/type checks available in the environment.
5. Fix failures rather than skipping checks.
6. Update `docs/TASKS.md` and relevant docs.
7. End with a concise report of changed files, checks run, and remaining risks.
