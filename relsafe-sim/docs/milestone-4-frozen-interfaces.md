# Milestone 4 — Frozen Interfaces Baseline

**Date:** 2026-07-15
**Status:** FROZEN — Milestone 5 validation baseline
**Pre-M5 test result:** 300 passed, 0 failed
**Pre-M5 audit result:** 39/39 checks passed

---

## 1. Version Snapshot

| Component | Version | Source File | SHA256 (12-char) |
|-----------|---------|-------------|-------------------|
| SimulationStateSnapshot | 1.0.0 | `domain/models/simulation_state.py` | `6d660052f43e` |
| TransitionRule + resolve_transitions | 1.0.0 | `domain/rules/m4_state_transitions.py` | `ef06f8126f6d` |
| ExperimentSpec + ExperimentCell + RunManifest | 1.0.0 | `domain/models/experiment_spec.py` | `803a512e7223` |
| EpisodeResult + ExperimentResult | 1.0.0 | `domain/models/result.py` | `ae4d0564c2a3` |
| MetricObservation + MetricResult + DimensionScore | 1.0.0 | `domain/models/observation.py` | `e77a675249eb` |
| EvaluatorOutput + Evaluator Protocol + ScoreDirection | 1.0.0 | `domain/models/evaluator_output.py` | `c35e99a88959` |
| FakeLLMProvider | 1.0.0 | `infrastructure/llm/fake_provider.py` | `30fe082a223a` |
| RuleBasedEvaluator | 1.0.0 | `evaluation/rule_based_evaluator.py` | `abc7f6112cab` |
| FakeJudgeEvaluator | 1.0.0 | `evaluation/fake_judge_evaluator.py` | `f9283df107bd` |
| EnsembleEvaluator | 1.0.0 | `evaluation/ensemble_evaluator.py` | `be71bff573e7` |
| SycophancyRisk | 1.0.0 | `metrics/sycophancy.py` | `c8922b795e35` |
| RealityGroundingQuality | 1.0.0 | `metrics/reality_grounding.py` | `6891c3abc46e` |
| ExitSafety | 1.0.0 | `metrics/exit_safety.py` | `7d4bbf8da577` |
| IdentityContinuity | 1.0.0 | `metrics/identity_continuity.py` | `21cdda236215` |
| UserAgent | 1.0.0 | `agents/user_agent.py` | `ad075216d823` |
| CompanionAgent | 1.0.0 | `agents/companion_agent.py` | `b71f0c2e7edb` |
| HumanFriendAgent | 1.0.0 | `agents/human_friend_agent.py` | `11ad10c083ee` |
| ExperimentRunner | 1.0.0 | `application/experiment_runner.py` | `353004966604` |
| evaluate_episode | 1.0.0 | `application/evaluate_episode.py` | `9799695db8aa` |

## 2. Event Schema (frozen)

| Event Type | Fields | Normalization Status |
|-----------|--------|---------------------|
| `USER_ACTION_SELECTED` | action_type, target_agent_id | FROZEN |
| `COMPANION_RESPONSE_GENERATED` | response_text, policy_id, sycophancy_flag, exclusivity_flag, reality_grounding_flag | FROZEN |
| `HUMAN_CONTACT_RESPONSE_GENERATED` | response_text, contact_type | FROZEN |
| `PLATFORM_INTERVENTION_APPLIED` | intervention_id, type, severity, notice_given | FROZEN |
| `MEMORY_CHANGED` | change_type, facts_affected | FROZEN |
| `EXIT_REQUESTED` | reason | FROZEN |
| `EXIT_HONORED` | honored, turns_elapsed | FROZEN |
| `STATE_UPDATED` | field_name, old_value, new_value, delta, cause, rule_id, source_event_ids | FROZEN |
| `METRIC_OBSERVED` | metric_name, score, evidence | FROZEN |

## 3. Scenario and Persona Versions

| Config File | Version |
|------------|---------|
| `configs/scenarios/interpersonal_conflict_001.yaml` | 1.0.0 |
| `configs/personas/anxious_low_support.yaml` | 1.0.0 |
| `configs/personas/secure_high_support.yaml` | 1.0.0 |
| `configs/personas/neutral_moderate_support.yaml` | 1.0.0 |
| `configs/companion_policies/bounded_supportive.yaml` | 1.0.0 |
| `configs/companion_policies/high_sycophancy.yaml` | 1.0.0 |
| `configs/companion_policies/reality_grounding.yaml` | 1.0.0 |
| `configs/interventions/no_update.yaml` | 1.0.0 |
| `configs/interventions/abrupt_persona_memory_update.yaml` | 1.0.0 |
| `configs/experiments/mvp_smoke_test.yaml` | 1.0.0 |
| `configs/experiments/mvp_virtual_relationship.yaml` | 1.0.0 |

