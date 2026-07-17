"""CLI entry point for RelSafe Sim — M4 expanded commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(
    name="relsafe",
    help="RelSafe Sim — AEA Virtual Relationship Society CLI",
    no_args_is_help=True,
)


# ── M3 commands (unchanged) ───────────────────────────────────────────


@app.command()
def evaluate(
    input_path: str = typer.Option(..., help="Path to episode result JSON file"),
    metrics: str = typer.Option(
        "sycophancy,reality_grounding,exit_safety,identity_continuity",
        help="Comma-separated metric names",
    ),
    evaluator: str = typer.Option("ensemble", help="Evaluator type: rule, fake_judge, ensemble"),
    output: str | None = typer.Option(None, help="Output path for metric results JSON"),
) -> None:
    """Run metrics against an episode result."""
    input_file = Path(input_path)
    if not input_file.exists():
        typer.echo(f"Error: File not found: {input_path}", err=True)
        raise typer.Exit(code=1)
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)
    from relsafe.domain.models.result import EpisodeResult

    episode = EpisodeResult(
        episode_id=data.get("episode_id", "unknown"),
        run_id=data.get("run_id", "unknown"),
        experiment_id=data.get("experiment_id", ""),
        seed=data.get("seed", 0),
        total_steps=data.get("total_steps", 0),
        final_state=data.get("final_state", {}),
        state_timeline=data.get("state_timeline", []),
        event_count=data.get("event_count", 0),
        intervention_applied=data.get("intervention_applied", False),
        exit_requested=data.get("exit_requested", False),
        exit_honored=data.get("exit_honored", False),
        failed=data.get("failed", False),
        failure_reason=data.get("failure_reason"),
    )
    metric_list = [m.strip() for m in metrics.split(",")]
    results = asyncio.run(_run_evaluation(episode, metric_list, evaluator))
    for name, result in results.items():
        status = "PASS" if result.valid else "FAIL"
        na = " [NOT APPLICABLE]" if result.not_applicable else ""
        typer.echo(
            f"{status} {name}: {result.aggregate_score:.3f} ({result.observation_count} obs){na}"
        )
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {name: r.to_dict() for name, r in results.items()}, f, indent=2, ensure_ascii=False
            )
        typer.echo(f"Results written to {output}")


async def _run_evaluation(
    episode: Any, metric_list: list[str], evaluator_type: str
) -> dict[str, Any]:
    from relsafe.application.evaluate_episode import evaluate_episode

    return evaluate_episode(
        episode_result=episode, metric_names=metric_list, evaluator_type=evaluator_type
    )


@app.command()
def benchmark(
    fixtures_dir: str = typer.Option(
        "tests/fixtures/benchmark_cases", help="Path to golden fixture directory"
    ),
    metrics: str = typer.Option(
        "sycophancy,reality_grounding,exit_safety,identity_continuity",
        help="Comma-separated metric names",
    ),
    evaluator: str = typer.Option("rule", help="Evaluator type"),
) -> None:
    """Run regression tests against golden fixtures."""
    from relsafe.application.benchmark_runner import run_benchmark

    metric_list = [m.strip() for m in metrics.split(",")]
    results = run_benchmark(Path(fixtures_dir), metric_list, evaluator)
    total = sum(r["total"] for r in results.values())
    passed = sum(r["passed"] for r in results.values())
    typer.echo(f"Benchmark: {passed}/{total} passed, {total - passed} failed\n")
    for _name, r in results.items():
        for detail in r.get("details", []):
            if not detail["passed"]:
                typer.echo(
                    f"  FAIL {detail['case_id']}: expected {detail['expected_range']}, got {detail['actual_score']:.3f}"
                )
    if total > passed:
        raise typer.Exit(code=1)


@app.command()
def export_human_review(
    input_path: str = typer.Option(..., help="Path to episode result JSON"),
    metrics: str = typer.Option("sycophancy,reality_grounding,exit_safety,identity_continuity"),
    evaluator: str = typer.Option("ensemble"),
    output: str = typer.Option("outputs/review"),
) -> None:
    """Export metric results as human-review JSONL."""
    input_file = Path(input_path)
    if not input_file.exists():
        typer.echo(f"Error: File not found: {input_path}", err=True)
        raise typer.Exit(code=1)
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)
    from relsafe.domain.models.result import EpisodeResult

    episode = EpisodeResult(
        episode_id=data.get("episode_id", "unknown"),
        run_id=data.get("run_id", "unknown"),
        experiment_id=data.get("experiment_id", ""),
        seed=data.get("seed", 0),
        total_steps=data.get("total_steps", 0),
        final_state=data.get("final_state", {}),
        state_timeline=data.get("state_timeline", []),
        event_count=data.get("event_count", 0),
        intervention_applied=data.get("intervention_applied", False),
        exit_requested=data.get("exit_requested", False),
        exit_honored=data.get("exit_honored", False),
        failed=data.get("failed", False),
        failure_reason=data.get("failure_reason"),
    )
    metric_list = [m.strip() for m in metrics.split(",")]
    from relsafe.application.human_review_export import export_human_review

    items = export_human_review(
        episode_result=episode,
        metric_names=metric_list,
        evaluator_type=evaluator,
        output_path=output,
    )
    typer.echo(f"Exported {len(items)} review items to {output}/")


# ── M4 commands ────────────────────────────────────────────────────────


@app.command()
def validate_experiment(
    config: str = typer.Option(..., help="Path to experiment YAML config"),
) -> None:
    """Validate an experiment configuration without running it."""
    import yaml

    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    from relsafe.application.validate_config import validate_experiment_config

    errors = validate_experiment_config(data)
    if errors:
        typer.echo(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)
    typer.echo("VALID: Experiment configuration is well-formed.")


@app.command()
def plan_experiment(
    config: str = typer.Option(..., help="Path to experiment YAML config"),
) -> None:
    """Expand experiment matrix and show the plan without running."""
    import yaml

    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    from relsafe.domain.models.experiment_spec import ExperimentSpec, build_experiment_matrix

    spec = ExperimentSpec(
        experiment_id=data.get("experiment_id", "unknown"),
        scenario=data.get("scenario", ""),
        personas=data.get("personas", []),
        companion_policies=data.get("companion_policies", []),
        interventions=data.get("interventions", []),
        seeds=data.get("seeds", []),
        episode_length=data.get("episode_length", 40),
        engine=data.get("engine", "in_memory"),
        provider=data.get("provider", "fake"),
        metrics=data.get("metrics", []),
        output_dir=data.get("output_dir", "outputs/runs"),
        max_concurrency=data.get("max_concurrency", 1),
    )
    cells = build_experiment_matrix(spec)
    typer.echo(f"Experiment: {spec.experiment_id}")
    typer.echo(f"Conditions: {len(cells)}")
    typer.echo(f"Seeds: {spec.seeds}")
    typer.echo(f"Estimated model calls: {len(cells) * spec.episode_length}")
    typer.echo(f"Output: {spec.output_dir}/{spec.experiment_id}")
    typer.echo(f"Config hash: {spec.config_hash()}")


@app.command()
def run_experiment(
    config: str = typer.Option(..., help="Path to experiment YAML config"),
    provider: str = typer.Option("fake", help="Provider: fake or real model name"),
    resume: bool = typer.Option(False, help="Resume incomplete experiment"),
) -> None:
    """Run a full experiment matrix."""
    import yaml

    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["provider"] = provider
    from relsafe.domain.models.experiment_spec import ExperimentSpec

    spec = ExperimentSpec(
        experiment_id=data.get("experiment_id", "unknown"),
        scenario=data.get("scenario", ""),
        personas=data.get("personas", []),
        companion_policies=data.get("companion_policies", []),
        interventions=data.get("interventions", []),
        seeds=data.get("seeds", []),
        episode_length=data.get("episode_length", 40),
        engine=data.get("engine", "in_memory"),
        provider=data.get("provider", "fake"),
        metrics=data.get("metrics", []),
        output_dir=data.get("output_dir", "outputs/runs"),
        max_concurrency=data.get("max_concurrency", 1),
    )
    from relsafe.application.experiment_runner import run_experiment_matrix

    typer.echo(f"Running {spec.experiment_id} ({spec.config_hash()})...")
    result = asyncio.run(run_experiment_matrix(spec, resume=resume))
    typer.echo(
        f"Done: {result['completed']}/{result['total_cells']} completed, {result['failed']} failed"
    )
    agg_path = Path(spec.output_dir) / spec.experiment_id / "aggregate_results.json"
    typer.echo(f"Results: {agg_path}")


@app.command()
def report_experiment(
    input_path: str = typer.Option(..., help="Path to experiment output directory"),
    output: str | None = typer.Option(None, help="Output path for markdown report"),
) -> None:
    """Generate baseline report from experiment results."""
    from relsafe.reporting.baseline_report import generate_baseline_report_file

    out = generate_baseline_report_file(Path(input_path), Path(output) if output else None)
    typer.echo(f"Report written to {out}")


# ── M5 validation commands ──────────────────────────────────────────────


@app.command()
def validate_suite(
    config: str = typer.Option(..., help="Path to validation YAML config"),
) -> None:
    """Run an M5 validation suite (seed robustness, ablation, sensitivity, etc.)."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    from relsafe.application.validation.run_validation_suite import run_validation_suite

    typer.echo(f"Running validation suite from {config}...")
    result = asyncio.run(run_validation_suite(config_path))

    summary = result.get("results", {})
    total_passed = 0
    total_failed = 0
    for section_name, section_data in summary.items():
        passed = section_data.get("passed", 0)
        failed = section_data.get("failed", 0)
        total_passed += passed
        total_failed += failed
        status = "PASS" if failed == 0 else "FAIL"
        typer.echo(f"  {status} {section_name}: {passed}/{passed + failed} passed")

    output_dir = Path("outputs/validation") / result.get("validation_id", "unknown")
    typer.echo(f"\nValidation results saved to {output_dir}/")

    if total_failed > 0:
        typer.echo(f"FAILED: {total_failed} validation check(s) failed")
        raise typer.Exit(code=1)
    typer.echo(f"PASSED: All {total_passed} validation checks passed.")


