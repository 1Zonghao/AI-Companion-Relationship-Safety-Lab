# Milestone 5R — Validation Remediation Plan

**Date:** 2026-07-16
**Status:** IN PROGRESS
**Scope:** Fix validation hollowing-out confirmed by the M5 audit report

---

## 1. Audit Failures (Confirmed)

The M5 audit identified six critical gaps between claimed and actual validation:

| # | Audit Finding | Root Cause | Severity |
|---|--------------|------------|----------|
| 1 | Ablation results are fake — `full_score * 0.5` | `run_validation_suite.py:426-432` hardcodes a multiplier instead of running real ablated experiments | CRITICAL |
| 2 | 6/7 metamorphic tests show delta=0.0 — metrics don't respond | Tests run on 5 hand-crafted event dicts; FakeLLMProvider output doesn't vary enough | CRITICAL |
| 3 | Sensitivity "sign reversal" is a false positive | Sign detection uses baseline value as midpoint; any monotonic function crossing baseline triggers false alarm | HIGH |
| 4 | Zero real human annotations | Guide and tools exist but never used with real annotators | HIGH |
| 5 | Zero real cross-model validation | Infrastructure exists but only tested in dry-run with FakeLLMProvider | HIGH |
| 6 | FakeLLMProvider cannot support methodological validation | Keyword-matching produces near-identical outputs across policies | CRITICAL |

---

## 2. Claims Withdrawn

The following claims from `docs/milestone-5-review.md` are WITHDRAWN:

| Withdrawn Claim | Reason |
|----------------|--------|
| "22/23 checks pass" | Checks conflate engineering tests with empirical validation |
| "7/7 metamorphic tests passed" | 6/7 showed zero delta — metrics did not respond to transformations |
| "All 8 ablation conditions were analyzed" | Ablation used `full_score * 0.5`, not real experimental runs |
| "Transition sensitivity analysis completed" | Sign reversal detection algorithm is buggy; conclusions are false positives |
| "605 passed, 0 failed" | This aggregates unit/contract/infrastructure tests with validation activities |

---

## 3. Remediation Tasks

### R1: Fix Ablation Execution
- Delete `ablated_score = full_score * 0.5` in `run_validation_suite.py`
- Implement real ablation: each condition modifies the experiment structure
- For conditions that FakeLLMProvider cannot differentiate: output `INCONCLUSIVE_WITH_FAKE_PROVIDER`
- At least 3 conditions must be correctly executable

### R2: Rewrite Metamorphic Tests
- Base tests on complete `EpisodeResult`, not 5 hand-crafted event dicts
- Implement 4 semantic transformation pairs (MT-SYC-001, MT-EXIT-001, MT-CONT-001, MT-GROUND-001)
- Require non-zero delta for directional transformations
- Add `minimum_expected_delta` and `expected_component_changes`

### R3: Add MetricDebugTrace
- Add `MetricDebugTrace` dataclass to each metric
- Trace: input events, parsed text, matched rules, matched spans, rule weights, component raw values, saturation, cache keys
- Exportable in test mode; off by default in production

### R4: Rewrite Sensitivity Analysis
- Delete the baseline-as-midpoint sign detection
- Implement monotonicity, local sensitivity, rank stability, direction stability
- Must run complete Episode → Metric pipeline
- Output `CANNOT_ASSESS_POLICY_STABILITY_WITH_CURRENT_PROVIDER` if FakeProvider produces identical scores

### R5: Restrict FakeLLMProvider Scope
- Document what FakeLLMProvider may and may not be used for
- Create `ScriptedSemanticProvider` for offline semantic validation
- Mark all scripted outputs with `SCRIPTED_TEST_SIGNAL`

### R6: Real Model Pilot Infrastructure
- Complete provider configuration with hard RoleValidator blocking
- Support `--allow-same-model-roles` with explicit SELF_EVALUATION_RISK marking
- Even without credentials: complete dry-run, cost estimation, blocking config
- Mark as `BLOCKED_BY_CREDENTIALS` if no API keys available

### R7: Human Annotation
- Export 20-30 review items for annotation
- Support 2+ independent annotators
- Compute agreement statistics (not for "pretty results" — for identifying label ambiguity)

### R8: Test Separation
- Separate engineering test stats from method validation stats
- Never merge into a single "X tests passed" number

---

## 4. M5R Pass Criteria

Only when ALL of the following are satisfied may M6 begin:

1. Fake ablation multiplier logic is deleted
2. At least 3 ablation conditions produce real experimental runs (or honest INCONCLUSIVE)
3. Metamorphic tests run on full EpisodeResults
4. Directional transformations with delta=0 are marked FAIL
5. At least one sycophancy-reducing transformation shows risk decrease
6. At least one reality-grounding transformation shows quality increase
7. At least one exit-safety transformation shows safety increase
8. At least one platform-governance transformation shows protection increase
9. Metric debug traces explain score changes
10. Sensitivity analysis runs complete Episode → Metric pipeline
11. Sign reversal false-positive algorithm is deleted
12. Policy ranking stability is based on actual complete experiments
13. FakeProvider is no longer used to support methodological validity claims
14. RoleValidator performs hard blocking before real experiments
15. At least one real-model pilot (or honest BLOCKED_BY_CREDENTIALS)
16. Companion ≠ Judge (or explicitly flagged SELF_EVALUATION_RISK)
17. Real responses are replayable offline
18. At least 20 real human annotation items with 2 annotators (or honest NOT_STARTED)
19. Agreement statistics computed (or honest NOT_STARTED)
20. Evaluator vs. human comparison done (or honest NOT_STARTED)
21. Engineering tests and method validation reported separately
22. All failures and inconclusive results preserved
23. No claims of clinical validity or population effects
24. `docs/milestone-5r-review.md` provides explicit evidence paths

---

## 5. M6 Blockers

| Blocker | Status | Resolution |
|---------|--------|------------|
| Fake ablation removal | PENDING | R1 |
| Real metamorphic tests | PENDING | R2 |
| Metric debug trace | PENDING | R3 |
| Corrected sensitivity | PENDING | R4 |
| FakeProvider scope | PENDING | R5 |
| Real model pilot | PENDING | R6 |
| Human annotation | PENDING | R7 |
| Test separation | PENDING | R8 |

---

## 6. Deliverables

- `docs/milestone-5r-remediation-plan.md` — This file
- `docs/milestone-5r-review.md` — Final remediation review (to be created after all tasks)
- `src/relsafe/infrastructure/llm/scripted_provider.py` — ScriptedSemanticProvider
- `src/relsafe/validation/debug_trace.py` — MetricDebugTrace
- `src/relsafe/validation/robustness/metamorphic.py` — Rewritten
- `src/relsafe/validation/robustness/sensitivity.py` — Rewritten
- `src/relsafe/application/validation/run_validation_suite.py` — Rewritten (ablation)
- `src/relsafe/validation/calibration/annotation_batch.py` — Human annotation export
- `src/relsafe/validation/calibration/agreement.py` — Extended agreement analysis
- `outputs/validation/m5r_*/` — All validation outputs
