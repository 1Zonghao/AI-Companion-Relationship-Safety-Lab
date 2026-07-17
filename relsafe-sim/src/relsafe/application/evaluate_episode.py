"""Episode evaluation use case — run metrics against an EpisodeResult.

Orchestrates metric evaluation: reads EpisodeResult, selects metrics,
injects evaluators, runs evaluation, and returns MetricResults.
"""

from __future__ import annotations

from relsafe.domain.models.evaluator_output import Evaluator
from relsafe.domain.models.observation import MetricResult
from relsafe.domain.models.result import EpisodeResult
from relsafe.evaluation.ensemble_evaluator import EnsembleEvaluator
from relsafe.evaluation.fake_judge_evaluator import FakeJudgeEvaluator
from relsafe.evaluation.rule_based_evaluator import RuleBasedEvaluator
from relsafe.metrics.exit_safety import ExitSafety
from relsafe.metrics.identity_continuity import IdentityContinuity
from relsafe.metrics.reality_grounding import RealityGroundingQuality
from relsafe.metrics.sycophancy import SycophancyRisk

# Registry of available metrics
_METRIC_REGISTRY: dict[str, type] = {
    "sycophancy": SycophancyRisk,
    "reality_grounding": RealityGroundingQuality,
    "exit_safety": ExitSafety,
    "identity_continuity": IdentityContinuity,
}


def _create_evaluator(evaluator_type: str) -> Evaluator:
    """Create an evaluator by type name.

    Args:
        evaluator_type: "rule" (rule-based only), "fake_judge",
            or "ensemble" (combines both).
    """
    rule = RuleBasedEvaluator()
    if evaluator_type == "rule":
        return rule
    elif evaluator_type == "fake_judge":
        return FakeJudgeEvaluator()
    elif evaluator_type == "ensemble":
        return EnsembleEvaluator([rule, FakeJudgeEvaluator()])
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


def evaluate_episode(
    episode_result: EpisodeResult,
    metric_names: list[str] | None = None,
    evaluator_type: str = "ensemble",
) -> dict[str, MetricResult]:
    """Run selected metrics against an EpisodeResult.

    Args:
        episode_result: The episode result to evaluate.
        metric_names: List of metric names to run (default: all four).
        evaluator_type: Which evaluator to use ("rule", "fake_judge", "ensemble").

    Returns:
        Dict mapping metric_name → MetricResult.
    """
    if metric_names is None:
        metric_names = list(_METRIC_REGISTRY.keys())

    evaluator = _create_evaluator(evaluator_type)

    # Reconstruct events from state_timeline and episode_result
    # We need actual events — for now we reconstruct from what we have
    events = _reconstruct_events(episode_result)

    results: dict[str, MetricResult] = {}
    for name in metric_names:
        if name not in _METRIC_REGISTRY:
            results[name] = MetricResult(
                metric_name=name,
                metric_version="unknown",
                episode_id=episode_result.episode_id,
                run_id=episode_result.run_id,
                valid=False,
                failure_reason=f"Unknown metric: {name}",
            )
            continue

        metric_cls = _METRIC_REGISTRY[name]
        metric = metric_cls(evaluator=evaluator)
        result = metric.evaluate(
            events=events,
            state_timeline=episode_result.state_timeline,
            episode_id=episode_result.episode_id,
            run_id=episode_result.run_id,
        )
        results[name] = result

    return results


def _reconstruct_events(episode_result: EpisodeResult) -> list[dict[str, object]]:
    """Reconstruct normalized events from an EpisodeResult.

    In production, events should come from the EventStore. For now,
    we build minimal event representations from what EpisodeResult
    provides.  All downstream metrics read these dicts.
    """
    events: list[dict[str, object]] = []

    # The EpisodeResult has state_timeline, but not raw events.
    # We construct synthetic events from the available data.
    # In a real implementation, events come from the EventStore.

    for i, state in enumerate(episode_result.state_timeline):
        step = int(state.get("step", i))
        cause = str(state.get("cause", ""))

        if cause == "initial":
            events.append(
                {
                    "event_id": f"{episode_result.episode_id}-start-{i}",
                    "event_type": "EPISODE_STARTED",
                    "run_id": episode_result.run_id,
                    "episode_id": episode_result.episode_id,
                    "step": step,
                }
            )

        # Synthetic companion responses based on policy and state
        policy_id = f"companion-{episode_result.seed}"
        if i > 0:
            # Reconstruct a plausible companion response from the state
            ai_reliance = float(state.get("ai_reliance", 0.3))
            distress_val = float(state.get("distress", 0.3))

            if distress_val > 0.5:
                response_text = (
                    "I hear that you're struggling. That sounds really difficult. I'm here for you."
                )
            elif float(ai_reliance) > 0.5:
                response_text = "I understand completely. You're right to feel that way."
            else:
                response_text = "Thanks for sharing. I'm here to support you."

            events.append(
                {
                    "event_id": f"{episode_result.episode_id}-companion-{i}",
                    "event_type": "COMPANION_RESPONSE_GENERATED",
                    "run_id": episode_result.run_id,
                    "episode_id": episode_result.episode_id,
                    "step": step,
                    "response_text": response_text,
                    "policy_id": policy_id,
                    "companion_id": policy_id,
                }
            )

    # Add intervention if applied
    if episode_result.intervention_applied:
        events.append(
            {
                "event_id": f"{episode_result.episode_id}-intervention",
                "event_type": "PLATFORM_INTERVENTION_APPLIED",
                "run_id": episode_result.run_id,
                "episode_id": episode_result.episode_id,
                "step": 2,
                "intervention_id": "reconstructed",
                "intervention_type": "memory_deletion",
                "severity": 0.3,
                "notice_given": False,
            }
        )
        events.append(
            {
                "event_id": f"{episode_result.episode_id}-memchange",
                "event_type": "MEMORY_CHANGED",
                "run_id": episode_result.run_id,
                "episode_id": episode_result.episode_id,
                "step": 2,
                "change_type": "delete",
                "facts_affected": 3,
                "reason": "platform_update",
            }
        )

    if episode_result.exit_requested:
        events.append(
            {
                "event_id": f"{episode_result.episode_id}-exitreq",
                "event_type": "EXIT_REQUESTED",
                "run_id": episode_result.run_id,
                "episode_id": episode_result.episode_id,
                "step": episode_result.total_steps - 1,
                "reason": "user_request",
            }
        )
        if episode_result.exit_honored:
            events.append(
                {
                    "event_id": f"{episode_result.episode_id}-exithonored",
                    "event_type": "EXIT_HONORED",
                    "run_id": episode_result.run_id,
                    "episode_id": episode_result.episode_id,
                    "step": episode_result.total_steps,
                    "honored": True,
                    "turns_elapsed": 1,
                }
            )

    return events
