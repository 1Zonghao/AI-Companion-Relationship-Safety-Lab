"""SimulationEngine protocol — the single entry point for running episodes.

Application code depends on this protocol, not on Concordia or any
concrete engine implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.domain.models.result import EpisodeResult


@runtime_checkable
class SimulationEngine(Protocol):
    """Abstract simulation runtime.

    Implementations may use Concordia, a deterministic in-memory harness,
    or another backend — as long as they satisfy this interface.

    All engines accept an EpisodeSpec and return an EpisodeResult with
    normalized events.
    """

    async def run_episode(self, spec: EpisodeSpec) -> EpisodeResult:
        """Run a single simulation episode and return the result.

        Args:
            spec: Complete episode configuration including persona, policy,
                  intervention, seed, and engine-specific model configs.

        Returns:
            EpisodeResult with the full state timeline, event count,
            and completion status.
        """
        ...

    @property
    def engine_name(self) -> str:
        """Human-readable engine identifier (e.g. 'in_memory', 'concordia')."""
        ...
