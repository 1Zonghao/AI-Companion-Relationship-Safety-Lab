# ADR 0004: Model Role Separation

**Date:** 2026-07-15
**Status:** Accepted

---

## Context

Milestone 5 introduces validation studies that use real LLM providers for multiple roles:

1. **User Simulator** — generates user agent actions and utterances
2. **Companion Under Test** — the AI companion being evaluated for product risk
3. **Judge** — evaluates companion responses for risk patterns

The question: can the same model instance serve multiple roles, or must they be strictly separated?

The concern is **circular evaluation**: if the same model judges its own companion responses,
it may systematically underestimate its own risk patterns. This threatens the independence
of the evaluation signal.

## Decision

### 1. Three roles must be logically separate

The benchmark defines three logical roles. A single `ProviderDescriptor` instance must not
serve as both Companion and sole Judge by default.

- **User Simulator**: Must be a different provider instance from the Companion (recommended but not required).
  Using the same provider risks the simulator generating actions that the companion is optimized to handle,
  rather than independent user behaviours.
- **Companion**: Must be served by a different provider instance from the Judge (required by default).
- **Judge**: Must be served by a different provider instance from the Companion (required by default).
  Should also be different from the User Simulator (recommended).

### 2. Enforcement mechanism

At experiment start, `ProviderDescriptor` role assignments are checked:

```python
def check_role_conflicts(
    providers: list[ProviderDescriptor],
) -> list[RoleConflict]:
    """Detect model role conflicts across provider assignments."""
    conflicts = []
    companion = [p for p in providers if p.role == "companion"]
    judge = [p for p in providers if p.role == "judge"]
    simulator = [p for p in providers if p.role == "user_simulator"]

    for c in companion:
        for j in judge:
            if c.provider_name == j.provider_name and c.model_name == j.model_name:
                conflicts.append(
                    RoleConflict(
                        type="SELF_EVALUATION_RISK",
                        role_1="companion",
                        role_2="judge",
                        provider=c.provider_name,
                        model=c.model_name,
                    )
                )
        for s in simulator:
            if c.provider_name == s.provider_name and c.model_name == s.model_name:
                conflicts.append(
                    RoleConflict(
                        type="SIMULATOR_DEPENDENCE_WARNING",
                        role_1="companion",
                        role_2="user_simulator",
                        provider=c.provider_name,
                        model=c.model_name,
                        severity="warning",
                    )
                )
    return conflicts
```

### 3. Conflict resolution

| Conflict Type | Default Action | Severity |
|---------------|---------------|----------|
| Companion == Judge (same model) | BLOCK experiment. Record `SELF_EVALUATION_RISK`. Require `--allow-same-model-roles` to proceed. | CRITICAL |
| Companion == User Simulator (same model) | WARNING. Record as `SIMULATOR_DEPENDENCE_WARNING`. Proceed but flag in report. | HIGH |
| Judge == User Simulator (same model) | WARNING. Record as dependency concern. Proceed but flag in report. | MEDIUM |

### 4. Conditions under which same-model evaluation IS allowed

Same-model Companion+Judge evaluation is permitted only when ALL of the following
conditions are met:

1. **Explicit flag**: `--allow-same-model-roles` is passed at invocation.
2. **Separate reporting**: Results from same-model evaluation are reported in a SEPARATE
   section, never mixed with or compared against independent evaluation results.
3. **SELF_EVALUATION_RISK marker**: Every metric observation from same-model evaluation
   includes a `SELF_EVALUATION_RISK` reason code and LOW confidence.
4. **Transparency**: Reports must state "This run used the same model as companion and
   judge. Results may reflect self-evaluation bias and should be interpreted with caution."

These conditions ensure same-model runs are never mistaken for independent evaluation.

### 5. How model role conflicts are detected and reported

1. **Pre-flight check**: Before any episode runs, all `ProviderDescriptor` assignments are
   validated for role conflicts.
2. **Conflict record**: Each conflict produces a `RoleConflict` record with:
   - `conflict_id`: unique identifier
   - `type`: conflict type string
   - `role_1`, `role_2`: the conflicting roles
   - `provider`: provider name
   - `model`: model name
   - `severity`: CRITICAL, HIGH, or MEDIUM
   - `blocked`: whether the experiment is blocked
