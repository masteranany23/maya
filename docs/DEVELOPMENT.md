# Development Guide

## Principles

Keep modules small. Prefer composition over inheritance. Use async at integration boundaries. Keep domain types independent of FastAPI and external SDKs.

## Environment

Python 3.11+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Checks

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

## Commit pattern

Use focused commits such as:

- `feat(memory): add episodic memory interface`
- `feat(emotion): add affect state model`
- `test(conversation): cover provider failure`
- `docs(architecture): clarify memory tiers`

## Safe changes

Avoid broad rewrites. Before replacing a component, preserve its interface and test the new implementation behind the same contract.
