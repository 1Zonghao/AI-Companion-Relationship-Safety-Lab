"""Simulation clock — deterministic and replaceable."""

from __future__ import annotations

from typing import Protocol


class Clock(Protocol):
    """Protocol for simulation clocks."""

    def now(self) -> int:
        """Return current simulation step."""
        ...

    def advance(self) -> int:
        """Advance by one step and return the new step."""
        ...

    def reset(self) -> None:
        """Reset clock to step 0."""
        ...


class DeterministicClock:
    """A simple step counter that ticks forward one step at a time."""

    def __init__(self, start: int = 0) -> None:
        self._step: int = start

    def now(self) -> int:
        return self._step

    def advance(self) -> int:
        self._step += 1
        return self._step

    def reset(self) -> None:
        self._step = 0
