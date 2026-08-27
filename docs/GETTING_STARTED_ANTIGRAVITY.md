# Antigravity Setup for MAYA

Antigravity recognizes workspace rules under `.agents/rules/` and workflows under `.agents/workflows/`. It also supports codebase-level `AGENTS.md`/`GEMINI.md` instructions.

## First run

Open this folder as an Antigravity workspace.

Then run `/bootstrap-maya`.

After bootstrap, use `/maya-next` repeatedly. Keep the Agent Manager focused on one phase/task at a time rather than asking it to build all future features in one pass.

## Recommended agent workflow

1. Human defines/updates requirements in `docs/PRODUCT_SPEC.md`.
2. Architect updates contracts/ADRs where necessary.
3. Backend implements the smallest task.
4. Memory/Affect specialist handles their module when relevant.
5. QA adds regression/evaluation tests.
6. Release agent checks quality/security.

## Rules activation

Keep core and testing rules always-on. Use architecture, memory, affect and free-stack rules by model decision. Invoke a rule explicitly with its `@` mention when you need tighter focus.

## Context discipline

Do not paste the entire research corpus into every prompt. Keep durable knowledge in the repository and use `@` mentions for only the relevant files.
