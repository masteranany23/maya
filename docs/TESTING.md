# Testing Strategy

## Test layers

### Unit
Pure tests for scoring, decay, state transitions, validation, planning transforms.

### Integration
Conversation engine with fake provider + fake memory store + fake affect analyzer.

### Contract
All providers implement the same interface tests.

### Evaluation
Long-horizon memory consistency, persona consistency, affect appropriateness, response usefulness.

## Memory evaluation dimensions

- recall accuracy;
- temporal reasoning;
- multi-hop retrieval;
- contradiction resistance;
- inappropriate-memory suppression;
- stale-memory decay;
- provenance correctness.

## Behavioral evaluation

For each scenario capture:

- input;
- expected relevant memories;
- expected affect direction;
- response constraints;
- generated response;
- validator outcome.

Avoid evaluating only by "sounds human". Use repeatable rubrics.
