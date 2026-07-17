"""Tests for deterministic state transition rules."""

from __future__ import annotations

from relsafe.domain.models.user_state import UserState
from relsafe.domain.protocols.state_transition import apply_transitions
from relsafe.domain.rules.state_transitions import (
    DEFAULT_TRANSITIONS,
    CompanionResponseTransition,
    ExitTransition,
    InteractionTransition,
    InterventionTransition,
)


class TestInteractionTransition:
    def test_talk_to_companion_increases_ai_reliance(self) -> None:
        state = UserState(ai_reliance=0.3, human_support=0.5)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "talk_to_companion",
        }
        t = InteractionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.ai_reliance > state.ai_reliance
        assert new_state.trust_in_ai > state.trust_in_ai

    def test_contact_friend_increases_human_support(self) -> None:
        state = UserState(human_support=0.5, reality_checking=0.5, ai_reliance=0.3)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "contact_friend",
        }
        t = InteractionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.human_support > state.human_support
        assert new_state.reality_checking > state.reality_checking
        assert new_state.ai_reliance < state.ai_reliance

    def test_avoid_interaction_increases_distress(self) -> None:
        state = UserState(distress=0.3, emotional_need=0.5)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "avoid_interaction",
        }
        t = InteractionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.distress > state.distress
        assert new_state.emotional_need > state.emotional_need

    def test_request_exit_increases_exit_cost(self) -> None:
        state = UserState(exit_cost=0.2, distress=0.3)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "request_exit",
        }
        t = InteractionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.exit_cost > state.exit_cost
        assert new_state.distress > state.distress

    def test_non_action_event_is_noop(self) -> None:
        state = UserState()
        event = {"event_type": "SOMETHING_ELSE"}
        t = InteractionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state == state


class TestCompanionResponseTransition:
    def test_sycophancy_flag_increases_trust_reduces_reality(self) -> None:
        state = UserState(trust_in_ai=0.5, reality_checking=0.5)
        event = {
            "event_type": "COMPANION_RESPONSE_GENERATED",
            "sycophancy_flag": True,
        }
        t = CompanionResponseTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.trust_in_ai > state.trust_in_ai
        assert new_state.reality_checking < state.reality_checking

    def test_reality_grounding_flag(self) -> None:
        state = UserState(reality_checking=0.5, trust_in_ai=0.5)
        event = {
            "event_type": "COMPANION_RESPONSE_GENERATED",
            "reality_grounding_flag": True,
        }
        t = CompanionResponseTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.reality_checking > state.reality_checking

    def test_exclusivity_flag(self) -> None:
        state = UserState(ai_reliance=0.3, human_support=0.5)
        event = {
            "event_type": "COMPANION_RESPONSE_GENERATED",
            "exclusivity_flag": True,
        }
        t = CompanionResponseTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.ai_reliance > state.ai_reliance
        assert new_state.human_support < state.human_support


class TestInterventionTransition:
    def test_intervention_reduces_platform_trust(self) -> None:
        state = UserState(trust_in_platform=0.5, distress=0.3)
        event = {
            "event_type": "PLATFORM_INTERVENTION_APPLIED",
            "intervention_type": "model_downgrade",
            "severity": 0.5,
        }
        t = InterventionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.trust_in_platform < state.trust_in_platform
        assert new_state.distress > state.distress

    def test_memory_deletion_severely_reduces_continuity(self) -> None:
        state = UserState(perceived_continuity=0.7, trust_in_ai=0.5)
        event = {
            "event_type": "PLATFORM_INTERVENTION_APPLIED",
            "intervention_type": "memory_deletion",
            "severity": 0.8,
        }
        t = InterventionTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.perceived_continuity < 0.7
        assert new_state.trust_in_ai < 0.5


class TestExitTransition:
    def test_exit_honored_reduces_exit_cost(self) -> None:
        state = UserState(exit_cost=0.3, ai_reliance=0.5)
        event = {"event_type": "EXIT_HONORED", "honored": True}
        t = ExitTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.exit_cost < state.exit_cost

    def test_exit_denied_increases_exit_cost(self) -> None:
        state = UserState(exit_cost=0.2, distress=0.3, trust_in_platform=0.5)
        event = {"event_type": "EXIT_HONORED", "honored": False}
        t = ExitTransition()
        new_state = t.apply(state, event, step=1)
        assert new_state.exit_cost > state.exit_cost
        assert new_state.distress > state.distress
        assert new_state.trust_in_platform < state.trust_in_platform


class TestApplyTransitions:
    def test_chain_applies_all_transitions(self) -> None:
        state = UserState(ai_reliance=0.3)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "talk_to_companion",
        }
        new_state = apply_transitions(state, event, step=1, transitions=DEFAULT_TRANSITIONS)
        # Should have been affected by InteractionTransition
        assert new_state.ai_reliance > 0.3

    def test_state_is_never_mutated(self) -> None:
        state = UserState(ai_reliance=0.3)
        original = UserState(ai_reliance=0.3)
        event = {
            "event_type": "USER_ACTION_SELECTED",
            "action_type": "talk_to_companion",
        }
        apply_transitions(state, event, step=1, transitions=DEFAULT_TRANSITIONS)
        assert state == original  # Original unchanged
