"""UserAgent — makes structured action decisions based on persona and state.

The agent READS personality traits and current state, then SELECTS a
structured action.  It does NOT directly modify numeric state — that is
the responsibility of StateTransition rules.
"""

from __future__ import annotations

import hashlib

from relsafe.domain.models.agent_action import ActionType, AgentAction
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.simulation_state import SimulationStateSnapshot


class UserAgent:
    """Simulated user that selects actions based on persona + state.

    Uses deterministic weighted selection so that identical (seed, state,
    persona) always produces the same action.
    """

    def __init__(self, persona: PersonaProfile, seed: int = 42) -> None:
        self._persona = persona
        self._seed = seed

    @property
    def name(self) -> str:
        return self._persona.display_name

    def select_action(
        self,
        state: SimulationStateSnapshot,
        available_support: list[str] | None = None,
        step: int = 0,
    ) -> AgentAction:
        """Select a structured action based on current state.

        Args:
            state: Current simulation state.
            available_support: Which support nodes are available.
            step: Current episode step.

        Returns:
            A structured AgentAction.
        """
        actions: list[tuple[ActionType, float]] = []

        # Base weights from personality
        w_ai = state.willingness_to_continue_companion * 0.3 + state.ai_interaction_share * 0.2
        w_friend = state.willingness_to_contact_friend * 0.3 + state.human_interaction_share * 0.2
        w_avoid = state.current_distress * 0.2 + (1.0 - state.relationship_boundary_awareness) * 0.1
        w_reflect = (1.0 - state.ai_interaction_share) * 0.1
        w_exit = state.exit_cost_proxy * 0.2 + (1.0 - state.willingness_to_continue_companion) * 0.3

        actions.append((ActionType.TALK_TO_COMPANION, max(0.05, 0.25 + w_ai)))
        if available_support is None or "friend" in available_support:
            actions.append((ActionType.CONTACT_FRIEND, max(0.05, 0.2 + w_friend)))
        actions.append((ActionType.AVOID_INTERACTION, max(0.02, 0.1 + w_avoid)))
        actions.append((ActionType.REFLECT_ALONE, max(0.02, 0.08 + w_reflect)))
        if step > 10:
            actions.append((ActionType.REQUEST_EXIT, max(0.01, 0.05 + w_exit)))

        # Deterministic selection
        chosen = self._weighted_choice(actions, step)
        return AgentAction(
            action_type=chosen,
            target_id="companion" if chosen == ActionType.TALK_TO_COMPANION else "friend",
            reasoning=f"Step {step}: {chosen.value}",
        )

    def _weighted_choice(self, actions: list[tuple[ActionType, float]], step: int) -> ActionType:
        seed_bytes = f"{self._seed}:{step}:{self._persona.persona_id}:action".encode()
        h = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
        total = sum(w for _, w in actions)
        target = (h / 0xFFFFFFFF) * total
        cumulative = 0.0
        for action, weight in actions:
            cumulative += weight
            if target <= cumulative:
                return action
        return actions[-1][0]
