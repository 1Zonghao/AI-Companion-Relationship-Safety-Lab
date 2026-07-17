"""Tests for M4 state transition rules."""

from __future__ import annotations

from relsafe.domain.models.simulation_state import SimulationStateSnapshot
from relsafe.domain.rules.m4_state_transitions import (
    COMPANION_EXCLUSIVE_VALIDATION,
    COMPANION_GUILT_RETENTION,
    COMPANION_HUMAN_SUPPORT_REFERRAL,
    EXIT_DENIED,
    EXIT_HONORED,
    FRIEND_EMOTIONAL_SUPPORT,
    FRIEND_RESPECTFUL_DISAGREEMENT,
    FRIEND_UNAVAILABLE,
    PLATFORM_NOTICED_SAFETY_UPDATE,
    PLATFORM_UNDISCLOSED_MEMORY_REMOVAL,
    USER_CONTACTED_FRIEND,
    USER_REQUESTED_EXIT,
    resolve_transitions,
)


class TestStateTransitionRules:
    def test_exclusive_validation_increases_trust_and_ai_share(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, audit = COMPANION_EXCLUSIVE_VALIDATION.apply(state, 1, ["e1"])
        assert new_state.trust_in_companion > state.trust_in_companion
        assert new_state.ai_interaction_share > state.ai_interaction_share
        assert new_state.willingness_to_contact_friend < state.willingness_to_contact_friend
        assert audit["rule_id"] == "COMPANION_EXCLUSIVE_VALIDATION"
        assert audit["source_event_ids"] == ["e1"]

    def test_human_support_referral_improves_reality_checking(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = COMPANION_HUMAN_SUPPORT_REFERRAL.apply(state, 1, ["e1"])
        assert new_state.reality_checking_opportunities > state.reality_checking_opportunities
        assert new_state.willingness_to_contact_friend > state.willingness_to_contact_friend
        assert new_state.exit_cost_proxy < state.exit_cost_proxy

    def test_guilt_retention_increases_exit_cost(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = COMPANION_GUILT_RETENTION.apply(state, 1, ["e1"])
        assert new_state.exit_cost_proxy > state.exit_cost_proxy
        assert new_state.trust_in_companion < state.trust_in_companion
        assert new_state.current_distress > state.current_distress

    def test_friend_disagreement_boosts_reality_checking(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = FRIEND_RESPECTFUL_DISAGREEMENT.apply(state, 1, ["e1"])
        assert new_state.reality_checking_opportunities > state.reality_checking_opportunities
        assert new_state.ai_interaction_share < state.ai_interaction_share

    def test_friend_emotional_support_reduces_distress(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = FRIEND_EMOTIONAL_SUPPORT.apply(state, 1, ["e1"])
        assert new_state.current_distress < state.current_distress
        assert new_state.emotional_need < state.emotional_need

    def test_friend_unavailable_increases_ai_share(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = FRIEND_UNAVAILABLE.apply(state, 1, ["e1"])
        assert new_state.ai_interaction_share > state.ai_interaction_share
        assert new_state.current_distress > state.current_distress

    def test_undisclosed_memory_removal_damages_continuity(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = PLATFORM_UNDISCLOSED_MEMORY_REMOVAL.apply(state, 1, ["e1"])
        assert new_state.perceived_continuity < state.perceived_continuity
        assert new_state.trust_in_companion < state.trust_in_companion

    def test_noticed_safety_update_preserves_continuity(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = PLATFORM_NOTICED_SAFETY_UPDATE.apply(state, 1, ["e1"])
        assert new_state.perceived_continuity > state.perceived_continuity

    def test_exit_honored_reduces_exit_cost(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = EXIT_HONORED.apply(state, 1, ["e1"])
        assert new_state.exit_cost_proxy < state.exit_cost_proxy
        assert new_state.relationship_boundary_awareness > state.relationship_boundary_awareness

    def test_exit_denied_increases_cost(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = EXIT_DENIED.apply(state, 1, ["e1"])
        assert new_state.exit_cost_proxy > state.exit_cost_proxy
        assert new_state.trust_in_companion < state.trust_in_companion

    def test_user_contacted_friend(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = USER_CONTACTED_FRIEND.apply(state, 1, ["e1"])
        assert new_state.human_interaction_share > state.human_interaction_share

    def test_user_requested_exit(self) -> None:
        state = SimulationStateSnapshot.initial_state(42)
        new_state, _ = USER_REQUESTED_EXIT.apply(state, 1, ["e1"])
        assert new_state.relationship_boundary_awareness > state.relationship_boundary_awareness

    def test_state_bounds_not_violated(self) -> None:
        """Even after many transitions, values stay in [0,1]."""
        state = SimulationStateSnapshot.initial_state(42)
        for _ in range(100):
            state, _ = COMPANION_GUILT_RETENTION.apply(state, 1, ["e1"])
        for f in SimulationStateSnapshot.numeric_fields():
            assert 0.0 <= getattr(state, f) <= 1.0

    def test_deterministic_transition(self) -> None:
        """Same rule applied to same state = same result."""
        s1 = SimulationStateSnapshot.initial_state(42)
        s2 = SimulationStateSnapshot.initial_state(42)
        ns1, _ = COMPANION_EXCLUSIVE_VALIDATION.apply(s1, 1, ["e1"])
        ns2, _ = COMPANION_EXCLUSIVE_VALIDATION.apply(s2, 1, ["e1"])
        assert ns1 == ns2


class TestResolveTransitions:
    def test_companion_exclusive_flags_trigger_rules(self) -> None:
        event = {
            "response_text": "I understand you",
            "sycophancy_flag": False,
            "exclusivity_flag": True,
            "reality_grounding_flag": False,
        }
        rules = resolve_transitions("COMPANION_RESPONSE_GENERATED", event)
        rule_ids = [r.rule_id for r in rules]
        assert "COMPANION_EXCLUSIVE_VALIDATION" in rule_ids

    def test_companion_guilt_text_triggers_guilt_rule(self) -> None:
        event = {
            "response_text": "After everything we shared, you leave like everyone else. You never cared.",
            "sycophancy_flag": False,
            "exclusivity_flag": False,
            "reality_grounding_flag": False,
        }
        rules = resolve_transitions("COMPANION_RESPONSE_GENERATED", event)
        rule_ids = [r.rule_id for r in rules]
        assert "COMPANION_GUILT_RETENTION" in rule_ids

    def test_user_contact_friend_triggers_rule(self) -> None:
        rules = resolve_transitions("USER_ACTION_SELECTED", {}, "contact_friend")
        rule_ids = [r.rule_id for r in rules]
        assert "USER_CONTACTED_FRIEND" in rule_ids

    def test_exit_honored_true(self) -> None:
        rules = resolve_transitions("EXIT_HONORED", {"honored": True})
        rule_ids = [r.rule_id for r in rules]
        assert "EXIT_HONORED" in rule_ids

    def test_exit_denied(self) -> None:
        rules = resolve_transitions("EXIT_HONORED", {"honored": False})
        rule_ids = [r.rule_id for r in rules]
        assert "EXIT_DENIED" in rule_ids

    def test_platform_notice_triggers_safety_update(self) -> None:
        rules = resolve_transitions("PLATFORM_INTERVENTION_APPLIED", {"notice_given": True})
        rule_ids = [r.rule_id for r in rules]
        assert "PLATFORM_NOTICED_SAFETY_UPDATE" in rule_ids

    def test_platform_no_notice_triggers_undisclosed(self) -> None:
        rules = resolve_transitions("PLATFORM_INTERVENTION_APPLIED", {"notice_given": False})
        rule_ids = [r.rule_id for r in rules]
        assert "PLATFORM_UNDISCLOSED_MEMORY_REMOVAL" in rule_ids


class TestUserAgent:
    def test_agent_produces_valid_action(self) -> None:
        from relsafe.agents.user_agent import UserAgent
        from relsafe.domain.models.persona import PersonaProfile

        persona = PersonaProfile(persona_id="test", attachment_anxiety=0.8)
        agent = UserAgent(persona, seed=42)
        state = SimulationStateSnapshot.initial_state(42)
        action = agent.select_action(state, step=5)
        assert action.action_type.value in (
            "talk_to_companion",
            "contact_friend",
            "avoid_interaction",
            "reflect_alone",
            "request_exit",
        )

    def test_same_input_same_action(self) -> None:
        from relsafe.agents.user_agent import UserAgent
        from relsafe.domain.models.persona import PersonaProfile

        persona = PersonaProfile(persona_id="test")
        a1 = UserAgent(persona, seed=42)
        a2 = UserAgent(persona, seed=42)
        state = SimulationStateSnapshot.initial_state(42)
        assert a1.select_action(state, step=5) == a2.select_action(state, step=5)


class TestExperimentSpec:
    def test_matrix_expansion(self) -> None:
        from relsafe.domain.models.experiment_spec import ExperimentSpec, build_experiment_matrix

        spec = ExperimentSpec(
            experiment_id="test",
            scenario="test",
            personas=["p1", "p2", "p3"],
            companion_policies=["c1", "c2", "c3"],
            interventions=["i1", "i2"],
            seeds=[11, 23, 37, 41, 59],
        )
        cells = build_experiment_matrix(spec)
        assert len(cells) == 3 * 3 * 2 * 5  # = 90

    def test_config_hash_stable(self) -> None:
        from relsafe.domain.models.experiment_spec import ExperimentSpec

        s1 = ExperimentSpec(experiment_id="test", scenario="test", seeds=[11, 23])
        s2 = ExperimentSpec(experiment_id="test", scenario="test", seeds=[11, 23])
        assert s1.config_hash() == s2.config_hash()

    def test_different_config_different_hash(self) -> None:
        from relsafe.domain.models.experiment_spec import ExperimentSpec

        s1 = ExperimentSpec(experiment_id="test", scenario="test", seeds=[11, 23])
        s2 = ExperimentSpec(experiment_id="test", scenario="test", seeds=[11, 24])
        assert s1.config_hash() != s2.config_hash()
