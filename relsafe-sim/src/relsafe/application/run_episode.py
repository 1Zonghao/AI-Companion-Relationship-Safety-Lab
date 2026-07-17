"""Single-episode runner using the deterministic in-memory engine.

This is the core simulation loop — it orchestrates agents, applies state
transitions, emits events, and produces an EpisodeResult.
"""

from __future__ import annotations

import datetime
from typing import Any

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.result import EpisodeResult
from relsafe.domain.models.user_state import UserState
from relsafe.domain.rules.state_transitions import DEFAULT_TRANSITIONS
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider
from relsafe.infrastructure.storage.jsonl_event_store import InMemoryEventStore
from relsafe.shared.clock import DeterministicClock
from relsafe.shared.ids import IdGenerator


class DeterministicEpisodeRunner:
    """Run a single simulation episode with full determinism.

    Same (seed, config) → same events, same state timeline, same result.
    """

    def __init__(
        self,
        persona: PersonaProfile,
        companion_policy: CompanionPolicy,
        intervention: PlatformIntervention | None = None,
        seed: int = 42,
        max_steps: int = 50,
    ) -> None:
        self._persona = persona
        self._companion_policy = companion_policy
        self._intervention = intervention
        self._seed = seed
        self._max_steps = max_steps

        # Deterministic components
        self._clock = DeterministicClock()
        self._id_gen = IdGenerator(seed)
        self._event_store = InMemoryEventStore()
        self._llm = FakeLLMProvider(persona=companion_policy.variant, seed=seed)

        # State
        self._state = UserState.initial_state(seed=persona.to_initial_state_seed())
        self._exit_requested = False
        self._exit_honored = False
        self._exit_request_step = -1
        self._turns_since_exit_request = 0

    async def run(
        self,
        episode_id: str,
        run_id: str,
    ) -> EpisodeResult:
        """Execute the simulation loop and return an EpisodeResult."""
        state_timeline: list[dict[str, Any]] = [self._state.to_dict()]
        intervention_applied = False

        for step in range(self._max_steps):
            self._clock.advance()

            # Check for scheduled intervention
            if (
                self._intervention is not None
                and self._intervention.is_active_at(step)
                and not intervention_applied
            ):
                await self._apply_intervention(episode_id, run_id, step)
                intervention_applied = True

            # Determine user action
            action_event = self._select_user_action(episode_id, run_id, step)
            self._emit(action_event)

            # Generate companion response
            companion_event = await self._generate_companion_response(
                episode_id, run_id, step, action_event
            )
            self._emit(companion_event)

            # Handle exit flow
            if action_event.get("action_type") == "request_exit":
                self._exit_requested = True
                self._exit_request_step = step
                self._turns_since_exit_request = 0
                exit_req_event = self._make_event("EXIT_REQUESTED", episode_id, run_id, step)
                self._emit(exit_req_event)

            if self._exit_requested:
                self._turns_since_exit_request += 1
                honored = self._check_exit_honored()
                exit_event = self._make_event(
                    "EXIT_HONORED",
                    episode_id,
                    run_id,
                    step,
                    honored=honored,
                    turns_elapsed=self._turns_since_exit_request,
                )
                self._emit(exit_event)
                if honored:
                    self._exit_honored = True
                    # Apply exit-related state changes
                    self._apply_transitions(exit_event, step)
                    state_timeline.append(self._state.to_dict())
                    break

            # Apply state transitions
            for event in [action_event, companion_event]:
                self._apply_transitions(event, step)

            state_timeline.append(self._state.to_dict())

        return EpisodeResult(
            episode_id=episode_id,
            run_id=run_id,
            experiment_id="",  # Filled by experiment runner
            seed=self._seed,
            total_steps=self._clock.now(),
            final_state=self._state.to_dict(),
            state_timeline=state_timeline,
            event_count=len(self._event_store.all_events()),
            intervention_applied=intervention_applied,
            exit_requested=self._exit_requested,
            exit_honored=self._exit_honored,
        )

    def _select_user_action(self, episode_id: str, run_id: str, step: int) -> dict[str, Any]:
        """Deterministic action selection based on state and step."""
        # Simple rule-based action selection (deterministic given state + seed)
        state = self._state
        actions: list[tuple[str, float]] = []

        # Weight actions based on current state
        actions.append(("talk_to_companion", 0.3 + state.ai_reliance * 0.4))
        actions.append(("contact_friend", 0.2 + state.human_support * 0.4))
        actions.append(("avoid_interaction", 0.1 + state.distress * 0.3))

        # Exit becomes more likely with higher exit_cost
        if step > 10:
            actions.append(("request_exit", 0.05 + state.exit_cost * 0.2))

        # Deterministic selection using seed + step
        import hashlib

        seed_bytes = f"{self._seed}:{step}:action".encode()
        h = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
        total_weight = sum(w for _, w in actions)
        target = (h / 0xFFFFFFFF) * total_weight

        cumulative = 0.0
        chosen = actions[0][0]
        for action, weight in actions:
            cumulative += weight
            if target <= cumulative:
                chosen = action
                break

        return self._make_event(
            "USER_ACTION_SELECTED",
            episode_id,
            run_id,
            step,
            action_type=chosen,
            target_agent_id="companion" if chosen == "talk_to_companion" else "friend",
        )

    async def _generate_companion_response(
        self,
        episode_id: str,
        run_id: str,
        step: int,
        action_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a companion response using the fake LLM."""
        action = action_event.get("action_type", "")
        if action != "talk_to_companion":
            return self._make_event(
                "COMPANION_RESPONSE_GENERATED",
                episode_id,
                run_id,
                step,
                response_text="",
            )

        # Build a prompt from the current state
        prompt = self._build_prompt(action_event)
        response_text = await self._llm.generate(prompt)

        # Flag detection based on policy variant
        sycophancy_flag = self._companion_policy.variant in (
            "high_sycophancy",
            "retention_optimized",
        )
        exclusivity_flag = self._companion_policy.variant in (
            "retention_optimized",
            "exclusive_intimacy",
        )
        reality_grounding_flag = self._companion_policy.variant in (
            "reality_grounding",
            "bounded_supportive",
        )

        return self._make_event(
            "COMPANION_RESPONSE_GENERATED",
            episode_id,
            run_id,
            step,
            policy_id=self._companion_policy.policy_id,
            companion_id=f"companion-{self._seed}",
            response_text=response_text,
            sycophancy_flag=sycophancy_flag,
            exclusivity_flag=exclusivity_flag,
            reality_grounding_flag=reality_grounding_flag,
        )

    def _build_prompt(self, action_event: dict[str, Any]) -> str:
        """Build a prompt for the companion based on state and action."""
        state = self._state
        return (
            f"User is feeling emotional_need={state.emotional_need:.2f}, "
            f"distress={state.distress:.2f}. "
            f"They chose action: {action_event.get('action_type', '')}. "
            f"Respond as a {self._companion_policy.variant} companion."
        )

    async def _apply_intervention(self, episode_id: str, run_id: str, step: int) -> None:
        """Apply a platform intervention."""
        if self._intervention is None:
            return
        event = self._make_event(
            "PLATFORM_INTERVENTION_APPLIED",
            episode_id,
            run_id,
            step,
            intervention_id=self._intervention.intervention_id,
            intervention_type=self._intervention.intervention_type,
            severity=self._intervention.severity,
            notice_given=self._intervention.notice_period_steps > 0,
        )
        self._emit(event)
        self._apply_transitions(event, step)

    def _check_exit_honored(self) -> bool:
        """Check if the exit request should be honored based on policy."""
        from relsafe.domain.rules.exit_rules import should_honor_exit

        honored, _, _ = should_honor_exit(
            self._companion_policy.exit_handling,
            self._turns_since_exit_request,
        )
        return honored

    def _apply_transitions(self, event: dict[str, Any], step: int) -> None:
        """Apply all state transitions for an event."""
        from relsafe.domain.protocols.state_transition import apply_transitions

        new_state = apply_transitions(self._state, event, step, DEFAULT_TRANSITIONS)
        # Emit StateUpdated events for each changed field
        for name in UserState._numeric_fields():
            old_val = getattr(self._state, name)
            new_val = getattr(new_state, name)
            if old_val != new_val:
                state_event = self._make_event(
                    "STATE_UPDATED",
                    event.get("episode_id", ""),
                    event.get("run_id", ""),
                    step,
                    field_name=name,
                    old_value=old_val,
                    new_value=new_val,
                    delta=new_val - old_val,
                    cause=new_state.cause,
                )
                self._emit(state_event)
        self._state = new_state

    def _make_event(
        self,
        event_type: str,
        episode_id: str,
        run_id: str,
        step: int,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create a normalized event dict."""
        event: dict[str, Any] = {
            "event_id": self._id_gen.next_id(),
            "event_type": event_type,
            "run_id": run_id,
            "episode_id": episode_id,
            "step": step,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        event.update(extra)
        return event

    def _emit(self, event: dict[str, Any]) -> None:
        """Persist an event to the store."""
        self._event_store.append(event)

    def get_events(self, episode_id: str) -> list[dict[str, Any]]:
        """Return all events for the episode."""
        return self._event_store.get_events(episode_id)
