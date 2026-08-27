# MAYA Workspace Context

Read `AGENTS.md` first. Then consult the relevant files under `docs/` and `.agents/` before implementation.

MAYA is a research-grounded, modular virtual companion project. The objective is to produce consistent human-like conversational behavior through explicit components for memory, affect, persona, relationship state, planning, and model/provider orchestration.

Use typed domain models and dependency inversion. Never make application logic depend directly on a specific LLM vendor.

Current bootstrap goal: build Phase 0/1 infrastructure and a text-only end-to-end conversational vertical slice before adding voice, vision, proactive behavior, or complex learning.
