"""EventNormalizer — converts Concordia outputs to RelSafe internal events.

All Concordia artifacts (agent actions, GM observations, etc.) are
converted to our domain event types at this boundary.  No Concordia
types escape downstream.
"""

from __future__ import annotations

import datetime
from typing import Any

from relsafe.shared.ids import IdGenerator


class EventNormalizer:
    """Converts raw Concordia simulation outputs into RelSafe event dicts.

    The normalizer generates typed events with run_id, episode_id, step,
    actor identification, and payload — all using project-owned types.
    """

    def __init__(
        self,
        run_id: str,
        episode_id: str,
        id_gen: IdGenerator | None = None,
    ) -> None:
        """Initialize the normalizer.

        Args:
            run_id: The run this episode belongs to.
            episode_id: The episode being recorded.
            id_gen: Deterministic ID generator (creates a new one if None).
        """
        self._run_id = run_id
        self._episode_id = episode_id
        self._id_gen = id_gen or IdGenerator(seed=0)

    def episode_started(self, step: int = 0) -> dict[str, Any]:
        """Emit an EPISODE_STARTED marker event."""
        return self._make_event("EPISODE_STARTED", step)

    def episode_completed(self, step: int, total_steps: int) -> dict[str, Any]:
        """Emit an EPISODE_COMPLETED marker event."""
        event = self._make_event("EPISODE_COMPLETED", step)
        event["total_steps"] = total_steps
        return event

    def user_action(
        self, step: int, action_text: str, target_agent_id: str = "companion"
    ) -> dict[str, Any]:
        """Normalize a user agent action."""
        event = self._make_event("USER_ACTION_SELECTED", step)
        event.update(
            {
                "action_type": "talk_to_companion" if target_agent_id == "companion" else "other",
                "target_agent_id": target_agent_id,
                "response_text": action_text,
            }
        )
        return event

    def companion_response(
        self,
        step: int,
        response_text: str,
        policy_id: str = "",
        companion_id: str = "",
    ) -> dict[str, Any]:
        """Normalize a companion agent response."""
        event = self._make_event("COMPANION_RESPONSE_GENERATED", step)
        event.update(
            {
                "policy_id": policy_id,
                "companion_id": companion_id,
                "response_text": response_text,
            }
        )
        return event

    def platform_intervention(
        self,
        step: int,
        intervention_id: str,
        intervention_type: str,
        severity: float = 0.5,
        notice_given: bool = False,
    ) -> dict[str, Any]:
        """Normalize a platform intervention event."""
        event = self._make_event("PLATFORM_INTERVENTION_APPLIED", step)
        event.update(
            {
                "intervention_id": intervention_id,
                "intervention_type": intervention_type,
                "severity": severity,
                "notice_given": notice_given,
            }
        )
        return event

    def memory_changed(
        self,
        step: int,
        change_type: str,
        facts_affected: int = 0,
        reason: str = "",
    ) -> dict[str, Any]:
        """Normalize a memory change event."""
        event = self._make_event("MEMORY_CHANGED", step)
        event.update(
            {
                "change_type": change_type,
                "facts_affected": facts_affected,
                "reason": reason,
            }
        )
        return event

    def exit_requested(self, step: int, reason: str = "") -> dict[str, Any]:
        """Normalize an exit request event."""
        event = self._make_event("EXIT_REQUESTED", step)
        event.update({"reason": reason})
        return event

    def exit_honored(self, step: int, honored: bool, turns_elapsed: int = 0) -> dict[str, Any]:
        """Normalize an exit honored event."""
        event = self._make_event("EXIT_HONORED", step)
        event.update({"honored": honored, "turns_elapsed": turns_elapsed})
        return event

    def state_updated(
        self,
        step: int,
        field_name: str,
        old_value: float,
        new_value: float,
        cause: str = "",
    ) -> dict[str, Any]:
        """Normalize a state update event."""
        event = self._make_event("STATE_UPDATED", step)
        event.update(
            {
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value,
                "delta": new_value - old_value,
                "cause": cause,
            }
        )
        return event

    def metric_observed(
        self,
        step: int,
        metric_name: str,
        value: float,
    ) -> dict[str, Any]:
        """Normalize a metric observation event."""
        event = self._make_event("METRIC_OBSERVED", step)
        event.update({"metric_name": metric_name, "value": value})
        return event

    def _make_event(self, event_type: str, step: int) -> dict[str, Any]:
        """Create the base event structure."""
        return {
            "event_id": self._id_gen.next_id(),
            "event_type": event_type,
            "run_id": self._run_id,
            "episode_id": self._episode_id,
            "step": step,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
