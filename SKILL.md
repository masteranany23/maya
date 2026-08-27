---
name: llm-gateway
---
# LLM Gateway Skill

Use a provider-neutral `LLMProvider` protocol.

A provider request should include:
- system/persona instructions;
- structured state/context;
- retrieved memories with provenance;
- current user input;
- requested output schema.

A provider adapter converts between the domain request and SDK/API specifics.

Do not leak provider response objects into application/domain code.

Handle timeout, rate-limit, malformed-output and unavailable-provider failures explicitly.
