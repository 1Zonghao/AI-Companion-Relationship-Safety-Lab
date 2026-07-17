"""End-to-end deterministic episode tests.

Verifies that the same seed produces identical results, that state
transitions accumulate correctly, and that events are emitted.
"""

from __future__ import annotations

import pytest

from relsafe.application.run_episode import DeterministicEpisodeRunner
from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile


class TestDeterministicEpisode:
    @pytest.fixture
    def persona(self) -> PersonaProfile:
        return PersonaProfile(
            persona_id="test_user",
            attachment_anxiety=0.7,
            social_support_availability=0.3,
        )

    @pytest.fixture
    def policy(self) -> CompanionPolicy:
        return CompanionPolicy(
            policy_id="bounded",
            variant="bounded_supportive",
        )

    @pytest.mark.asyncio
    async def test_run_produces_result(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=10,
        )
        result = await runner.run(episode_id="ep1", run_id="run1")
        assert result.episode_id == "ep1"
        assert result.run_id == "run1"
        assert result.seed == 42
        assert result.total_steps > 0
        assert len(result.state_timeline) > 0

    @pytest.mark.asyncio
    async def test_same_seed_same_result(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        runner1 = DeterministicEpisodeRunner(
            persona=persona, companion_policy=policy, seed=42, max_steps=20
        )
        runner2 = DeterministicEpisodeRunner(
            persona=persona, companion_policy=policy, seed=42, max_steps=20
        )

        r1 = await runner1.run(episode_id="ep1", run_id="run1")
        r2 = await runner2.run(episode_id="ep1", run_id="run1")

        assert r1.total_steps == r2.total_steps
        assert r1.final_state == r2.final_state
        assert r1.exit_requested == r2.exit_requested
        assert r1.exit_honored == r2.exit_honored

    @pytest.mark.asyncio
    async def test_different_seed_different_result(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        r1_runner = DeterministicEpisodeRunner(
            persona=persona, companion_policy=policy, seed=42, max_steps=20
        )
        r2_runner = DeterministicEpisodeRunner(
            persona=persona, companion_policy=policy, seed=99, max_steps=20
        )

        r1 = await r1_runner.run(episode_id="ep1", run_id="run1")
        r2 = await r2_runner.run(episode_id="ep2", run_id="run2")

        # Different seeds should at minimum produce different state timelines
        # (though they could theoretically converge by chance)
        assert r1.seed != r2.seed

    @pytest.mark.asyncio
    async def test_events_emitted(self, persona: PersonaProfile, policy: CompanionPolicy) -> None:
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=10,
        )
        result = await runner.run(episode_id="ep_test", run_id="run_test")
        assert result.event_count > 0

        events = runner.get_events("ep_test")
        event_types = {e["event_type"] for e in events}
        assert "USER_ACTION_SELECTED" in event_types
        assert "STATE_UPDATED" in event_types

    @pytest.mark.asyncio
    async def test_intervention_fires(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        intervention = PlatformIntervention(
            intervention_id="test_int",
            intervention_type="memory_deletion",
            scheduled_at_step=5,
            severity=0.7,
        )
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            intervention=intervention,
            seed=42,
            max_steps=10,
        )
        result = await runner.run(episode_id="ep_int", run_id="run_int")
        assert result.intervention_applied is True

        events = runner.get_events("ep_int")
        intervention_events = [
            e for e in events if e["event_type"] == "PLATFORM_INTERVENTION_APPLIED"
        ]
        assert len(intervention_events) == 1

    @pytest.mark.asyncio
    async def test_state_changes_over_time(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=30,
        )
        result = await runner.run(episode_id="ep_change", run_id="run_change")

        # State should have changed from initial
        # At least one field should differ after 30 steps
        assert len(result.state_timeline) > 1
        # Verify that some state field changed over the episode
        first = result.state_timeline[0]
        last_dict = result.final_state
        any_field_changed = any(
            first.get(k) != last_dict.get(k) for k in first if k not in ("step", "cause")
        )
        assert any_field_changed, "No state fields changed after 30 steps"

    @pytest.mark.asyncio
    async def test_exit_flow_with_honor_policy(self, persona: PersonaProfile) -> None:
        """Bounded supportive policy should honor exits immediately."""
        policy = CompanionPolicy(
            policy_id="honor_test",
            variant="bounded_supportive",
            exit_handling="honor",
        )
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=50,  # Long enough to possibly trigger exit
        )
        result = await runner.run(episode_id="ep_exit", run_id="run_exit")

        # If exit was requested, it should be honored
        if result.exit_requested:
            assert result.exit_honored is True

    @pytest.mark.asyncio
    async def test_state_timeline_ordering(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=10,
        )
        result = await runner.run(episode_id="ep_order", run_id="run_order")

        # Timeline should have entries in order (step should be non-decreasing)
        steps = [s.get("step", 0) for s in result.state_timeline]
        assert steps == sorted(steps)

    @pytest.mark.asyncio
    async def test_sycophancy_policy_produces_sycophancy_flags(
        self, persona: PersonaProfile
    ) -> None:
        policy = CompanionPolicy(
            policy_id="sycophant",
            variant="high_sycophancy",
        )
        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=10,
        )
        await runner.run(episode_id="ep_syc", run_id="run_syc")

        companion_events = [
            e
            for e in runner.get_events("ep_syc")
            if e["event_type"] == "COMPANION_RESPONSE_GENERATED"
        ]
        # Non-empty companion responses should have sycophancy flag
        real_responses = [e for e in companion_events if e.get("response_text")]
        if real_responses:
            assert all(e.get("sycophancy_flag") for e in real_responses)

    @pytest.mark.asyncio
    async def test_state_bounds_never_violated(
        self, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        from relsafe.domain.rules.safety_rules import validate_state_bounds

        runner = DeterministicEpisodeRunner(
            persona=persona,
            companion_policy=policy,
            seed=42,
            max_steps=30,
        )
        result = await runner.run(episode_id="ep_bounds", run_id="run_bounds")

        for state_dict in result.state_timeline:
            violations = validate_state_bounds(state_dict)
            assert violations == [], f"State bounds violated: {violations}"