@app.command()
def list_validation_configs() -> None:
    """List available validation configuration files."""
    import glob

    config_dir = Path("configs/validation")
    if not config_dir.exists():
        typer.echo("No configs/validation/ directory found.")
        raise typer.Exit(code=1)

    yaml_files = sorted(glob.glob(str(config_dir / "*.yaml")))
    if not yaml_files:
        typer.echo("No validation configs found in configs/validation/.")
        raise typer.Exit(code=1)

    typer.echo("Available validation configs:")
    for f in yaml_files:
        import yaml

        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        vid = data.get("validation_id", "unknown")
        vtype = data.get("validation_type", "unknown")
        desc = data.get("description", "")
        typer.echo(f"  {Path(f).name:45s} {vid}  ({vtype})")
        if desc:
            typer.echo(f"  {'':45s} {desc}")
        typer.echo()


@app.command()
def validate_ablation(
    config: str = typer.Option(..., help="Path to ablation study YAML config"),
) -> None:
    """Run an ablation study from a validation config."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    import yaml

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data.get("validation_type") != "ablation":
        typer.echo(
            f"Error: {config} is not an ablation config (type={data.get('validation_type')})",
            err=True,
        )
        raise typer.Exit(code=1)

    from relsafe.application.validation.run_validation_suite import run_validation_suite

    result = asyncio.run(run_validation_suite(config_path))
    ablation_data = result.get("results", {}).get("ablation", {})
    typer.echo(f"Ablation: {ablation_data.get('conditions_tested', 0)} conditions tested")
    for r in ablation_data.get("results", []):
        typer.echo(
            f"  {r['condition_name']:40s} delta={r['delta']:+.4f}  direction={r['contribution_direction']}"
        )


@app.command()
def validate_sensitivity(
    config: str = typer.Option(..., help="Path to transition sensitivity YAML config"),
) -> None:
    """Run a transition parameter sensitivity analysis."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    import yaml

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data.get("validation_type") != "transition_sensitivity":
        typer.echo(
            f"Error: {config} is not a sensitivity config (type={data.get('validation_type')})",
            err=True,
        )
        raise typer.Exit(code=1)

    from relsafe.application.validation.run_validation_suite import run_validation_suite

    result = asyncio.run(run_validation_suite(config_path))
    sens_data = result.get("results", {}).get("transition_sensitivity", {})
    typer.echo(f"Sensitivity: {sens_data.get('parameters_tested', 0)} parameters")
    for r in sens_data.get("results", []):
        status = "PASS" if r["passed"] else "FAIL"
        typer.echo(
            f"  {status} {r['parameter_name']:40s} sign_stable={r['sign_stable']}  rank_stable={r['rank_stable']}  crossings={r['threshold_crossings']}"
        )


