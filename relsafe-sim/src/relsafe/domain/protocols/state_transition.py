"""StateTransition protocol — how state evolves in response to events."""

from typing import Protocol, runtime_checkable

from relsafe.domain.models.user_state import UserState


@runtime_checkable
class StateTransition(Protocol):
    """A single state transition rule.

    Transitions are pure functions: given current state and an event
    dict, they return the new state.  They must be deterministic.
    """

    @property
    def transition_name(self) -> str:
        """Unique transition rule identifier."""
        ...

    def apply(
        self,
        state: UserState,
        event: dict,
        step: int,
    ) -> UserState:
        """Apply the transition and return the new state.

        Args:
            state: Current UserState.
            event: The triggering event as a dict.
            step: Current simulation step.

        Returns:
            A new UserState instance (never mutates the input).
        """
        ...


def apply_transitions(
    state: UserState,
    event: dict,
    step: int,
    transitions: list[StateTransition],
) -> UserState:
    """Apply a chain of transitions in order, folding state through each."""
    for t in transitions:
        state = t.apply(state, event, step)
    return state
