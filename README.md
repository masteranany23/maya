# MAYA — Modular Human-Like Virtual Companion

MAYA is an experimental, research-grounded virtual companion designed around explicit cognitive, affective, memory, persona, and relationship modules.

## Core idea

Instead of asking one LLM prompt to "act human", MAYA maintains structured state around the LLM:

`Input → Understanding → Memory Retrieval → Affect/Relationship Update → Response Planning → Generation → Validation → Memory Write`

The design is influenced by Generative Agents, CoALA, MemGPT, MemoryBank, LoCoMo, and affect-aware dialogue research.

## First milestone

A text-only vertical slice that can:

- receive a user message;
- maintain a stable persona;
- infer lightweight conversational affect signals;
- retrieve relevant long-term memories;
- generate a response through a provider interface;
- validate the response;
- write an auditable memory candidate;
- expose a testable application API.

## Start

1. Copy `.env.example` to `.env`.
2. Create a Python 3.11+ virtual environment.
3. Install `pip install -e '.[dev]'`.
4. Run `uvicorn maya.api:app --reload` once `src/maya/api.py` is implemented.

Use the Antigravity workflow `/maya-next` to continue implementation phase-by-phase.
