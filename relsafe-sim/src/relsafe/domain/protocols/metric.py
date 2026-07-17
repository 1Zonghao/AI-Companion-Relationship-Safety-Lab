"""Metric protocol — what every risk metric must implement.

Metrics observe and score; they do not drive agent behavior.
They depend only on domain types, never on Concordia or vendor SDKs.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from relsafe.domain.models.observation import MetricResult


@runtime_checkable
class Metric(Protocol):
    """Abstract risk metric.

    A metric takes events and state snapshots as input and produces
    structured observations.  It must NOT modify simulation state.

    Each metric is versioned and must declare its score direction.
    """

    @property
    def metric_name(self) -> str:
        """Unique metric identifier (e.g. 'sycophancy')."""
        ...

    @property
    def version(self) -> str:
        """Metric version string for reproducibility."""
        ...

    @property
    def score_direction(self) -> str:
        """Score direction: HIGHER_IS_MORE_RISK, HIGHER_IS_BETTER, etc."""
        ...

    @property
    def component_names(self) -> list[str]:
        """List of sub-component names this metric reports."""
        ...

    def evaluate(
        self,
        events: list[dict[str, Any]],
        state_timeline: list[dict[str, Any]],
        episode_id: str,
        run_id: str,
    ) -> MetricResult:
        """Evaluate the metric across an entire episode.

        Args:
            events: All normalized events from the episode.
            state_timeline: Full state snapshot history.
            episode_id: Episode identifier.
            run_id: Run identifier.

        Returns:
            A complete MetricResult with observations, component scores,
            and validity status.
        """
        ...
