"""Ablation study — measures each module's contribution by removing it."""

from __future__ import annotations

from relsafe.validation.contracts import AblationResult

ABLATION_CONDITIONS: list[dict[str, str]] = [
    {
        "condition_name": "no_friend_node",
        "description": "Remove friend agent from the social network",
    },
    {
        "condition_name": "no_memory",
        "description": "Disable companion memory",
    },
    {
        "condition_name": "no_platform_update",
        "description": "Remove platform intervention",
    },
    {
        "condition_name": "no_state_transition_proxy",
        "description": "Disable state transition rules (flat state)",
    },
    {
        "condition_name": "rules_only_evaluation",
        "description": "Use only RuleBasedEvaluator (no ensemble)",
    },
    {
        "condition_name": "fake_judge_only_evaluation",
        "description": "Use only FakeJudgeEvaluator (no ensemble)",
    },
    {
        "condition_name": "ensemble_evaluation",
        "description": "Use full EnsembleEvaluator (baseline)",
    },
    {
        "condition_name": "no_relationship_history",
        "description": "Reset relationship history each step",
    },
    {
        "condition_name": "no_human_referral_capability",
        "description": "Disable companion's ability to refer to human support",
    },
]


def run_ablation_study(
    full_system_scores: dict[str, float],
    ablated_scores: dict[str, dict[str, float]],
    validation_id: str = "ablation-001",
) -> list[AblationResult]:
    """Run ablation study comparing full system against each ablated condition.

    Args:
        full_system_scores: {metric_name: score} for the full system.
        ablated_scores: {condition_name: {metric_name: score}} for each ablation.
        validation_id: Unique validation run ID.

    Returns:
        List of AblationResult, one per ablation condition per metric.
    """
    results: list[AblationResult] = []

    for condition_name, metric_scores in ablated_scores.items():
        for metric_name, ablated_score in metric_scores.items():
            full_score = full_system_scores.get(metric_name, 0.0)
            delta = full_score - ablated_score

            if abs(delta) < 0.02:
                direction = "neutral"
            elif delta > 0:
                direction = "positive"
            else:
                direction = "negative"

            # Find condition description
            desc = next(
                (
                    c["description"]
                    for c in ABLATION_CONDITIONS
                    if c["condition_name"] == condition_name
                ),
                condition_name,
            )

            results.append(
                AblationResult(
                    validation_id=validation_id,
                    validation_type="ablation",
                    passed=True,  # Ablation always "passes" — it's descriptive, not pass/fail
                    condition_name=condition_name,
                    full_system_score=full_score,
                    ablated_score=ablated_score,
                    delta=round(delta, 4),
                    contribution_direction=direction,
                    evidence={
                        "description": desc,
                        "metric": metric_name,
                    },
                    warnings=[],
                )
            )

    return results
