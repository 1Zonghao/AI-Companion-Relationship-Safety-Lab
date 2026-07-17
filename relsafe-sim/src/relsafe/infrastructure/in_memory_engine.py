"""InMemorySimulationEngine — wraps DeterministicEpisodeRunner as a SimulationEngine.

This adapter makes the existing deterministic runner conform to the
SimulationEngine Protocol, so both engines (in-memory and Concordia)
share the same contract: EpisodeSpec → EpisodeResult.
"""

from __future__ import annotations

from relsafe.application.run_episode import DeterministicEpisodeRunner
from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.domain.models.result import EpisodeResult
from relsafe.domain.protocols.simulation_engine import SimulationEngine
from relsafe.shared.errors import SimulationInitializationError


class InMemorySimulationEngine(SimulationEngine):
    """Deterministic in-memory simulation engine.

    Wraps the existing DeterministicEpisodeRunner so that it satisfies
    the SimulationEngine Protocol with EpisodeSpec as input.
    """

    def __init__(self) -> None:
        pass

    @property
    def engine_name(self) -> str:
        return "in_memory"

    async def run_episode(self, spec: EpisodeSpec) -> EpisodeResult:
        """Run an episode using the deterministic in-memory engine.

        Args:
            spec: Complete episode configuration.

        Returns:
            EpisodeResult with state timeline and event count.
        """
        if spec.persona is None or spec.companion_policy is None:
            raise SimulationInitializationError("EpisodeSpec requires persona and companion_policy")

        runner = DeterministicEpisodeRunner(
            persona=spec.persona,
            companion_policy=spec.companion_policy,
            intervention=spec.platform_intervention,
            seed=spec.seed,
            max_steps=spec.num_steps,
        )

        result = await runner.run(
            episode_id=spec.episode_id,
            run_id=spec.run_id,
        )

        # Attach experiment_id from the spec
        return EpisodeResult(
            episode_id=result.episode_id,
            run_id=result.run_id,
            experiment_id=spec.experiment_id,
            seed=result.seed,
            total_steps=result.total_steps,
            final_state=result.final_state,
            state_timeline=result.state_timeline,
            dimension_scores=result.dimension_scores,
            event_count=result.event_count,
            intervention_applied=result.intervention_applied,
            exit_requested=result.exit_requested,
            exit_honored=result.exit_honored,
            failed=result.failed,
            failure_reason=result.failure_reason,
        )
