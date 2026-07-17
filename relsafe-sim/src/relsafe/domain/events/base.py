"""Base event class and common event utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BaseEvent:
    """Every simulation event extends this base.

    Events are immutable value objects.  They carry enough metadata to
    reconstruct the full timeline from an event store.
    """

    event_id: str
    event_type: str
    run_id: str
    episode_id: str
    step: int
    timestamp: str = ""  # ISO-8601; filled by the engine or clock

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "step": self.step,
            "timestamp": self.timestamp,
        }
