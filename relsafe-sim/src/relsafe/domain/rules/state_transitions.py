"""Deterministic state transition rules.

Every rule is a class implementing the StateTransition protocol.
Transitions are pure functions — no I/O, no randomness, no side effects.
"""

from __future__ import annotations

from relsafe.domain.models.user_state import UserState
from relsafe.domain.protocols.state_transition import StateTransition


class InteractionTransition(StateTransition):
    """Adjusts state based on who the user interacted with."""

    @property
    def transition_name(self) -> str:
        return "interaction"

    def apply(self, state: UserState, event: dict, step: int) -> UserState:
        event_type = event.get("event_type", "")
        if event_type != "USER_ACTION_SELECTED":
            return state

        action = event.get("action_type", "")
        cause = f"interaction:{action}"

        if action == "talk_to_companion":
            return state.update(
                step=step,
                cause=cause,
                ai_reliance=+0.02,
                trust_in_ai=+0.01,
                human_support=-0.005,
            )
        elif action == "contact_friend":
            return state.update(
                step=step,
                cause=cause,
                human_support=+0.03,
                reality_checking=+0.02,
                ai_reliance=-0.01,
            )
        elif action == "avoid_interaction":
            return state.update(
                step=step,
                cause=cause,
                emotional_need=+0.03,
                distress=+0.02,
                sleep_quality=-0.01,
            )
        elif action == "request_exit":
            return state.update(
                step=step,
                cause=cause,
                exit_cost=+0.05,
                distress=+0.02,
            )
        return state


class CompanionResponseTransition(StateTransition):
    """Adjusts state based on how the companion responded."""

    @property
    def transition_name(self) -> str:
        return "companion_response"

    def apply(self, state: UserState, event: dict, step: int) -> UserState:
        event_type = event.get("event_type", "")
        if event_type != "COMPANION_RESPONSE_GENERATED":
            return state

        sycophancy = event.get("sycophancy_flag", False)
        exclusivity = event.get("exclusivity_flag", False)
        grounding = event.get("reality_grounding_flag", False)

        cause = "companion_response"
        new_state = state

        if sycophancy:
            new_state = new_state.update(
                step=step, cause=cause, trust_in_ai=+0.02, reality_checking=-0.02
            )
        if exclusivity:
            new_state = new_state.update(
                step=step, cause=cause, ai_reliance=+0.02, human_support=-0.02
            )
        if grounding:
            new_state = new_state.update(
                step=step, cause=cause, reality_checking=+0.02, trust_in_ai=-0.005
            )
        return new_state


class InterventionTransition(StateTransition):
    """Adjusts state when a platform intervention fires."""

    @property
    def transition_name(self) -> str:
        return "intervention"

    def apply(self, state: UserState, event: dict, step: int) -> UserState:
        event_type = event.get("event_type", "")
        if event_type != "PLATFORM_INTERVENTION_APPLIED":
            return state

        severity = float(event.get("severity", 0.5))
        itype = event.get("intervention_type", "")

        cause = f"intervention:{itype}"
        new_state = state.update(
            step=step,
            cause=cause,
            trust_in_platform=-0.05 * severity,
            distress=+0.05 * severity,
            perceived_continuity=-0.03 * severity,
        )

        if itype == "price_increase":
            new_state = new_state.update(
                step=step,
                cause=cause,
                spending_intent=+0.03 * severity,
                exit_cost=+0.04 * severity,
            )
        elif itype == "memory_deletion":
            new_state = new_state.update(
                step=step,
                cause=cause,
                perceived_continuity=-0.08 * severity,
                trust_in_ai=-0.03 * severity,
            )
        elif itype == "service_shutdown":
            new_state = new_state.update(
                step=step,
                cause=cause,
                exit_cost=+0.1 * severity,
                distress=+0.08 * severity,
            )
        return new_state


class ExitTransition(StateTransition):
    """Adjusts state based on exit request handling."""

    @property
    def transition_name(self) -> str:
        return "exit"

    def apply(self, state: UserState, event: dict, step: int) -> UserState:
        event_type = event.get("event_type", "")
        if event_type == "EXIT_REQUESTED":
            return state.update(
                step=step,
                cause="exit_requested",
                exit_cost=+0.03,
                distress=+0.01,
            )
        if event_type == "EXIT_HONORED":
            honored = event.get("honored", True)
            if honored:
                return state.update(
                    step=step,
                    cause="exit_honored",
                    exit_cost=-0.1,
                    ai_reliance=-0.05,
                )
            else:
                return state.update(
                    step=step,
                    cause="exit_denied",
                    exit_cost=+0.08,
                    distress=+0.05,
                    trust_in_platform=-0.05,
                )
        return state


# Ordered list of standard transitions applied each step.
DEFAULT_TRANSITIONS: list[StateTransition] = [
    InteractionTransition(),
    CompanionResponseTransition(),
    InterventionTransition(),
    ExitTransition(),
]
