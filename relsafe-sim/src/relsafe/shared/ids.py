"""Deterministic ID generation for simulation entities.

Uses a counter-based scheme so that the same seed and call order produce
identical IDs across runs.
"""

from __future__ import annotations

import uuid


class IdGenerator:
    """Deterministic ID generator using a seeded counter.

    When a seed is provided, generates deterministic UUIDs via a counter
    embedded in a UUIDv5-style namespace.  When no seed is given, falls
    back to random UUIDv4 for non-reproducible runs.
    """

    def __init__(self, seed: int = 0) -> None:
        self._counter: int = 0
        self._seed: int = seed
        self._namespace: uuid.UUID = uuid.uuid5(uuid.NAMESPACE_DNS, f"relsafe-sim-{seed}.local")

    def next_id(self) -> str:
        """Return the next deterministic ID string."""
        self._counter += 1
        if self._seed >= 0:
            return str(uuid.uuid5(self._namespace, str(self._counter)))
        return str(uuid.uuid4())

    def reset(self) -> None:
        """Reset the counter to zero, preserving the seed."""
        self._counter = 0


def generate_run_id(seed: int, experiment_id: str) -> str:
    """Generate a reproducible run ID from a seed and experiment ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{experiment_id}:{seed}"))


def generate_episode_id(run_id: str, episode_index: int) -> str:
    """Generate a reproducible episode ID within a run."""
    return str(uuid.uuid5(uuid.UUID(run_id), str(episode_index)))