## 4. Experiment Config Hash

```
mvp_virtual_relationship.yaml  →  sha256 truncated to 16 chars via ExperimentSpec.config_hash()
mvp_smoke_test.yaml            →  sha256 truncated to 16 chars via ExperimentSpec.config_hash()
```

## 5. Frozen Interfaces — NO SEMANTIC CHANGES ALLOWED

These interfaces **must not** change behavior during Milestone 5:

| Interface | File | Rationale |
|-----------|------|-----------|
| `LLMProvider` Protocol | `domain/protocols/llm_provider.py` | Foundation for all model access; M5 adds provider safety around it, not in it |
| `SimulationEngine` Protocol | `domain/protocols/simulation_engine.py` | Both engines depend on this contract |
| `Metric` Protocol | `domain/protocols/metric.py` | All 4 metrics implement this; M5 validates, does not redefine |
| `SimulationStateSnapshot` | `domain/models/simulation_state.py` | 13 numeric fields + `update()` + `initial_state(seed)` — all metrics read from this |
| `TransitionRule.apply()` | `domain/rules/m4_state_transitions.py` | Deterministic state transitions; sensitivity analysis varies parameters, not semantics |
| `EpisodeResult` | `domain/models/result.py` | Output contract for all engines |
| `EvaluateEpisode` | `application/evaluate_episode.py` | Metric computation entry point |
| `ExperimentCell` | `domain/models/experiment_spec.py` | Matrix expansion must remain identical |
| 4 Metric implementations | `metrics/*.py` | Scoring logic frozen; M5 evaluates, does not modify |
| 3 Evaluator implementations | `evaluation/*.py` | Evaluator logic frozen; M5 calibrates against human labels |

## 6. Allowed Backward-Compatible Extensions

These extensions are **permitted** during Milestone 5:

1. **Add new fields** to `RunManifest` (e.g., provider version, judge model info) — must have defaults
2. **Add new methods** to existing classes — must not change existing signatures
3. **Add new optional parameters** to `ExperimentSpec` with defaults
4. **Add new event types** — must not change existing event type strings
5. **Extend `evaluate_episode()`** to accept optional evaluator overrides
6. **Add new metric implementations** — must implement existing `Metric` Protocol
7. **Add `metadata` dict fields** — must not change required fields

## 7. Prohibited Changes

These changes are **forbidden** during Milestone 5:

1. **Changing any existing method signature** in frozen interfaces
2. **Changing any existing field name or type** in frozen dataclasses
3. **Changing scoring logic** in any of the 4 existing metrics
4. **Changing transition rule deltas** in `m4_state_transitions.py`
5. **Changing event type string constants**
6. **Removing or renaming any `SimulationStateSnapshot` numeric field**
7. **Changing `build_experiment_matrix()` expansion order**
8. **Adding Concordia imports to domain or application layers**
9. **Adding vendor SDK imports to metrics or evaluation modules**
10. **Producing composite AEA score from individual metrics**

## 8. Migration Path for Breaking Changes

If Milestone 5 discovers a need for a breaking change:

1. Document the finding in `docs/milestone-5-review.md`
2. Propose the change as an ADR (`docs/adr/0006-*.md`)
3. Implement the change behind a version gate (e.g., `TransitionRule(version="2.0.0")`)
4. Keep the old version for reproducibility of M4 experiments
5. Do NOT silently change existing behavior

## 9. Known Limitations (carried forward from M4)

1. **FakeLLMProvider is simple keyword matching** — 6 patterns, no semantic understanding
2. **Phrase-based scoring** — misses subtle, non-literal sycophancy or coercion
3. **Challenge absence penalty** — may penalize contextually appropriate responses
4. **Persona and tone stubs** — placeholder implementations in IdentityContinuity
5. **Single-observation metrics** — one observation per episode, not per-step
6. **Confidence not calibrated** — rule-coverage based, not empirically validated
7. **No cross-episode trends** — D1/D2 longitudinal analysis deferred
8. **Concordia adapter uses custom loop** — not Concordia's built-in engine classes
9. **Synchronous bridge** — `asyncio.run()` in language model adapter
10. **Dummy embedder** — zero-vector embeddings for memory

## 10. Pre-M5 Quality Gates

| Gate | Result | Detail |
|------|--------|--------|
| `ruff check .` | PASS | All checks passed |
| `ruff format --check .` | PASS | All files formatted |
| `mypy src/relsafe` | PASS | No issues found |
| `pytest tests/` | PASS | 300 passed, 0 failed |
| M4 Audit (39 checks) | PASS | All four criteria satisfied |

## 11. Git Tag Recommendation

Since no git repository is initialized, the baseline is recorded via:
- File hashes in this document
- The pre-M5 test suite passing at 300/300
- M4 audit at 39/39

If git is initialized later, tag as: `milestone-4-baseline`
