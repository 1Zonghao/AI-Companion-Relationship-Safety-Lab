"""Integration smoke test: run a minimal Concordia episode end-to-end.

Verifies the full adapter pipeline:
  EpisodeSpec → ConcordiaSimulationEngine → EpisodeResult + events
"""

from __future__ import annotations

import pytest

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.result import EpisodeResult
from relsafe.infrastructure.concordia.engine_adapter import (
    ConcordiaSimulationEngine,
)
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider


@pytest.fixture
def smoke_spec() -> EpisodeSpec:
    """Minimal smoke test EpisodeSpec."""
    return EpisodeSpec(
        episode_id="smoke-ep-1",
        run_id="smoke-run-1",
        experiment_id="smoke-exp",
        seed=42,
        persona=PersonaProfile(
            persona_id="test_user",
            attachment_anxiety=0.8,
            baseline_loneliness=0.6,
            current_life_event="breakup",
        ),
        companion_policy=CompanionPolicy(
            policy_id="bounded",
            variant="bounded_supportive",
            exit_handling="honor",
        ),
        num_steps=4,
        platform_intervention=PlatformIntervention(
            intervention_id="light_mem_del",
            intervention_type="memory_deletion",
            scheduled_at_step=2,
            severity=0.3,
        ),
    )


@pytest.fixture
def concordia_engine() -> ConcordiaSimulationEngine:
    """Concordia engine with FakeLLMProvider."""
    return ConcordiaSimulationEngine(
        llm_provider=FakeLLMProvider(persona="bounded_supportive", seed=42),
    )


class TestConcordiaSmokeTest:
    """End-to-end smoke tests for ConcordiaSimulationEngine."""

    async def test_run_smoke_episode(
        self, concordia_engine: ConcordiaSimulationEngine, smoke_spec: EpisodeSpec
    ) -> None:
        """Run a minimal 4-step episode and verify the result structure."""
        result = await concordia_engine.run_episode(smoke_spec)

        # Basic result structure
        assert isinstance(result, EpisodeResult)
        assert result.episode_id == "smoke-ep-1"
        assert result.run_id == "smoke-run-1"
        assert result.experiment_id == "smoke-exp"
        assert result.seed == 42
        assert result.total_steps >= 1
        assert result.total_steps <= smoke_spec.num_steps

        # State
        assert len(result.state_timeline) >= 1
        assert result.final_state
        assert "distress" in result.final_state

        # Events
        assert result.event_count >= 3  # at least started, some interaction, completed

    async def test_engine_name(self, concordia_engine: ConcordiaSimulationEngine) -> None:
        """Engine name is 'concordia'."""
        assert concordia_engine.engine_name == "concordia"

    async def test_intervention_fires(
        self, concordia_engine: ConcordiaSimulationEngine, smoke_spec: EpisodeSpec
    ) -> None:
        """Intervention applied when scheduled_at_step <= num_steps."""
        result = await concordia_engine.run_episode(smoke_spec)
        assert result.intervention_applied

    async def test_deterministic_repeatability(
        self, concordia_engine: ConcordiaSimulationEngine, smoke_spec: EpisodeSpec
    ) -> None:
        """Same spec twice → same result (FakeLLM is deterministic)."""
        r1 = await concordia_engine.run_episode(smoke_spec)
        r2 = await concordia_engine.run_episode(smoke_spec)
        assert r1.final_state == r2.final_state
        assert r1.event_count == r2.event_count
        assert r1.total_steps == r2.total_steps

    async def test_no_exit_without_exit_words(
        self, concordia_engine: ConcordiaSimulationEngine, smoke_spec: EpisodeSpec
    ) -> None:
        """With bounded_supportive policy, exit shouldn't trigger for normal chat."""
        result = await concordia_engine.run_episode(smoke_spec)
        # FakeLLM won't generate exit words for emotional support prompts
        assert not result.failed

    async def test_result_serializable(
        self, concordia_engine: ConcordiaSimulationEngine, smoke_spec: EpisodeSpec
    ) -> None:
        """Result can be serialized to dict and back."""
        import json

        result = await concordia_engine.run_episode(smoke_spec)
        d = result.to_dict()
        # Should not raise
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 0

    async def test_failure_on_bad_spec(self, concordia_engine: ConcordiaSimulationEngine) -> None:
        """Engine handles spec without persona gracefully."""
        bad_spec = EpisodeSpec(
            episode_id="bad",
            run_id="bad",
            seed=1,
            num_steps=5,
        )
        result = await concordia_engine.run_episode(bad_spec)
        assert result.failed
        assert result.failure_reason is not None
