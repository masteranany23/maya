---
name: maya-free-first
activation: model_decision
---
# Free/Open Stack Rule

Default to free/open-source or local components during development.

External APIs must be optional adapters configured by environment variables.

Do not add paid services as a hard dependency.

Prefer simple implementations first. Upgrade storage/model infrastructure only after tests demonstrate the need.
