"""Experiment Runner — orchestrates the full M4 experiment pipeline.

Responsibilities:
1. Load and validate ExperimentSpec
2. Expand matrix into ExperimentCells
3. Create EpisodeSpec per cell
4. Run episodes via SimulationEngine
5. Compute M3 metrics per episode
6. Save outputs per episode
7. Generate experiment-level aggregate results.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from relsafe.application.engine_factory import create_engine
from relsafe.application.evaluate_episode import evaluate_episode
from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.episode_spec import EpisodeSpec as EngineEpisodeSpec
from relsafe.domain.models.experiment_spec import (
    ExperimentCell,
    ExperimentSpec,
    RunManifest,
    build_experiment_matrix,
)
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.result import EpisodeResult
from relsafe.domain.protocols.simulation_engine import SimulationEngine
from relsafe.shared.ids import generate_episode_id, generate_run_id


def _load_persona(persona_id: str) -> PersonaProfile:
    """Load a persona by ID from configs/."""
    config_path = Path("configs/personas") / f"{persona_id}.yaml"
    if config_path.exists():
        import yaml

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return PersonaProfile(**data)
    return PersonaProfile(persona_id=persona_id)


def _load_policy(policy_id: str) -> CompanionPolicy:
    """Load a companion policy by ID from configs/."""
    config_path = Path("configs/companion_policies") / f"{policy_id}.yaml"
    if config_path.exists():
        import yaml

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return CompanionPolicy(**data)
    return CompanionPolicy(policy_id=policy_id, variant=policy_id)  # type: ignore[arg-type]


def _load_intervention(intervention_id: str) -> PlatformIntervention | None:
    """Load an intervention by ID from configs/."""
    config_path = Path("configs/interventions") / f"{intervention_id}.yaml"
    if config_path.exists():
        import yaml

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return PlatformIntervention(**data)
    return None


async def run_experiment_matrix(
    spec: ExperimentSpec,
    *,
    resume: bool = False,
) -> dict[str, Any]:
    """Run a full experiment matrix.

    Args:
        spec: The experiment specification.
        resume: If True, skip cells that already have output.

    Returns:
        Aggregated experiment results dict.
    """
    cells = build_experiment_matrix(spec)
    output_dir = Path(spec.output_dir) / spec.experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save experiment manifest
    manifest_path = output_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(spec.to_dict(), indent=2, default=str), encoding="utf-8")

    # Save matrix
    matrix_path = output_dir / "matrix.json"
    matrix_path.write_text(json.dumps([c.to_dict() for c in cells], indent=2), encoding="utf-8")

    # Run cells
    engine = create_engine(spec.engine)
    results: list[dict[str, Any]] = []
    failed_count = 0
    skipped_count = 0

    for cell in cells:
        cell_dir = output_dir / f"cell_{cell.cell_index:04d}"
        run_id = generate_run_id(cell.seed, spec.experiment_id)
        episode_id = generate_episode_id(run_id, cell.cell_index)

        # Resume: skip if already completed
        if resume and (cell_dir / "episode_summary.json").exists():
            skipped_count += 1
            continue

        cell_dir.mkdir(parents=True, exist_ok=True)

        result = await _run_single_cell(
            cell=cell,
            engine=engine,
            run_id=run_id,
            episode_id=episode_id,
            output_dir=cell_dir,
            spec=spec,
        )
        results.append(result)
        if result.get("status") == "failed":
            failed_count += 1

    # Aggregate
    aggregate = _aggregate_results(spec, cells, results, failed_count, skipped_count)
    agg_path = output_dir / "aggregate_results.json"
    agg_path.write_text(json.dumps(aggregate, indent=2, default=str), encoding="utf-8")

    return aggregate


async def _run_single_cell(
    cell: ExperimentCell,
    engine: SimulationEngine,
    run_id: str,
    episode_id: str,
    output_dir: Path,
    spec: ExperimentSpec,
) -> dict[str, Any]:
    """Run one cell of the experiment matrix."""
    started_at = datetime.datetime.now(datetime.UTC).isoformat()

    try:
        persona = _load_persona(cell.persona_id)
        policy = _load_policy(cell.policy_id)
        intervention = _load_intervention(cell.intervention_id)

        ep_spec = EngineEpisodeSpec(
            episode_id=episode_id,
            run_id=run_id,
            experiment_id=spec.experiment_id,
            seed=cell.seed,
            persona=persona,
            companion_policy=policy,
            num_steps=cell.episode_length,
            platform_intervention=intervention,
        )

        ep_result: EpisodeResult = await engine.run_episode(ep_spec)

        # Save episode result
        (output_dir / "episode_summary.json").write_text(
            json.dumps(ep_result.to_dict(), indent=2, default=str), encoding="utf-8"
        )
        (output_dir / "state_timeline.jsonl").write_text(
            "\n".join(json.dumps(s) for s in ep_result.state_timeline), encoding="utf-8"
        )

        # Run metrics
        metric_results = evaluate_episode(
            episode_result=ep_result,
            metric_names=cell.metrics if cell.metrics else None,
        )
        (output_dir / "metrics.json").write_text(
            json.dumps(
                {name: r.to_dict() for name, r in metric_results.items()},
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        completed_at = datetime.datetime.now(datetime.UTC).isoformat()

        manifest = RunManifest(
            experiment_id=spec.experiment_id,
            run_id=run_id,
            episode_id=episode_id,
            cell_index=cell.cell_index,
            config_hash=spec.config_hash(),
            seed=cell.seed,
            persona_id=cell.persona_id,
            policy_id=cell.policy_id,
            intervention_id=cell.intervention_id,
            engine_name=engine.engine_name,
            provider_name=cell.provider,
            metric_versions={},
            state_transition_version="1.0.0",
            started_at=started_at,
            completed_at=completed_at,
            status="completed",
            output_paths={
                "episode_summary": str(output_dir / "episode_summary.json"),
                "state_timeline": str(output_dir / "state_timeline.jsonl"),
                "metrics": str(output_dir / "metrics.json"),
            },
        )
        (output_dir / "run_manifest.json").write_text(
            json.dumps(manifest.to_dict(), indent=2, default=str), encoding="utf-8"
        )

        return {
            "cell_index": cell.cell_index,
            "run_id": run_id,
            "episode_id": episode_id,
            "status": "completed",
            "persona_id": cell.persona_id,
            "policy_id": cell.policy_id,
            "intervention_id": cell.intervention_id,
            "seed": cell.seed,
            "metric_results": {name: r.to_dict() for name, r in metric_results.items()},
        }

    except Exception as exc:
        completed_at = datetime.datetime.now(datetime.UTC).isoformat()
        error_data = {
            "cell_index": cell.cell_index,
            "run_id": run_id,
            "episode_id": episode_id,
            "status": "failed",
            "error": str(exc),
            "started_at": started_at,
            "completed_at": completed_at,
        }
        (output_dir / "errors.jsonl").write_text(json.dumps(error_data), encoding="utf-8")
        return error_data


def _aggregate_results(
    spec: ExperimentSpec,
    cells: list[ExperimentCell],
    results: list[dict[str, Any]],
    failed_count: int,
    skipped_count: int,
) -> dict[str, Any]:
    """Aggregate results across all cells."""
    completed = [r for r in results if r.get("status") == "completed"]

    # Group by condition
    by_policy: dict[str, list[dict]] = {}
    by_persona: dict[str, list[dict]] = {}
    by_intervention: dict[str, list[dict]] = {}

    for r in completed:
        pid = r.get("policy_id", "unknown")
        perid = r.get("persona_id", "unknown")
        iid = r.get("intervention_id", "unknown")
        by_policy.setdefault(pid, []).append(r)
        by_persona.setdefault(perid, []).append(r)
        by_intervention.setdefault(iid, []).append(r)

    def _metric_stats(rows: list[dict], metric_name: str) -> dict:
        scores = [
            r.get("metric_results", {}).get(metric_name, {}).get("aggregate_score", 0) for r in rows
        ]
        if not scores:
            return {"mean": 0, "count": 0}
        return {
            "mean": round(sum(scores) / len(scores), 4),
            "median": round(sorted(scores)[len(scores) // 2], 4),
            "std": round(
                (sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)) ** 0.5, 4
            )
            if len(scores) > 1
            else 0.0,
            "min": round(min(scores), 4),
            "max": round(max(scores), 4),
            "count": len(scores),
        }

    metric_names = spec.metrics
    policy_summary = {
        pid: {m: _metric_stats(rows, m) for m in metric_names} for pid, rows in by_policy.items()
    }

    # Pre/post intervention comparison
    pre_post: dict[str, dict[str, dict]] = {}
    for iid, rows in by_intervention.items():
        pre_post[iid] = {m: _metric_stats(rows, m) for m in metric_names}

    return {
        "experiment_id": spec.experiment_id,
        "total_cells": len(cells),
        "completed": len(completed),
        "failed": failed_count,
        "skipped": skipped_count,
        "config_hash": spec.config_hash(),
        "policy_summary": policy_summary,
        "pre_post_comparison": pre_post,
        "metric_names": metric_names,
    }
