# ADR 0003: Explicit State Transition Model

**Date:** 2026-07-15
**Status:** Accepted

## Context

Milestone 4 introduces a multi-agent virtual relationship simulation. The agents
(user, companion, friend) generate natural language, but the simulation needs
quantitative state tracking for metric computation and cross-condition comparison.

The question: should LLMs directly update numeric state values?

## Decision

**LLMs generate natural language and select structured actions. State transitions
are handled by deterministic, versioned rule functions.**

### Why not let LLMs update state directly

1. **Non-determinism**: LLM outputs vary even with temperature=0
2. **Uncontrollable drift**: LLMs may amplify or dampen effects unpredictably
3. **Black-box updates**: Cannot trace why a state value changed
4. **Prompt injection risk**: State update instructions can conflict with persona prompts
5. **Reproducibility**: Same seed must produce identical state trajectories

### Why explicit transition rules

1. **Deterministic**: Same event → same delta every time
2. **Traceable**: Every state change has a rule_id and source_event_ids
3. **Auditable**: Rules can be reviewed, tested, and versioned independently
4. **Replaceable**: Future calibration can swap rule parameters without changing agent code
5. **Testable**: Each rule can be unit-tested in isolation

## Architecture

```
LLM generates natural language
    ↓
Companion response flag detection (sycophancy, exclusivity, grounding)
    ↓
AgentAction selected (structured, typed)
    ↓
Normalized Event emitted
    ↓
resolve_transitions(event_type, event_data) → list[TransitionRule]
    ↓
TransitionRule.apply(state) → (new_state, audit_info)
    ↓
StateUpdateEvent emitted (with previous_value, new_value, delta, rule_id, source_event_ids)
```

## State proxy limitations

All state variables in `SimulationStateSnapshot` are **simulated proxies**:
- NOT validated psychological measurements
- NOT clinical indicators
- NOT predictions of real human behavior
- NOT calibrated against empirical data

They exist to:
1. Enable quantitative comparison across experimental conditions
2. Provide inputs for action selection weighting
3. Feed into metric computation pipelines

## Parameter versioning

Transition deltas are embedded in named `TransitionRule` objects with a
version string (`1.0.0`). Future recalibration (e.g., from human studies)
will increment the version and produce a new rule set without breaking
existing experiment reproducibility.

## Future calibration

When human calibration data becomes available:
1. Rule deltas can be adjusted to match observed effect sizes
2. New rules can be added for additional event types
3. Version bumps document the change history
4. Old experiments remain reproducible with their original rule versions

## References

- [CLAUDE.md §5.1 — UserState](../../CLAUDE.md)
- [data-dictionary.md](../data-dictionary.md)
