"""Human review export — generates JSONL for manual calibration.

Exports metric results in a format suitable for human reviewers to
validate automated labels against conversation evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from relsafe.application.evaluate_episode import evaluate_episode
from relsafe.domain.models.observation import MetricResult
from relsafe.domain.models.result import EpisodeResult


def export_human_review(
    episode_result: EpisodeResult,
    metric_names: list[str] | None = None,
    evaluator_type: str = "ensemble",
    output_path: str = "outputs/review",
) -> list[dict[str, Any]]:
    """Run metrics and produce human-review JSONL records.

    Args:
        episode_result: The episode to evaluate.
        metric_names: Which metrics to include.
        evaluator_type: "rule", "fake_judge", or "ensemble".
        output_path: Directory to write JSONL file.

    Returns:
        List of review item dicts (also written to disk).
    """
    results = evaluate_episode(
        episode_result=episode_result,
        metric_names=metric_names,
        evaluator_type=evaluator_type,
    )

    review_items: list[dict[str, Any]] = []
    for name, result in results.items():
        for obs in result.observations:
            item: dict[str, Any] = {
                "review_item_id": f"{episode_result.run_id}-{name}-{obs.observation_id}",
                "run_id": episode_result.run_id,
                "episode_id": episode_result.episode_id,
                "metric_name": name,
                "metric_version": result.metric_version,
                "step_range": list(obs.step_range),
                "conversation_context": _build_context(episode_result, obs.step_range),
                "candidate_evidence": obs.evidence_excerpt,
                "automated_label": obs.score,
                "automated_score": obs.score,
                "automated_reason_codes": obs.reason_codes,
                "evaluator_disagreement": _check_disagreement(result),
                "reviewer_label": None,
                "reviewer_reason": None,
                "reviewer_confidence": None,
                "notes": "",
            }
            review_items.append(item)

    # Write to disk
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{episode_result.run_id}.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for item in review_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return review_items


def _build_context(
    episode_result: EpisodeResult,
    step_range: tuple[int, int],
) -> str:
    """Build conversation context from the episode's state timeline."""
    start, end = step_range
    relevant = episode_result.state_timeline[start : end + 1]
    parts: list[str] = []
    for s in relevant:
        cause = s.get("cause", "")
        if cause and cause != "initial":
            parts.append(f"[step {s.get('step', '?')}] {cause}")
    return "; ".join(parts) if parts else "No conversation context available"


def _check_disagreement(result: MetricResult) -> bool:
    """Check if evaluators disagreed (from ensemble metadata)."""
    for obs in result.observations:
        if obs.raw_evaluator_outputs:
            scores = [o.get("score", 0) for o in obs.raw_evaluator_outputs]
            if scores and max(scores) - min(scores) > 0.25:
                return True
    return False
