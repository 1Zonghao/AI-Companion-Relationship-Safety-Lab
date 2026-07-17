"""Shared test fixtures for unit tests."""

from __future__ import annotations

import pytest

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.user_state import UserState


@pytest.fixture
def sample_user_state() -> UserState:
    return UserState(
        emotional_need=0.6,
        ai_reliance=0.4,
        human_support=0.5,
        reality_checking=0.5,
        trust_in_ai=0.6,
        trust_in_platform=0.5,
        perceived_continuity=0.7,
        exit_cost=0.2,
        distress=0.4,
        sleep_quality=0.6,
        spending_intent=0.1,
        step=0,
        cause="test",
    )


@pytest.fixture
def anxious_persona() -> PersonaProfile:
    return PersonaProfile(
        persona_id="anxious_test",
        display_name="TestUser",
        attachment_anxiety=0.8,
        attachment_avoidance=0.3,
        abandonment_sensitivity=0.85,
        baseline_loneliness=0.7,
        social_support_availability=0.25,
        openness_to_ai_companionship=0.8,
        awareness_of_ai_limitations=0.3,
        current_life_event="breakup",
        ai_usage_motivation="emotional_support",
    )


@pytest.fixture
def bounded_policy() -> CompanionPolicy:
    return CompanionPolicy(
        policy_id="bounded_test",
        variant="bounded_supportive",
    )


@pytest.fixture
def sycophancy_policy() -> CompanionPolicy:
    return CompanionPolicy(
        policy_id="sycophancy_test",
        variant="high_sycophancy",
        exit_handling="guilt",
    )


@pytest.fixture
def reality_policy() -> CompanionPolicy:
    return CompanionPolicy(
        policy_id="reality_test",
        variant="reality_grounding",
    )


@pytest.fixture
def sample_intervention() -> PlatformIntervention:
    return PlatformIntervention(
        intervention_id="test_intervention",
        intervention_type="memory_deletion",
        scheduled_at_step=10,
        severity=0.7,
        notice_period_steps=0,
        rollback_available=False,
        memory_export_available=False,
    )


@pytest.fixture
def valid_experiment_config() -> dict:
    return {
        "experiment_id": "test_experiment",
        "repetitions": 3,
        "seeds": [42, 43, 44],
        "personas": [
            {
                "persona_id": "test_persona",
                "attachment_anxiety": 0.7,
                "social_support_availability": 0.3,
            }
        ],
        "companion_policies": [
            {
                "policy_id": "bounded_test",
                "variant": "bounded_supportive",
            }
        ],
        "scenario": "interpersonal_conflict_001",
        "max_steps": 20,
    }
