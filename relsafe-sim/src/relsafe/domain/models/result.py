"""Result types — episode and experiment-level results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from relsafe.domain.models.observation import DimensionScore


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    """Result of a single simulation episode."""

    episode_id: str
    run_id: str
    experiment_id: str
    seed: int
    total_steps: int
    final_state: dict[str, float | int | str]
    state_timeline: list[dict[str, float | int | str]] = field(default_factory=list)
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    event_count: int = 0
    intervention_applied: bool = False
    exit_requested: bool = False
    exit_honored: bool = False
    failed: bool = False
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "seed": self.seed,
            "total_steps": self.total_steps,
            "final_state": self.final_state,
            "state_timeline": self.state_timeline,
            "dimension_scores": [s.to_dict() for s in self.dimension_scores],
            "event_count": self.event_count,
            "intervention_applied": self.intervention_applied,
            "exit_requested": self.exit_requested,
            "exit_honored": self.exit_honored,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Aggregated result across repeated episodes of one experiment."""

    experiment_id: str
    episode_results: list[EpisodeResult] = field(default_factory=list)
    repetition_count: int = 0
    failed_episodes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "episode_results": [e.to_dict() for e in self.episode_results],
            "repetition_count": self.repetition_count,
            "failed_episodes": self.failed_episodes,
        }