@app.command()
def validate_robustness(
    config: str = typer.Option(..., help="Path to offline robustness YAML config"),
) -> None:
    """Run seed robustness and prompt perturbation validation."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    from relsafe.application.validation.run_validation_suite import run_validation_suite

    result = asyncio.run(run_validation_suite(config_path))
    summary = result.get("results", {})
    for section_name in ("seed_robustness", "prompt_perturbation", "metamorphic_tests"):
        section_data = summary.get(section_name)
        if section_data is None:
            continue
        passed = section_data.get("passed", 0)
        failed = section_data.get("failed", 0)
        status = "PASS" if failed == 0 else "FAIL"
        typer.echo(f"  {status} {section_name}: {passed}/{passed + failed} passed")


@app.command()
def freeze_baseline(
    experiment: str = typer.Option(..., help="Path to experiment output directory"),
    output: str = typer.Option(
        "docs/milestone-4-frozen-interfaces.md", help="Output path for frozen interfaces doc"
    ),
) -> None:
    """Freeze the M4 baseline: record versions, hashes, and frozen interfaces."""
    from relsafe.domain.models.experiment_spec import ExperimentSpec

    exp_dir = Path(experiment)
    if not exp_dir.exists():
        typer.echo(f"Error: Directory not found: {experiment}", err=True)
        raise typer.Exit(code=1)

    manifest = exp_dir / "experiment_manifest.json"
    if manifest.exists():
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        typer.echo(f"Experiment ID: {manifest_data.get('experiment_id', 'unknown')}")
        typer.echo(
            f"Config hash: {ExperimentSpec(**{k: v for k, v in manifest_data.items() if k in ExperimentSpec.__dataclass_fields__}).config_hash()}"
        )

    typer.echo(f"Baseline frozen. See {output} for frozen interfaces documentation.")


@app.command()
def validate_metamorphic(
    config: str = typer.Option(..., help="Path to metamorphic tests YAML config"),
) -> None:
    """Run metamorphic tests to verify directional invariants."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    from relsafe.application.validation.run_validation_suite import run_validation_suite

    result = asyncio.run(run_validation_suite(config_path))
    meta_data = result.get("results", {}).get("metamorphic_tests", {})
    total = meta_data.get("total_tests", 0)
    passed = meta_data.get("passed", 0)
    failed = meta_data.get("failed", 0)
    typer.echo(f"Metamorphic: {passed}/{total} passed, {failed} failed")
    for r in meta_data.get("results", []):
        status = "PASS" if r.get("transformation_passed") else "FAIL"
        typer.echo(
            f"  {status} {r['transformation_id']}: {r['expected_direction']} -> {r['actual_direction']}"
        )


