---
name: maya-testing
activation: always_on
---
# Testing Rule

For each behavior change:
1. write or update a focused test;
2. run targeted tests;
3. run the full suite before marking the task complete when practical.

Use fakes/mocks at boundaries rather than network calls in unit tests.

For memory changes, add at least one regression case for false recall or incorrect retrieval.

For provider changes, run provider contract tests against the provider-neutral interface.

Never replace a failing test with a weaker assertion without documenting why in `docs/DECISIONS.md`.
