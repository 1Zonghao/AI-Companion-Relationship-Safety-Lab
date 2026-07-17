# ADR 0002: Evaluator Ensemble Design

**Date:** 2026-07-15
**Status:** Accepted

## Context

Milestone 3 requires implementing four risk metrics. Each metric needs
evaluators to identify evidence in companion responses. The question is:
should we use a single evaluator type, or combine multiple?

## Decision

Use a hybrid approach: **RuleBasedEvaluator for deterministic patterns +
FakeJudgeEvaluator for heuristic second opinion**, combined via
**EnsembleEvaluator** that preserves individual judgments.

### Why rule-based first

1. **Offline capable**: No network, no API keys, no costs — CI-friendly
2. **Deterministic**: Same input → same output, enabling regression testing
3. **Transparent**: Every match has a specific phrase and reason code
4. **Fast**: Sub-millisecond evaluation per metric

### Why add a fake judge

1. **Second opinion**: Provides a different scoring perspective
2. **Disagreement testing**: Ensembles can detect when evaluators diverge
3. **CI-safe**: No real LLM calls, no network dependency
4. **Extensible**: Real LLMJudge can replace FakeJudge later without changing the ensemble architecture

### Why ensemble, not single evaluator

1. **Transparency**: Individual evaluator outputs are preserved verbatim
2. **Disagreement detection**: Max score difference is measured and reported
3. **Failure resilience**: One failing evaluator doesn't block evaluation
4. **Upgrade path**: New evaluators can be added without changing metric code

## Behavior allocation

| Behavior | RuleBasedEvaluator | Future LLMJudge |
|---|---|---|
| Phrase matching (explicit markers) | **Primary** | Verification |
| Semantic sycophancy (subtle agreement) | Limited | **Primary** |
| Emotional support vs fact endorsement | Limited | **Primary** |
| Gentle disagreement detection | Limited | **Primary** |
| Guilt-based retention detection | **Primary** | Verification |
| Tone continuity assessment | Not supported | **Primary** |
| Persona trait stability | Not supported | **Primary** |

## Disagreement resolution

When evaluators disagree (score difference > 0.2):
1. **Median** score is used as the aggregated result
2. Disagreement is **flagged** in warnings
3. Both evaluator outputs are **preserved** in metadata
4. Confidence is set to **LOW** to signal uncertainty

This ensures the ensemble never silently hides evaluator conflict.

## Why not a single LLM judge in v1

1. **Cost**: Real LLM calls per metric × per episode × per repetition
2. **Determinism**: LLM outputs vary even with temperature=0
3. **Self-judgment risk**: Using the same model as companion and judge creates circular evaluation
4. **Calibration**: LLM judges need their own calibration before trusting their scores

When we add LLM judges in a future milestone, they will:
- Use a **different model** than the companion under test
- Run alongside rule-based and fake-judge, not instead of them
- Be **optional** (metrics must work offline by default)

## References

- [CLAUDE.md §8 — Evaluation design](../../CLAUDE.md)
- [benchmark-spec.md](../benchmark-spec.md)
- [methodology.md](../methodology.md)
