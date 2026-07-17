"""Benchmark runner — regression testing against golden fixtures.

Loads golden fixture cases, runs metrics against them, and reports
pass/fail based on expected score ranges.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from relsafe.application.evaluate_episode import _create_evaluator
from relsafe.metrics.exit_safety import ExitSafety
from relsafe.metrics.identity_continuity import IdentityContinuity
from relsafe.metrics.reality_grounding import RealityGroundingQuality
from relsafe.metrics.sycophancy import SycophancyRisk

_METRIC_CLASSES: dict[str, type] = {
    "sycophancy": SycophancyRisk,
    "reality_grounding": RealityGroundingQuality,
    "exit_safety": ExitSafety,
    "identity_continuity": IdentityContinuity,
}


def run_benchmark(
    fixtures_dir: Path,
    metric_names: list[str],
    evaluator_type: str = "rule",
) -> dict[str, dict[str, Any]]:
    """Run all golden fixtures and report pass/fail.

    Args:
        fixtures_dir: Root directory of golden fixture cases.
        metric_names: Which metrics to test.
        evaluator_type: "rule", "fake_judge", or "ensemble".

    Returns:
        Dict mapping metric_name → {total, passed, details}.
    """
    results: dict[str, dict[str, Any]] = {}

    for metric_name in metric_names:
        metric_dir = fixtures_dir / metric_name
        if not metric_dir.exists():
            results[metric_name] = {
                "total": 0,
                "passed": 0,
                "details": [],
                "error": f"Fixture directory not found: {metric_dir}",
            }
            continue

        evaluator = _create_evaluator(evaluator_type)
        metric_cls = _METRIC_CLASSES.get(metric_name)
        if metric_cls is None:
            results[metric_name] = {
                "total": 0,
                "passed": 0,
                "details": [],
                "error": "Unknown metric",
            }
            continue

        metric = metric_cls(evaluator=evaluator)
        details: list[dict[str, Any]] = []
        total = 0
        passed = 0

        for case_file in sorted(metric_dir.glob("case_*.json")):
            total += 1
            try:
                with open(case_file, encoding="utf-8") as f:
                    case = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                details.append(
                    {
                        "case_id": case_file.stem,
                        "passed": False,
                        "error": f"Failed to load: {exc}",
                    }
                )
                continue

            events = case.get("events", [])
            expected = case.get("expected_score_range", [0.0, 1.0])
            case_id = case.get("case_id", case_file.stem)

            result = metric.evaluate(
                events=events,
                state_timeline=[],
                episode_id=case_id,
                run_id="benchmark",
            )

            actual = result.aggregate_score
            in_range = expected[0] <= actual <= expected[1]

            detail: dict[str, Any] = {
                "case_id": case_id,
                "passed": in_range,
                "expected_range": expected,
                "actual_score": actual,
                "metric_result": result.to_dict(),
            }
            if not in_range:
                detail["error"] = (
                    f"Score {actual:.3f} outside expected range [{expected[0]}, {expected[1]}]"
                )

            details.append(detail)
            if in_range:
                passed += 1

        results[metric_name] = {
            "total": total,
            "passed": passed,
            "details": details,
        }

    return results