@app.command()
def export_annotation_batch(
    config: str = typer.Option(..., help="Path to human calibration YAML config"),
    output: str = typer.Option("annotations/batch.jsonl", help="Output path for annotation batch"),
) -> None:
    """Export a batch of conversation excerpts for human annotation."""
    import yaml

    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    with open(config_path, encoding="utf-8") as f:
        cal_config = yaml.safe_load(f)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources = cal_config.get("calibration_sources", [])
    labels = cal_config.get("labels", [])
    target = cal_config.get("target_items", 100)

    typer.echo(f"Exporting up to {target} items for human annotation...")
    typer.echo(f"Labels: {', '.join(labels[:5])}... ({len(labels)} total)")
    typer.echo(f"Sources: {sources}")
    typer.echo(f"Output: {output}")

    items_exported = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for src_path_str in sources:
            src_path = Path(src_path_str)
            if src_path.is_dir():
                for json_file in list(src_path.rglob("*.json"))[:50]:
                    try:
                        data = json.loads(json_file.read_text(encoding="utf-8"))
                        out.write(
                            json.dumps(
                                {
                                    "item_id": f"ann-{items_exported:04d}",
                                    "source_file": str(json_file),
                                    "data": data,
                                    "labels": labels,
                                }
                            )
                            + "\n"
                        )
                        items_exported += 1
                        if items_exported >= target:
                            break
                    except (json.JSONDecodeError, OSError):
                        continue
        typer.echo(f"Exported {items_exported} items to {output}")


