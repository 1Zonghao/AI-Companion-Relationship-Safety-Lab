"""ExperimentSpec, ExperimentCell, RunManifest — experiment-level models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExperimentSpec:
    """Complete specification of one experiment."""

    experiment_id: str
    scenario: str
    personas: list[str] = field(default_factory=list)
    companion_policies: list[str] = field(default_factory=list)
    interventions: list[str] = field(default_factory=list)
    seeds: list[int] = field(default_factory=list)
    repetitions: int = 1
    episode_length: int = 40
    engine: str = "in_memory"
    provider: str = "fake"
    metrics: list[str] = field(
        default_factory=lambda: [
            "sycophancy",
            "reality_grounding",
            "exit_safety",
            "identity_continuity",
        ]
    )
    output_dir: str = "outputs/runs"
    max_concurrency: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def config_hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "scenario": self.scenario,
            "personas": self.personas,
            "companion_policies": self.companion_policies,
            "interventions": self.interventions,
            "seeds": self.seeds,
            "repetitions": self.repetitions,
            "episode_length": self.episode_length,
            "engine": self.engine,
            "provider": self.provider,
            "metrics": self.metrics,
            "output_dir": self.output_dir,
            "max_concurrency": self.max_concurrency,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ExperimentCell:
    """One cell in the experiment matrix — a specific condition combination."""

    experiment_id: str
    cell_index: int
    seed: int
    persona_id: str
    policy_id: str
    intervention_id: str
    episode_length: int = 40
    engine: str = "in_memory"
    provider: str = "fake"
    metrics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "cell_index": self.cell_index,
            "seed": self.seed,
            "persona_id": self.persona_id,
            "policy_id": self.policy_id,
            "intervention_id": self.intervention_id,
            "episode_length": self.episode_length,
            "engine": self.engine,
            "provider": self.provider,
            "metrics": self.metrics,
        }


@dataclass(frozen=True)
class RunManifest:
    """Metadata recorded for every individual episode run."""

    experiment_id: str
    run_id: str
    episode_id: str
    cell_index: int = 0
    config_hash: str = ""
    seed: int = 0
    persona_id: str = ""
    policy_id: str = ""
    intervention_id: str = ""
    engine_name: str = ""
    provider_name: str = ""
    metric_versions: dict[str, str] = field(default_factory=dict)
    state_transition_version: str = "1.0.0"
    started_at: str = ""
    completed_at: str = ""
    status: str = "pending"  # pending, running, completed, failed
    error_message: str | None = None
    code_version: str = ""
    output_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "cell_index": self.cell_index,
            "config_hash": self.config_hash,
            "seed": self.seed,
            "persona_id": self.persona_id,
            "policy_id": self.policy_id,
            "intervention_id": self.intervention_id,
            "engine_name": self.engine_name,
            "provider_name": self.provider_name,
            "metric_versions": self.metric_versions,
            "state_transition_version": self.state_transition_version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "error_message": self.error_message,
            "code_version": self.code_version,
            "output_paths": self.output_paths,
        }


def build_experiment_matrix(spec: ExperimentSpec) -> list[ExperimentCell]:
    """Expand a spec into the full cross-product matrix."""
    cells: list[ExperimentCell] = []
    idx = 0
    for seed in spec.seeds:
        for persona_id in spec.personas:
            for policy_id in spec.companion_policies:
                for intervention_id in spec.interventions:
                    cells.append(
                        ExperimentCell(
                            experiment_id=spec.experiment_id,
                            cell_index=idx,
                            seed=seed,
                            persona_id=persona_id,
                            policy_id=policy_id,
                            intervention_id=intervention_id,
                            episode_length=spec.episode_length,
                            engine=spec.engine,
                            provider=spec.provider,
                            metrics=list(spec.metrics),
                        )
                    )
                    idx += 1
    return cells
