---
name: maya-memory
activation: model_decision
---
# Memory Rule

Use memory tiers:
- working: immediate context;
- episodic: events/experiences;
- semantic: stable synthesized facts;
- profile: user preferences/attributes useful to interaction;
- reflective: derived patterns/conclusions.

Every memory item should carry at least:
- id;
- type;
- content;
- timestamp;
- source/provenance;
- confidence;
- importance;
- optional entities/tags.

Never convert an uncertain inference into a verified user fact.

Retrieval should optimize relevance, recency and importance while respecting privacy and scope.

Prefer soft deletion/archival and explainable updates over destructive overwrites.
