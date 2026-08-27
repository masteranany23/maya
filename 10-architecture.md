---
name: maya-architecture
activation: model_decision
---
# Architecture Rule

Use dependency inversion:
- domain/core code contains protocols and models;
- infrastructure implements protocols;
- API/UI depends on application services;
- provider SDKs never define domain interfaces.

Prefer Strategy/Adapter patterns for LLM, memory storage, retrieval, affect analysis, STT and TTS.

Keep orchestration explicit and observable. A single turn should have traceable stages and typed intermediate objects.

Do not introduce a database, vector store, framework, queue, or agent framework unless the current task requires it and the dependency can be isolated behind an interface.
