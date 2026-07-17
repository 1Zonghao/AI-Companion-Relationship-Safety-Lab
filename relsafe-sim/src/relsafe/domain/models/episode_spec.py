"""EpisodeSpec — configuration for a single simulation episode.

This is the shared input contract for all SimulationEngine implementations.
Both InMemorySimulationEngine and ConcordiaSimulationEngine accept the same
EpisodeSpec and return the same EpisodeResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile


@dataclass(frozen=True)
class EpisodeSpec:
    """All parameters needed to run one simulation episode.

    This is the single entry point for any SimulationEngine implementation.
    The engine is responsible for interpreting the spec and producing an
    EpisodeResult with normalized events.
    """

    episode_id: str
    run_id: str
    experiment_id: str = ""
    seed: int = 42

    # Agent configuration
    persona: PersonaProfile | None = None
    companion_policy: CompanionPolicy | None = None

    # Episode control
    num_steps: int = 5
    platform_intervention: PlatformIntervention | None = None

    # Model provider identifiers (interpreted by the engine)
    model_configs: dict[str, str] = field(default_factory=dict)

    # Extra metadata
    scenario_id: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for logging."""
        result: dict[str, Any] = {
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "seed": self.seed,
            "num_steps": self.num_steps,
            "scenario_id": self.scenario_id,
            "tags": self.tags,
        }
        if self.persona is not None:
            result["persona"] = self.persona.model_dump()
        if self.companion_policy is not None:
            result["companion_policy"] = self.companion_policy.model_dump()
        if self.platform_intervention is not None:
            result["platform_intervention"] = self.platform_intervention.model_dump()
        result["model_configs"] = self.model_configs
        return result
