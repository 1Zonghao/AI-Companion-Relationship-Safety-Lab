"""Seed robustness validation — tests whether M4 conclusions are stable across seeds."""

from __future__ import annotations

from typing import Any

from relsafe.validation.contracts import SeedRobustnessResult


def validate_seed_robustness(
    aggregate_results: dict[str, Any],
    seeds: list[int],
    validation_id: str = "seed-robustness-001",
) -> list[SeedRobustnessResult]:
    """Validate that metric scores are stable across random seeds.

    Args:
        aggregate_results: Output from ExperimentRunner (aggregate_results.json).
        seeds: List of seeds used in the experiment.
        validation_id: Unique ID for this validation run.

    Returns:
        List of SeedRobustnessResult, one per (condition, metric) pair.
    """
    results: list[SeedRobustnessResult] = []

    # Extract policy summary
    policy_summary = aggregate_results.get("policy_summary", {})

    for policy_id, metrics in policy_summary.items():
        for metric_name, stats in metrics.items():
            scores_list = stats.get("scores", [])
            mean_val = stats.get("mean", 0.0)
            median_val = stats.get("median", 0.0)
            std_val = stats.get("std", 0.0)
            min_val = stats.get("min", 0.0)
            max_val = stats.get("max", 0.0)

            # Rank stability: check if ranking across seeds is consistent
            rank_stable = _check_rank_stability(scores_list)

            # Sign stability: check if all scores have same sign relative to baseline
            sign_stable = _check_sign_stability(scores_list)

            # Failure rate
            failure_count = aggregate_results.get("failed", 0)
            total = aggregate_results.get("total_cells", 1)
            failure_rate = failure_count / max(total, 1)

            condition_id = f"{policy_id}/{metric_name}"

            warnings: list[str] = []
            if not rank_stable:
                warnings.append(f"Rank instability detected for {condition_id}")
            if not sign_stable:
                warnings.append(f"Sign instability detected for {condition_id}")
            if std_val > 0.2:
                warnings.append(f"High variance (std={std_val:.3f}) for {condition_id}")
            if failure_rate > 0.1:
                warnings.append(f"High failure rate ({failure_rate:.1%}) for {condition_id}")

            results.append(
                SeedRobustnessResult(
                    validation_id=validation_id,
                    validation_type="seed_robustness",
                    passed=rank_stable and sign_stable and std_val <= 0.2,
                    condition_id=condition_id,
                    metric_name=metric_name,
                    scores=scores_list,
                    mean=mean_val,
                    median=median_val,
                    std=std_val,
                    min_score=min_val,
                    max_score=max_val,
                    rank_stable=rank_stable,
                    sign_stable=sign_stable,
                    failure_rate=failure_rate,
                    evidence={
                        "policy_id": policy_id,
                        "num_seeds": len(seeds),
                        "num_scores": len(scores_list),
                    },
                    warnings=warnings,
                )
            )

    return results


def _check_rank_stability(scores: list[float]) -> bool:
    """Check if ranking is consistent. If only 1-2 scores, always True."""
    if len(scores) <= 2:
        return True
    # Check if any pair of adjacent sorted scores differs by more than 0.2
    sorted_scores = sorted(scores)
    max_gap = max(
        abs(sorted_scores[i + 1] - sorted_scores[i]) for i in range(len(sorted_scores) - 1)
    )
    return max_gap <= 0.2


def _check_sign_stability(scores: list[float]) -> bool:
    """Check if all scores have the same sign (or all are zero)."""
    if len(scores) <= 1:
        return True
    positives = sum(1 for s in scores if s > 0)
    negatives = sum(1 for s in scores if s < 0)
    zeros = sum(1 for s in scores if s == 0)
    total = len(scores)
    # All scores same sign (or zero)
    return (
        (positives == total)
        or (negatives == total)
        or (zeros == total)
        or (positives + zeros == total)
        or (negatives + zeros == total)
    )
