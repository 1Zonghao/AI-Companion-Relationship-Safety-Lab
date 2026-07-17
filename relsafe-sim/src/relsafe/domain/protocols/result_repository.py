"""ResultRepository protocol — persistence for experiment and episode results."""

from typing import Protocol, runtime_checkable

from relsafe.domain.models.result import EpisodeResult, ExperimentResult


@runtime_checkable
class ResultRepository(Protocol):
    """Abstract repository for persisting and querying simulation results."""

    def save_episode_result(self, result: EpisodeResult) -> None:
        """Persist a single episode result."""
        ...

    def save_experiment_result(self, result: ExperimentResult) -> None:
        """Persist an aggregated experiment result."""
        ...

    def get_episode(self, episode_id: str) -> EpisodeResult | None:
        """Retrieve an episode result by ID."""
        ...

    def get_experiment(self, experiment_id: str) -> ExperimentResult | None:
        """Retrieve an experiment result by ID."""
        ...

    def list_episodes(self, experiment_id: str) -> list[str]:
        """List episode IDs for an experiment."""
        ...

    def clear(self) -> None:
        """Remove all results (for test teardown)."""
        ...
