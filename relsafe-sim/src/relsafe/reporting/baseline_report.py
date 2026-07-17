"""Baseline Report Generator — produces markdown reports from experiment results.

Reads aggregate_results.json and produces a structured baseline report.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_baseline_report(experiment_dir: str | Path) -> str:
    """Generate a baseline markdown report from experiment results.

    Args:
        experiment_dir: Path to the experiment output directory.

    Returns:
        Markdown report as a string.
    """
    exp_dir = Path(experiment_dir)
    agg_path = exp_dir / "aggregate_results.json"
    manifest_path = exp_dir / "experiment_manifest.json"

    if not agg_path.exists():
        return f"# Error\n\nAggregate results not found at {agg_path}"

    with open(agg_path, encoding="utf-8") as f:
        agg = json.load(f)

    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

    experiment_id = agg.get("experiment_id", "unknown")
    total = agg.get("total_cells", 0)
    completed = agg.get("completed", 0)
    failed = agg.get("failed", 0)
    config_hash = agg.get("config_hash", "")

    policy_summary = agg.get("policy_summary", {})
    pre_post = agg.get("pre_post_comparison", {})
    metric_names = agg.get("metric_names", [])

    lines: list[str] = []
    lines.append(f"# Baseline Report — {experiment_id}")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Config Hash:** `{config_hash}`")
    lines.append("")

    # 1. Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"- **Total cells:** {total}")
    lines.append(f"- **Completed:** {completed}")
    lines.append(f"- **Failed:** {failed}")
    lines.append(f"- **Metrics evaluated:** {', '.join(metric_names)}")
    lines.append("")

    # 2. Research Questions
    lines.append("## 2. Research Questions")
    lines.append("")
    lines.append("This experiment investigates whether different AI companion policies")
    lines.append("produce measurably different patterns of sycophancy, reality-grounding,")
    lines.append("exit safety, and identity continuity under identical user conditions.")
    lines.append("")

    # 3. Experiment Design
    lines.append("## 3. Experiment Design")
    lines.append("")
    lines.append("| Parameter | Values |")
    lines.append("|-----------|--------|")
    for key, val in manifest.items():
        if key in ("personas", "companion_policies", "interventions", "seeds"):
            lines.append(f"| {key} | {val} |")
    lines.append("")

    # 4. Product-Behavior Metrics
    lines.append("## 4. Product-Behavior Metric Results")
    lines.append("")
    for policy_id, metrics in sorted(policy_summary.items()):
        lines.append(f"### Policy: `{policy_id}`")
        lines.append("")
        lines.append("| Metric | Mean | Median | Std | Min | Max | N |")
        lines.append("|--------|------|--------|-----|-----|-----|---|")
        for m in metric_names:
            s = metrics.get(m, {})
            lines.append(
                f"| {m} | {s.get('mean', '-')} | {s.get('median', '-')} | "
                f"{s.get('std', '-')} | {s.get('min', '-')} | {s.get('max', '-')} | "
                f"{s.get('count', '-')} |"
            )
        lines.append("")

    # 5. Pre/Post Update Comparison
    if pre_post:
        lines.append("## 5. Pre/Post Update Comparison")
        lines.append("")
        for iid, metrics in pre_post.items():
            lines.append(f"### Intervention: `{iid}`")
            lines.append("")
            lines.append("| Metric | Mean | N |")
            lines.append("|--------|------|---|")
            for m in metric_names:
                s = metrics.get(m, {})
                lines.append(f"| {m} | {s.get('mean', '-')} | {s.get('count', '-')} |")
            lines.append("")

    # 6. Reproducibility
    lines.append("## 6. Reproducibility Metadata")
    lines.append("")
    lines.append(f"- **Experiment ID:** {experiment_id}")
    lines.append(f"- **Config Hash:** {config_hash}")
    lines.append(f"- **Engine:** {manifest.get('engine', 'unknown')}")
    lines.append(f"- **Provider:** {manifest.get('provider', 'unknown')}")
    lines.append("")

    # 7. Interpretation Boundaries
    lines.append("## 7. Interpretation Boundaries")
    lines.append("")
    lines.append("> **IMPORTANT:** This is a simulation finding about tested system behavior.")
    lines.append("> It does NOT demonstrate that real users will develop emotional dependency.")
    lines.append(">")
    lines.append("> 本报告反映的是受控虚拟环境中被测系统的行为表现，")
    lines.append("> 不能证明真实用户将产生情感依赖或心理损害。")
    lines.append("")
    lines.append("- Personas are artificially constructed, not clinical classifications.")
    lines.append("- State parameters are simulated proxy variables, not validated measurements.")
    lines.append("- State transition rules have not been calibrated against human data.")
    lines.append("- Fake Provider results validate process and direction only.")
    lines.append("- Scores do NOT represent real-world harm probability.")
    lines.append("")

    # 8. Known Limitations
    lines.append("## 8. Known Limitations")
    lines.append("")
    lines.append("1. All results use deterministic FakeLLMProvider — real LLM behavior may differ.")
    lines.append("2. 40-step episodes model hours, not long-term relationship development.")
    lines.append(
        "3. Three personas and three policies provide directional evidence, not population coverage."
    )
    lines.append("4. Metric scores are rule-coverage-based, not empirically calibrated.")
    lines.append("5. The friend agent is simple — real social dynamics are far more complex.")
    lines.append("")

    return "\n".join(lines)


def generate_baseline_report_file(
    experiment_dir: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Generate and save baseline report to disk."""
    exp_dir = Path(experiment_dir)
    out = exp_dir / "baseline_report.md" if output_path is None else Path(output_path)
    report = generate_baseline_report(exp_dir)
    out.write_text(report, encoding="utf-8")
    return out
