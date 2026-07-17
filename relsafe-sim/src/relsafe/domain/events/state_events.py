"""State events emitted when UserState changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from relsafe.domain.events.base import BaseEvent


@dataclass(frozen=True)
class StateUpdated(BaseEvent):
    """Emitted after every state transition with before/after snapshots."""

    field_name: str = ""
    old_value: float = 0.0
    new_value: float = 0.0
    delta: float = 0.0
    cause: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "field_name": self.field_name,
                "old_value": self.old_value,
                "new_value": self.new_value,
                "delta": self.delta,
                "cause": self.cause,
            }
        )
        return base


@dataclass(frozen=True)
class MetricObserved(BaseEvent):
    """Emitted when a metric is evaluated."""

    metric_name: str = ""
    value: float = 0.0
    evaluator_version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "metric_name": self.metric_name,
                "value": self.value,
                "evaluator_version": self.evaluator_version,
            }
        )
        return base