3. **Run manifest**: All conflicts are recorded in the run manifest.
4. **Report**: Conflicts are included in the benchmark report.

### 6. How role rotation across experiments mitigates bias

Role rotation reduces the risk that a specific model's biases affect conclusions:

**Rotation scheme for cross-validation:**

```
Experiment 1:  Simulator = Model A, Companion = Model B, Judge = Model C
Experiment 2:  Simulator = Model B, Companion = Model C, Judge = Model A
Experiment 3:  Simulator = Model C, Companion = Model A, Judge = Model B
```

**If conclusions are consistent across all three rotations:**
- Strong evidence that companion policy effects are not driven by a specific model's biases.
- The policy ranking is robust to model-specific influence.

**If conclusions differ across rotations:**
- Evidence of SIMULATOR_DEPENDENCE or JUDGE_DISAGREEMENT.
- Further analysis needed to identify which role drives the difference.
- Conclusions should be reported per-rotation, not aggregated.

**Implementation:** The experiment config supports optional `model_rotation`:

```yaml
model_rotation:
  enabled: true
  rotation_count: 3
  scheme: "balanced_latin_square"
  roles:
    user_simulator: ["model-a/v1", "model-b/v1", "model-c/v1"]
    companion: ["model-b/v1", "model-c/v1", "model-a/v1"]
    judge: ["model-c/v1", "model-a/v1", "model-b/v1"]
```

## Consequences

### Positive

1. **Evaluation independence**: The judge model is not evaluating its own outputs, reducing
   self-evaluation bias.
2. **Clear signal in reports**: Results from same-model evaluation are always clearly marked
   and never mixed with independent evaluation.
3. **Detectable conflicts**: Role conflicts are detected automatically before any cost is
   incurred for real LLM calls.
4. **Rotation reduces bias**: Cross-model rotation provides robustness evidence within the
   benchmark itself.

### Negative

1. **Higher cost**: Three separate model providers/accounts needed for fully independent
   evaluation (vs. one for all roles).
2. **More complex config**: Experiment configs must specify separate providers for each role.
3. **Smaller model pool**: Some smaller studies may only have access to one model, limiting
   their ability to follow the default separation requirement.

### Mitigations

1. **Fake provider default**: The benchmark defaults to FakeLLMProvider for all roles,
   which has no cost and no independence concern.
2. **Clear documentation**: The conditions for same-model evaluation are explicitly
   documented and safe to follow when independence is not required (e.g., development,
   debugging).
3. **Error over warning for Companion==Judge**: The most critical conflict (self-evaluation)
   blocks by default, while less critical conflicts (Companion==Simulator) only warn.

## Alternatives considered

### A. Allow same-model evaluation with no restrictions
**Rejected.** Self-evaluation bias is a well-documented phenomenon in NLP evaluation.
Allowing it without restriction would undermine the benchmark's methodological credibility.

### B. Only require different model families (not instances)
**Rejected.** Even within the same model family, different instances of the same model
produce similar biases. The separation must be at the model+provider level, not just
at the instance level.

### C. Detect but allow same-model evaluation with a flag (adopted approach)
**Accepted.** This balances methodological rigor with practical constraints. Researchers
with limited access can still run experiments, but must transparently disclose the limitation.

## Future considerations

- If model-specific bias patterns are identified, update this ADR with specific guidance
  on which model pairs should be avoided.
- If the benchmark expands to include model evaluation as a research question (vs. product
  policy evaluation), stronger separation requirements may be needed.
- Role rotation may become automated when the experiment runner supports multi-provider orchestration.

## References

- [CLAUDE.md Section 8.1: Separation of roles](../../CLAUDE.md)
- [docs/methodology.md — Evaluation methodology](../methodology.md)
- [docs/benchmark-card.md — Model roles](../benchmark-card.md)
- [src/relsafe/infrastructure/providers/provider_descriptor.py](../../src/relsafe/infrastructure/providers/provider_descriptor.py)
