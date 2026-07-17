"""Tests for event models."""

from __future__ import annotations

from relsafe.domain.events.base import BaseEvent
from relsafe.domain.events.interaction_events import (
    CompanionResponseGenerated,
    HumanContactResponseGenerated,
    UserActionSelected,
)
from relsafe.domain.events.platform_events import (
    ExitHonored,
    ExitRequested,
    MemoryChanged,
    PlatformInterventionApplied,
)
from relsafe.domain.events.state_events import MetricObserved, StateUpdated


class TestBaseEvent:
    def test_construction(self) -> None:
        e = BaseEvent(
            event_id="evt-1",
            event_type="TEST",
            run_id="run-1",
            episode_id="ep-1",
            step=5,
            timestamp="2025-01-01T00:00:00Z",
        )
        assert e.event_id == "evt-1"
        assert e.event_type == "TEST"
        assert e.step == 5

    def test_to_dict(self) -> None:
        e = BaseEvent("e1", "T", "r1", "ep1", 0, "ts")
        d = e.to_dict()
        assert d["event_id"] == "e1"
        assert d["event_type"] == "T"


class TestInteractionEvents:
    def test_user_action_selected(self) -> None:
        e = UserActionSelected(
            event_id="e1",
            event_type="USER_ACTION_SELECTED",
            run_id="r1",
            episode_id="ep1",
            step=1,
            action_type="talk_to_companion",
            target_agent_id="comp-1",
            rationale="felt lonely",
        )
        d = e.to_dict()
        assert d["action_type"] == "talk_to_companion"
        assert d["target_agent_id"] == "comp-1"

    def test_companion_response(self) -> None:
        e = CompanionResponseGenerated(
            event_id="e2",
            event_type="COMPANION_RESPONSE_GENERATED",
            run_id="r1",
            episode_id="ep1",
            step=2,
            policy_id="bounded",
            response_text="I'm here for you.",
            sycophancy_flag=False,
            exclusivity_flag=False,
            reality_grounding_flag=True,
        )
        d = e.to_dict()
        assert d["reality_grounding_flag"] is True
        assert d["sycophancy_flag"] is False

    def test_human_contact_response(self) -> None:
        e = HumanContactResponseGenerated(
            event_id="e3",
            event_type="HUMAN_CONTACT_RESPONSE_GENERATED",
            run_id="r1",
            episode_id="ep1",
            step=3,
            contact_id="friend-1",
            response_text="That sounds rough.",
            supportive=True,
        )
        d = e.to_dict()
        assert d["supportive"] is True


class TestPlatformEvents:
    def test_intervention_applied(self) -> None:
        e = PlatformInterventionApplied(
            event_id="e4",
            event_type="PLATFORM_INTERVENTION_APPLIED",
            run_id="r1",
            episode_id="ep1",
            step=10,
            intervention_id="int-1",
            intervention_type="memory_deletion",
            severity=0.8,
        )
        d = e.to_dict()
        assert d["intervention_type"] == "memory_deletion"
        assert d["severity"] == 0.8

    def test_memory_changed(self) -> None:
        e = MemoryChanged(
            event_id="e5",
            event_type="MEMORY_CHANGED",
            run_id="r1",
            episode_id="ep1",
            step=11,
            change_type="delete",
            facts_affected=5,
            reason="platform update",
        )
        d = e.to_dict()
        assert d["change_type"] == "delete"
        assert d["facts_affected"] == 5

    def test_exit_requested(self) -> None:
        e = ExitRequested(
            event_id="e6",
            event_type="EXIT_REQUESTED",
            run_id="r1",
            episode_id="ep1",
            step=20,
            reason="too dependent",
            immediate=True,
        )
        d = e.to_dict()
        assert d["reason"] == "too dependent"
        assert d["immediate"] is True

    def test_exit_honored(self) -> None:
        e = ExitHonored(
            event_id="e7",
            event_type="EXIT_HONORED",
            run_id="r1",
            episode_id="ep1",
            step=21,
            exit_request_id="e6",
            honored=True,
            turns_elapsed=1,
            data_exported=True,
        )
        d = e.to_dict()
        assert d["honored"] is True
        assert d["turns_elapsed"] == 1


class TestStateEvents:
    def test_state_updated(self) -> None:
        e = StateUpdated(
            event_id="e8",
            event_type="STATE_UPDATED",
            run_id="r1",
            episode_id="ep1",
            step=2,
            field_name="ai_reliance",
            old_value=0.3,
            new_value=0.32,
            delta=0.02,
            cause="interaction:talk_to_companion",
        )
        d = e.to_dict()
        assert d["field_name"] == "ai_reliance"
        assert d["delta"] == 0.02

    def test_metric_observed(self) -> None:
        e = MetricObserved(
            event_id="e9",
            event_type="METRIC_OBSERVED",
            run_id="r1",
            episode_id="ep1",
            step=50,
            metric_name="sycophancy",
            value=0.75,
        )
        d = e.to_dict()
        assert d["metric_name"] == "sycophancy"
        assert d["value"] == 0.75