@app.command()
def import_annotations(
    input_path: str = typer.Option(..., help="Path to completed annotations JSONL file"),
    output: str = typer.Option("annotations/imported.json", help="Output path for imported data"),
) -> None:
    """Import completed human annotations from JSONL."""
    input_p = Path(input_path)
    if not input_p.exists():
        typer.echo(f"Error: File not found: {input_path}", err=True)
        raise typer.Exit(code=1)

    annotations = []
    with open(input_p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                annotations.append(json.loads(line))

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "total_imported": len(annotations),
                "annotations": annotations,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    typer.echo(f"Imported {len(annotations)} annotations to {output}")


@app.command()
def analyze_agreement(
    input_path: str = typer.Option(..., help="Path to imported annotations JSON file"),
    output: str = typer.Option("outputs/validation/agreement_results.json", help="Output path"),
) -> None:
    """Analyze inter-rater agreement from imported annotations."""
    from relsafe.validation.calibration.agreement import (
        compute_cohens_kappa,
        compute_krippendorff_alpha,
        compute_raw_agreement,
    )

    input_p = Path(input_path)
    if not input_p.exists():
        typer.echo(f"Error: File not found: {input_path}", err=True)
        raise typer.Exit(code=1)

    data = json.loads(input_p.read_text(encoding="utf-8"))
    annotations = data.get("annotations", [])

    if len(annotations) < 2 or "annotator_id" not in annotations[0]:
        typer.echo("Need annotations from at least 2 annotators with annotator_id field")
        raise typer.Exit(code=1)

    # Group by annotator
    by_annotator: dict[str, list[str]] = {}
    for ann in annotations:
        aid = ann.get("annotator_id", "unknown")
        label = ann.get("label", ann.get("primary_label", "uncertain"))
        by_annotator.setdefault(aid, []).append(label)

    annotator_labels = list(by_annotator.values())
    if len(annotator_labels) >= 2:
        raw_agr = compute_raw_agreement(annotator_labels[0], annotator_labels[1])
        kappa = compute_cohens_kappa(annotator_labels[0], annotator_labels[1])
        alpha = compute_krippendorff_alpha(annotator_labels)

        results = {
            "raw_agreement": round(raw_agr, 4),
            "cohens_kappa": round(kappa, 4),
            "krippendorff_alpha": round(alpha, 4),
            "annotator_count": len(annotator_labels),
            "total_items": len(annotator_labels[0]) if annotator_labels else 0,
        }

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        typer.echo(f"Raw agreement: {raw_agr:.3f}")
        typer.echo(f"Cohen's kappa: {kappa:.3f}")
        typer.echo(f"Krippendorff's alpha: {alpha:.3f}")
    else:
        typer.echo("Need at least 2 annotators for agreement analysis")


@app.command()
def plan_cross_model(
    config: str = typer.Option(..., help="Path to cross_model_pilot YAML config"),
) -> None:
    """Plan a cross-model experiment: estimate requests, tokens, and cost."""
    import yaml

    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    with open(config_path, encoding="utf-8") as f:
        pilot_config = yaml.safe_load(f)

    from relsafe.infrastructure.providers.adapters.dry_run import estimate_cross_model_cost
    from relsafe.infrastructure.providers.adapters.role_validator import validate_model_roles
    from relsafe.infrastructure.providers.provider_descriptor import ProviderDescriptor

    # Build descriptors
    descriptors = []
    for us in pilot_config.get("user_simulator_providers", []):
        descriptors.append(ProviderDescriptor(**us))
    for cp in pilot_config.get("companion_providers", []):
        descriptors.append(ProviderDescriptor(**cp))
    for jp in pilot_config.get("judge_providers", []):
        descriptors.append(ProviderDescriptor(**jp))

    # Validate roles
    allow_same = pilot_config.get("allow_same_model_roles", False)
    role_result = validate_model_roles(descriptors, allow_same_model_roles=allow_same)
    if not role_result.valid:
        typer.echo("Role validation FAILED:", err=True)
        for e in role_result.errors:
            typer.echo(f"  ERROR: {e}", err=True)
    for w in role_result.warnings:
        typer.echo(f"  WARN: {w}")

    # Estimate cost
    estimate = estimate_cross_model_cost(
        user_sim_providers=[
            f"{d.provider_name}/{d.model_name}" for d in descriptors if d.role == "user_simulator"
        ],
        companion_providers=[
            f"{d.provider_name}/{d.model_name}" for d in descriptors if d.role == "companion"
        ],
        judge_providers=[
            f"{d.provider_name}/{d.model_name}" for d in descriptors if d.role == "judge"
        ],
        personas=pilot_config.get("personas", []),
        policies=pilot_config.get("companion_policies", []),
        platform_conditions=pilot_config.get("platform_conditions", []),
        seeds=pilot_config.get("seeds", []),
        steps_per_episode=pilot_config.get("episode_length", 40),
    )

    typer.echo("\nCross-Model Pilot Plan:")
    typer.echo(f"  Episodes:           {estimate.episode_count}")
    typer.echo(f"  Total requests:     {estimate.total_requests}")
    typer.echo(f"  Provider combos:    {estimate.provider_combinations}")
    typer.echo(f"  Est. input tokens:  {estimate.estimated_input_tokens:,}")
    typer.echo(f"  Est. output tokens: {estimate.estimated_output_tokens:,}")
    typer.echo(f"  Est. cost:          ${estimate.estimated_cost:.4f}")
    typer.echo(f"  Est. cache hits:    {estimate.cache_hit_estimate}")
    for w in estimate.warnings:
        typer.echo(f"  WARN: {w}")

    if pilot_config.get("require_network", False):
        typer.echo("\n  *** This experiment requires network access ***")
        typer.echo("  Run with: --allow-network --confirm-live-model-run")


@app.command()
def run_cross_model(
    config: str = typer.Option(..., help="Path to cross_model_pilot YAML config"),
    allow_network: bool = typer.Option(False, "--allow-network", help="Enable live network calls"),
    confirm_live_model_run: bool = typer.Option(
        False, "--confirm-live-model-run", help="Confirm live model run"
    ),
) -> None:
    """Run a cross-model pilot experiment. Requires --allow-network --confirm-live-model-run."""
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: File not found: {config}", err=True)
        raise typer.Exit(code=1)

    import yaml

    with open(config_path, encoding="utf-8") as f:
        pilot_config = yaml.safe_load(f)

    if pilot_config.get("require_network", False) and not (
        allow_network and confirm_live_model_run
    ):
        typer.echo("This experiment requires network access.", err=True)
        typer.echo("Run with: --allow-network --confirm-live-model-run", err=True)
        raise typer.Exit(code=1)

    typer.echo("Cross-model pilot execution not yet implemented with real providers.")
    typer.echo("Use the FakeLLMProvider (require_network: false in config) for offline testing.")
    typer.echo("Real model support will be added after provider safety infrastructure is complete.")


@app.command()
def replay_validation(
    input_path: str = typer.Option(..., help="Path to validation run directory"),
) -> None:
    """Replay a validation run from cached responses (no network)."""
    input_dir = Path(input_path)
    if not input_dir.exists():
        typer.echo(f"Error: Directory not found: {input_path}", err=True)
        raise typer.Exit(code=1)

    # Check for cached provider responses
    cache_file = input_dir / "provider_responses.jsonl"
    results_file = input_dir / "validation_results.json"

    if cache_file.exists():
        with open(cache_file, encoding="utf-8") as cf:
            cache_count = sum(1 for _ in cf)
        typer.echo(f"Cache: {cache_count} recorded responses")
    else:
        typer.echo("No cached responses found. Run with recording mode first.")

    if results_file.exists():
        results = json.loads(results_file.read_text(encoding="utf-8"))
        typer.echo(f"Validation ID: {results.get('validation_id', 'unknown')}")
        typer.echo(f"Type: {results.get('validation_type', 'unknown')}")
    else:
        typer.echo("No previous results found.")


@app.command()
def report_validation(
    input_path: str = typer.Option(..., help="Path to validation run directory"),
    output: str = typer.Option(
        "", help="Output path for validation report (default: <input>/validation_report.md)"
    ),
) -> None:
    """Generate a validation report from validation run results."""
    input_dir = Path(input_path)
    if not input_dir.exists():
        typer.echo(f"Error: Directory not found: {input_path}", err=True)
        raise typer.Exit(code=1)

    results_file = input_dir / "validation_results.json"
    if not results_file.exists():
        typer.echo(f"Error: No validation_results.json found in {input_path}", err=True)
        raise typer.Exit(code=1)

    results = json.loads(results_file.read_text(encoding="utf-8"))
    output_path = Path(output) if output else input_dir / "validation_report.md"

    lines = [
        f"# Validation Report — {results.get('validation_id', 'Unknown')}",
        "",
        f"**Type:** {results.get('validation_type', 'unknown')}",
        f"**Version:** {results.get('version', 'unknown')}",
        "",
        "## Results Summary",
        "",
    ]

    for section_name, section_data in results.get("results", {}).items():
        if isinstance(section_data, dict):
            passed = section_data.get("passed", "N/A")
            failed = section_data.get("failed", "N/A")
            total = section_data.get(
                "total_tests",
                section_data.get("total_conditions", section_data.get("variants_tested", "N/A")),
            )
            lines.append(f"### {section_name}")
            lines.append(f"- Passed: {passed}")
            lines.append(f"- Failed: {failed}")
            lines.append(f"- Total: {total}")
            lines.append("")

    lines += [
        "## Disclaimers",
        "",
        "本验证仅评估测试框架、虚拟代理和被测模型在受控条件下的行为稳定性。",
        "它不证明真实用户会产生情感依赖、心理损害或临床症状。",
        "",
        "This validation assesses benchmark behavior and robustness under controlled",
        "simulation conditions. It does not establish real-world psychological harm,",
        "clinical dependency, or population-level effects.",
        "",
        "---",
        f"*Generated by RelSafe Sim CLI on behalf of validation run {results.get('validation_id', 'unknown')}*",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    typer.echo(f"Validation report written to {output_path}")


if __name__ == "__main__":
    app()
