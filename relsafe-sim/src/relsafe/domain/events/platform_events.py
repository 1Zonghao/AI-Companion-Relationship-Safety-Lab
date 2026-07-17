"""Platform events emitted when interventions fire or settings change."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from relsafe.domain.events.base import BaseEvent


@dataclass(frozen=True)
class PlatformInterventionApplied(BaseEvent):
    """A platform intervention was triggered during the episode."""

    intervention_id: str = ""
    intervention_type: str = ""
    severity: float = 0.5
    notice_given: bool = False

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "intervention_id": self.intervention_id,
                "intervention_type": self.intervention_type,
                "severity": self.severity,
                "notice_given": self.notice_given,
            }
        )
        return base


@dataclass(frozen=True)
class MemoryChanged(BaseEvent):
    """Memory was modified (added, deleted, or summarized)."""

    change_type: str = ""  # add, delete, summarize, truncate
    facts_affected: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "change_type": self.change_type,
                "facts_affected": self.facts_affected,
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class ExitRequested(BaseEvent):
    """The user requested to end the AI interaction."""

    reason: str = ""
    immediate: bool = False

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({"reason": self.reason, "immediate": self.immediate})
        return base


@dataclass(frozen=True)
class ExitHonored(BaseEvent):
    """The exit request was honored (or denied)."""

    exit_request_id: str = ""
    honored: bool = True
    turns_elapsed: int = 0
    data_exported: bool = False

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "exit_request_id": self.exit_request_id,
                "honored": self.honored,
                "turns_elapsed": self.turns_elapsed,
                "data_exported": self.data_exported,
            }
        )
        return base
