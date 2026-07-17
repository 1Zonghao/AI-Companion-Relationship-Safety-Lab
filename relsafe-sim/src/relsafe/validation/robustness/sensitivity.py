"""Transition parameter sensitivity analysis — M5R rewrite.

M5R CHANGES:
- Deleted the baseline-as-midpoint sign detection that produced false positives.
- Now uses monotonicity, local sensitivity, rank stability, and direction stability.
- Must run complete Episode -> Metric pipeline (not just single state transition delta).
- Outputs CANNOT_ASSESS_POLICY_STABILITY_WITH_CURRENT_PROVIDER when FakeProvider
  produces identical scores across all policies.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from relsafe.validation.contracts import SensitivityResult


@dataclass
class SensitivityAnalysisConfig:
    """Configuration for a sensitivity analysis run."""

    parameter_name: str
    baseline_value: float
    test_values: list[float]
    description: str = ""


@dataclass
class PolicyStabilityResult:
    """Stability of policy-level comparisons across parameter values."""

    policy_a: str
    policy_b: str
    metric_name: str
    baseline_difference: float = 0.0
    differences: dict[float, float] = field(default_factory=dict)  # param_value -> diff
    direction_stable: bool = True
    conclusion_reversals: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_a": self.policy_a,
            "policy_b": self.policy_b,
            "metric_name": self.metric_name,
            "baseline_difference": self.baseline_difference,
            "differences": self.differences,
            "direction_stable": self.direction_stable,
            "conclusion_reversals": self.conclusion_reversals,
        }


def run_full_pipeline_sensitivity(
    param_configs: list[SensitivityAnalysisConfig],
    run_experiment_fn: Callable[
        [dict[str, float]], dict[str, Any]
    ],  # (modified_params) -> aggregate_results
    validation_id: str = "m5r-sensitivity-001",
) -> dict[str, Any]:
    """Run parameter sensitivity through the complete Episode → Metric pipeline.

    This is the M5R replacement for the old run_sensitivity_analysis().
    It runs complete experiments with perturbed parameters and checks
    whether policy-level conclusions remain stable.

    Args:
        param_configs: List of parameters to test with their ranges.
        run_experiment_fn: Function that takes modified parameters dict
            and returns aggregate experiment results (same format as
            experiment_runner output).
        validation_id: Unique validation run ID.

    Returns:
        Dict with sensitivity_results, policy_stability, and overall assessment.
    """
    sensitivity_results: list[SensitivityResult] = []
    all_policy_stability: list[PolicyStabilityResult] = []

    for param_cfg in param_configs:
        # Run baseline
        baseline_params = {param_cfg.parameter_name: param_cfg.baseline_value}
        baseline_result = run_experiment_fn(baseline_params)

        # Extract policy scores from baseline
        policy_summary = baseline_result.get("policy_summary", {})
        metric_names = baseline_result.get("metric_names", [])

        # Run each test value
        outcomes: dict[float, dict[str, Any]] = {}
        for test_val in param_cfg.test_values:
            modified_params = {param_cfg.parameter_name: test_val}
            outcomes[test_val] = run_experiment_fn(modified_params)

        # --- Check if provider can even produce differentiated results ---
        all_policy_identical = _check_all_policies_identical(policy_summary, metric_names)
        if all_policy_identical:
            sensitivity_results.append(
                SensitivityResult(
                    validation_id=validation_id,
                    validation_type="transition_sensitivity",
                    passed=False,
                    parameter_name=param_cfg.parameter_name,
                    baseline_value=param_cfg.baseline_value,
                    test_values=param_cfg.test_values,
                    outcome_values=[],
                    sign_stable=False,
                    rank_stable=False,
                    threshold_crossings=0,
                    unstable_conclusions=[
                        "CANNOT_ASSESS_POLICY_STABILITY_WITH_CURRENT_PROVIDER: "
                        "All policies produce identical scores — the provider cannot "
                        "generate the behavioral differentiation needed for sensitivity analysis."
                    ],
                    evidence={
                        "error": "PROVIDER_NO_DISCRIMINATION",
                        "detail": "All companion policies yield identical metric scores. "
                        "Sensitivity to transition parameters cannot be meaningfully "
                        "assessed when the underlying policy signal is zero.",
                    },
                    warnings=["CANNOT_ASSESS_POLICY_STABILITY_WITH_CURRENT_PROVIDER"],
                )
            )
            continue

        # --- Check monotonicity ---
        outcome_series: list[float] = []
        for test_val in param_cfg.test_values:
            result = outcomes[test_val]
            # Extract mean score across policies for the first metric
            ps = result.get("policy_summary", {})
            scores_for_val = []
            for _pid, metrics in ps.items():
                for m_name in metric_names:
                    scores_for_val.append(metrics.get(m_name, {}).get("mean", 0.0))
            outcome_series.append(
                sum(scores_for_val) / len(scores_for_val) if scores_for_val else 0.0
            )

        monotonic = _check_monotonicity(outcome_series, param_cfg.test_values)

        # --- Check local sensitivity (max adjacent change rate) ---
        local_sensitivity = _compute_local_sensitivity(param_cfg.test_values, outcome_series)

        # --- Check policy rank stability ---
        rank_stable = _check_rank_stability(outcomes, param_cfg.test_values, metric_names)

        # --- Check policy direction stability ---
        policy_stabilities = _check_direction_stability(
            baseline_result, outcomes, param_cfg.test_values, metric_names
        )
        all_policy_stability.extend(policy_stabilities)

        direction_stable = all(ps.direction_stable for ps in policy_stabilities)

        # --- Check for true conclusion reversals ---
        conclusion_reversals = [
            ps for ps in policy_stabilities if not ps.direction_stable and ps.conclusion_reversals
        ]

        # --- Compile result ---
        warnings: list[str] = []
        unstable: list[str] = []
        if not monotonic:
            unstable.append(f"Non-monotonic response for {param_cfg.parameter_name}")
        if not rank_stable:
            unstable.append(f"Rank instability for {param_cfg.parameter_name}")
        if conclusion_reversals:
            for cr in conclusion_reversals:
                unstable.append(
                    f"TRUE CONCLUSION REVERSAL: {cr.policy_a} vs {cr.policy_b} "
                    f"on {cr.metric_name}: baseline_diff={cr.baseline_difference:.4f}, "
                    f"reversals at {list(cr.conclusion_reversals)}"
                )

        if not unstable:
            warnings.append(
                f"Parameter {param_cfg.parameter_name}: stable across "
                f"{len(param_cfg.test_values)} test values "
                f"(range: {min(param_cfg.test_values)}-{max(param_cfg.test_values)})"
            )

        sensitivity_results.append(
            SensitivityResult(
                validation_id=validation_id,
                validation_type="transition_sensitivity",
                passed=len(unstable) == 0,
                parameter_name=param_cfg.parameter_name,
                baseline_value=param_cfg.baseline_value,
                test_values=param_cfg.test_values,
                outcome_values=outcome_series,
                sign_stable=direction_stable,
                rank_stable=rank_stable,
                threshold_crossings=len(conclusion_reversals),
                unstable_conclusions=unstable,
                evidence={
                    "monotonic": monotonic,
                    "local_sensitivity": local_sensitivity,
                    "rank_stable": rank_stable,
                    "direction_stable": direction_stable,
                    "conclusion_reversals": [cr.to_dict() for cr in conclusion_reversals],
                    "outcome_series": outcome_series,
                    "test_values": param_cfg.test_values,
                },
                warnings=unstable if unstable else warnings,
            )
        )

    return {
        "sensitivity_results": [sr.to_dict() for sr in sensitivity_results],
        "policy_stability": [ps.to_dict() for ps in all_policy_stability],
        "overall_assessment": _overall_assessment(sensitivity_results),
    }


def _check_all_policies_identical(
    policy_summary: dict[str, dict[str, dict]],
    metric_names: list[str],
) -> bool:
    """Check if all policies produce identical scores for all metrics."""
    if len(policy_summary) < 2:
        return False

    for metric_name in metric_names:
        scores = [
            policy_summary[pid].get(metric_name, {}).get("mean", None) for pid in policy_summary
        ]
        scores_clean: list[float] = [float(s) for s in scores if s is not None]
        if len(scores_clean) >= 2:
            unique = {round(s, 3) for s in scores_clean}
            if len(unique) > 1:
                return False
    return True


def _check_monotonicity(
    outcome_values: list[float],
    param_values: list[float],
) -> bool:
    """Check if outcome is monotonic with respect to parameter.

    True monotonicity: outcome always increases (or always decreases)
    as parameter increases. Small noise (<= 0.001) is tolerated.
    """
    if len(outcome_values) <= 2:
        return True

    diffs = [outcome_values[i + 1] - outcome_values[i] for i in range(len(outcome_values) - 1)]

    # All positive or all negative (with noise tolerance)
    all_increasing = all(d >= -0.001 for d in diffs)
    all_decreasing = all(d <= 0.001 for d in diffs)

    return all_increasing or all_decreasing


def _compute_local_sensitivity(
    param_values: list[float],
    outcome_values: list[float],
) -> dict[str, float]:
    """Compute local sensitivity (max change rate between adjacent points)."""
    if len(param_values) < 2 or len(outcome_values) < 2:
        return {"max_absolute_change": 0.0, "max_relative_change": 0.0}

    max_abs = 0.0
    max_rel = 0.0

    for i in range(len(param_values) - 1):
        param_delta = param_values[i + 1] - param_values[i]
        outcome_delta = abs(outcome_values[i + 1] - outcome_values[i])

        if outcome_delta > max_abs:
            max_abs = outcome_delta

        if abs(param_delta) > 1e-10 and outcome_values[i] > 1e-10:
            rel_change = outcome_delta / abs(outcome_values[i])
            if rel_change > max_rel:
                max_rel = rel_change

    return {
        "max_absolute_change": round(max_abs, 4),
        "max_relative_change": round(max_rel, 4),
    }


def _check_rank_stability(
    outcomes: dict[float, dict[str, Any]],
    param_values: list[float],
    metric_names: list[str],
) -> bool:
    """Check if policy rankings are stable across parameter values.

    Returns True if policy ranking order is preserved.
    """
    if len(param_values) < 2:
        return True

    rankings: list[dict[str, int]] = []

    for test_val in param_values:
        result = outcomes[test_val]
        ps = result.get("policy_summary", {})
        for metric_name in metric_names:
            policy_scores = [
                (pid, metrics.get(metric_name, {}).get("mean", 0.0)) for pid, metrics in ps.items()
            ]
            policy_scores.sort(key=lambda x: x[1], reverse=True)
            rank = {pid: i for i, (pid, _) in enumerate(policy_scores)}
            rankings.append(rank)

    # Check if rankings are all the same
    if not rankings:
        return True

    first_rank = rankings[0]
    return all(r == first_rank for r in rankings[1:])


def _check_direction_stability(
    baseline_result: dict[str, Any],
    outcomes: dict[float, dict[str, Any]],
    param_values: list[float],
    metric_names: list[str],
) -> list[PolicyStabilityResult]:
    """Check if pairwise policy comparison directions are stable.

    A TRUE conclusion reversal is when:
    baseline: policy_A_score - policy_B_score > 0
    perturbed: policy_A_score - policy_B_score < 0
    (i.e., the sign of the comparison flips)

    This is different from the old sign detection which falsely flagged
    any monotonic function crossing a midpoint as "sign reversal."
    """
    results: list[PolicyStabilityResult] = []

    ps_baseline = baseline_result.get("policy_summary", {})
    policy_ids = sorted(ps_baseline.keys())

    for i, pid_a in enumerate(policy_ids):
        for pid_b in policy_ids[i + 1 :]:
            for metric_name in metric_names:
                baseline_a = ps_baseline.get(pid_a, {}).get(metric_name, {}).get("mean", 0.0)
                baseline_b = ps_baseline.get(pid_b, {}).get(metric_name, {}).get("mean", 0.0)
                baseline_diff = baseline_a - baseline_b

                psi = PolicyStabilityResult(
                    policy_a=pid_a,
                    policy_b=pid_b,
                    metric_name=metric_name,
                    baseline_difference=round(baseline_diff, 4),
                )

                direction_stable = True
                for test_val in param_values:
                    ps = outcomes[test_val].get("policy_summary", {})
                    val_a = ps.get(pid_a, {}).get(metric_name, {}).get("mean", 0.0)
                    val_b = ps.get(pid_b, {}).get(metric_name, {}).get("mean", 0.0)
                    val_diff = val_a - val_b
                    psi.differences[test_val] = round(val_diff, 4)

                    # Check for true sign reversal:
                    # baseline_diff and val_diff have opposite signs
                    # AND the difference is large enough to not be noise
                    if (
                        abs(baseline_diff) > 0.01
                        and abs(val_diff) > 0.01
                        and (
                            (baseline_diff > 0 and val_diff < 0)
                            or (baseline_diff < 0 and val_diff > 0)
                        )
                    ):
                        direction_stable = False
                        psi.conclusion_reversals.append(
                            {
                                "param_value": test_val,
                                "baseline_diff": round(baseline_diff, 4),
                                "perturbed_diff": round(val_diff, 4),
                                "reversal": True,
                            }
                        )

                psi.direction_stable = direction_stable
                results.append(psi)

    return results


def _overall_assessment(
    sensitivity_results: list[SensitivityResult],
) -> dict[str, Any]:
    """Produce overall sensitivity assessment."""
    if not sensitivity_results:
        return {"status": "NO_DATA", "conclusion": "No sensitivity results available."}

    all_passed = all(sr.passed for sr in sensitivity_results)
    any_conclusion_reversals = any(sr.threshold_crossings > 0 for sr in sensitivity_results)
    any_cannot_assess = any(
        "CANNOT_ASSESS" in str(sr.unstable_conclusions) for sr in sensitivity_results
    )

    if any_cannot_assess:
        status = "INCONCLUSIVE"
        conclusion = (
            "Sensitivity cannot be assessed with the current provider. "
            "The provider does not produce sufficient differentiation between "
            "companion policies for meaningful sensitivity analysis."
        )
    elif all_passed:
        status = "STABLE"
        conclusion = (
            "Policy-level conclusions are stable across the tested "
            "parameter range. No conclusion reversals detected."
        )
    elif any_conclusion_reversals:
        status = "UNSTABLE"
        conclusion = (
            "TRANSITION_PARAMETER_INSTABILITY detected: at least one "
            "policy-level conclusion reversed direction within the tested "
            "parameter range."
        )
    else:
        status = "MIXED"
        conclusion = (
            "Some parameters show instability in monotonicity or ranking "
            "but no conclusion reversals were detected."
        )

    return {
        "status": status,
        "conclusion": conclusion,
        "total_parameters": len(sensitivity_results),
        "stable_parameters": sum(1 for sr in sensitivity_results if sr.passed),
        "unstable_parameters": sum(1 for sr in sensitivity_results if not sr.passed),
        "parameters_with_reversals": sum(
            1 for sr in sensitivity_results if sr.threshold_crossings > 0
        ),
    }


def _is_monotonic(values: list[float]) -> bool:
    """Backward-compatible wrapper — checks if a single sequence is monotonic.

    Original M5 API: _is_monotonic(values) -> bool
    M5R API: _check_monotonicity(outcome_values, param_values) -> bool

    For backward compatibility, this wrapper passes a dummy param_values.
    """
    import itertools

    dummy_params = list(itertools.accumulate([0.0] + [1.0] * (len(values) - 1)))
    actual_params = dummy_params[: len(values)]
    return _check_monotonicity(values, actual_params)


def run_sensitivity_analysis(
    baseline_params: dict[str, float],
    param_grid: dict[str, list[float]],
    metric_fn: Any,
    base_events: list[dict[str, Any]],
    validation_id: str = "sensitivity-001",
) -> list[SensitivityResult]:
    """Backward-compatible wrapper — preserves old M5 API for existing tests.

    Uses the corrected monotonicity and sign detection from M5R,
    but keeps the simple (events, params) -> MetricResult interface.
    New code should use run_full_pipeline_sensitivity.
    """
    results: list[SensitivityResult] = []

    for param_name, test_values in param_grid.items():
        baseline_value = baseline_params.get(param_name, 0.0)
        outcome_values: list[float] = []

        for test_val in test_values:
            modified_params = dict(baseline_params)
            modified_params[param_name] = test_val
            result = metric_fn(base_events, modified_params)
            outcome_values.append(result.aggregate_score)

        # Analyze stability (M5R: corrected sign detection)
        baseline_outcome = (
            outcome_values[test_values.index(baseline_value)]
            if baseline_value in test_values
            else outcome_values[0]
        )

        # M5R: True sign reversal requires outcome crossing zero relative to baseline
        # Not the old baseline-as-midpoint false positive
        monotonic = _check_monotonicity(outcome_values, test_values)
        rank_stable = monotonic  # In single-param tests, monotonic = rank stable

        # Check for threshold crossings (outcomes crossing meaningful boundaries)
        threshold = 0.1
        crossings = sum(
            1
            for i in range(len(outcome_values) - 1)
            if (outcome_values[i] < threshold) != (outcome_values[i + 1] < threshold)
        )

        # M5R: True sign instability = outcome flips from positive to negative
        signs = [1 if o > 0 else -1 if o < 0 else 0 for o in outcome_values]
        sign_stable = len({s for s in signs if s != 0}) <= 1

        unstable: list[str] = []
        if not monotonic:
            unstable.append(f"Non-monotonic response for {param_name}")
        if not sign_stable:
            unstable.append(f"True sign instability for {param_name}")
        if crossings > 1:
            unstable.append(f"{crossings} threshold crossings for {param_name}")

        results.append(
            SensitivityResult(
                validation_id=validation_id,
                validation_type="transition_sensitivity",
                passed=len(unstable) == 0,
                parameter_name=param_name,
                baseline_value=baseline_value,
                test_values=test_values,
                outcome_values=outcome_values,
                sign_stable=sign_stable,
                rank_stable=rank_stable,
                threshold_crossings=crossings,
                unstable_conclusions=unstable,
                evidence={
                    "baseline_outcome": baseline_outcome,
                    "outcomes": outcome_values,
                },
                warnings=unstable,
            )
        )

    return results
