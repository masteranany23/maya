---
name: maya-next
description: Continue MAYA by implementing the next unblocked task with tests and docs.
---
Read:
- AGENTS.md
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md
- docs/ROADMAP.md
- docs/TASKS.md
- docs/DECISIONS.md

Then:
1. Identify the next unblocked task in the current phase.
2. Inspect the relevant code and tests.
3. Write an implementation plan in the agent response before editing.
4. Implement the smallest coherent change.
5. Add/update tests.
6. Run lint/type/tests relevant to the change.
7. Update TASKS.md and any architecture docs/ADR needed.
8. Summarize files changed, tests run, and remaining risks.

Do not jump ahead to later phases unless the current task is blocked.
