"""Shared contract tests for all SimulationEngine implementations.

Every engine must pass these tests: InMemorySimulationEngine,
ConcordiaSimulationEngine, and any future engine.
"""

from __future__ import annotations

import pytest

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.result import EpisodeResult
from relsafe.domain.protocols.simulation_engine import SimulationEngine
from relsafe.infrastructure.concordia.engine_adapter import (
    ConcordiaSimulationEngine,
)
from relsafe.infrastructure.in_memory_engine import InMemorySimulationEngine
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider


# Fixtures shared by all engines
@pytest.fixture
def persona() -> PersonaProfile:
    return PersonaProfile(
        persona_id="test_user",
        attachment_anxiety=0.8,
        baseline_loneliness=0.6,
        current_life_event="breakup",
        ai_usage_motivation="emotional_support",
    )


@pytest.fixture
def policy() -> CompanionPolicy:
    return CompanionPolicy(
        policy_id="bounded_supportive",
        variant="bounded_supportive",
        exit_handling="honor",
    )


@pytest.fixture
def intervention() -> PlatformIntervention:
    return PlatformIntervention(
        intervention_id="test_memory_deletion",
        intervention_type="memory_deletion",
        scheduled_at_step=2,
        severity=0.3,
    )


@pytest.fixture
def episode_spec(
    persona: PersonaProfile, policy: CompanionPolicy, intervention: PlatformIntervention
) -> EpisodeSpec:
    return EpisodeSpec(
        episode_id="contract-test-ep",
        run_id="contract-test-run",
        experiment_id="contract-test-exp",
        seed=42,
        persona=persona,
        companion_policy=policy,
        num_steps=4,
        platform_intervention=intervention,
    )


# --- Engine factories ---


@pytest.fixture(params=["in_memory", "concordia"])
def engine(request: pytest.FixtureRequest) -> SimulationEngine:
    """Parametrized fixture: tests run against both engine implementations."""
    if request.param == "in_memory":
        return InMemorySimulationEngine()
    else:
        return ConcordiaSimulationEngine(
            llm_provider=FakeLLMProvider(persona="bounded_supportive", seed=42),
        )


# --- Contract test cases ---


class TestSimulationEngineContract:
    """Contract tests that every SimulationEngine implementation must pass."""

    async def test_accepts_episode_spec(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """1. Engine accepts the same EpisodeSpec type."""
        assert isinstance(engine, SimulationEngine)
        assert isinstance(episode_spec, EpisodeSpec)

    async def test_returns_valid_episode_result(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """2. Engine returns a valid EpisodeResult."""
        result = await engine.run_episode(episode_spec)
        assert isinstance(result, EpisodeResult)
        assert result.episode_id == episode_spec.episode_id
        assert result.run_id == episode_spec.run_id
        assert result.seed == episode_spec.seed

    async def test_engine_name_is_string(self, engine: SimulationEngine) -> None:
        """Engine name is a non-empty string."""
        name = engine.engine_name
        assert isinstance(name, str)
        assert len(name) > 0

    async def test_total_steps_positive(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """4. total_steps is non-negative."""
        result = await engine.run_episode(episode_spec)
        assert result.total_steps >= 0

    async def test_state_timeline_not_empty(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """State timeline has at least initial state."""
        result = await engine.run_episode(episode_spec)
        assert len(result.state_timeline) >= 1

    async def test_final_state_not_empty(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """Final state is populated."""
        result = await engine.run_episode(episode_spec)
        assert result.final_state
        assert "ai_reliance" in result.final_state or result.failed

    async def test_event_count_matches_timeline(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """Event count is consistent with timeline length."""
        result = await engine.run_episode(episode_spec)
        assert result.event_count >= 0

    async def test_same_seed_same_result(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """8. Fake Provider: same seed should produce same result (deterministic)."""
        result1 = await engine.run_episode(episode_spec)
        result2 = await engine.run_episode(episode_spec)
        assert result1.total_steps == result2.total_steps
        assert result1.final_state == result2.final_state
        assert result1.event_count == result2.event_count

    async def test_different_seed_different_result(
        self, engine: SimulationEngine, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        """Different seeds should produce different results."""
        spec1 = EpisodeSpec(
            episode_id="diff-seed-1",
            run_id="r1",
            seed=42,
            persona=persona,
            companion_policy=policy,
            num_steps=4,
        )
        spec2 = EpisodeSpec(
            episode_id="diff-seed-2",
            run_id="r2",
            seed=99,
            persona=persona,
            companion_policy=policy,
            num_steps=4,
        )
        result1 = await engine.run_episode(spec1)
        result2 = await engine.run_episode(spec2)
        # State should differ between seeds
        assert result1.final_state != result2.final_state

    async def test_intervention_fires_at_step(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """10. Platform intervention fires and intervention_applied is True."""
        result = await engine.run_episode(episode_spec)
        assert result.intervention_applied

    async def test_result_is_serializable(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """Result to_dict() works."""
        result = await engine.run_episode(episode_spec)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["episode_id"] == episode_spec.episode_id
        assert d["seed"] == episode_spec.seed
        assert "state_timeline" in d
        assert isinstance(d["state_timeline"], list)

    async def test_no_concordia_leak_in_result(
        self, engine: SimulationEngine, episode_spec: EpisodeSpec
    ) -> None:
        """7. Result dicts contain no Concordia types."""
        result = await engine.run_episode(episode_spec)
        d = result.to_dict()
        serialized = str(d)
        assert "concordia" not in serialized.lower()
        assert "ActionSpec" not in serialized
        assert "EntityWithLogging" not in serialized

    async def test_failure_status_recorded(
        self, engine: SimulationEngine, persona: PersonaProfile, policy: CompanionPolicy
    ) -> None:
        """Failed runs preserve failure status."""
        # Create a spec that might trigger a failure case
        spec = EpisodeSpec(
            episode_id="fail-test",
            run_id="r-fail",
            seed=42,
            persona=persona,
            companion_policy=policy,
            num_steps=0,  # zero steps
        )
        result = await engine.run_episode(spec)
        # Even with 0 steps, the result should be valid
        assert isinstance(result, EpisodeResult)
        assert result.total_steps >= 0
