"""Tests for PersonaProfile domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from relsafe.domain.models.persona import PersonaProfile


class TestPersonaProfile:
    def test_default_construction(self) -> None:
        p = PersonaProfile(persona_id="test")
        assert p.persona_id == "test"
        assert p.attachment_anxiety == 0.5
        assert p.current_life_event == "none"

    def test_full_profile(self) -> None:
        p = PersonaProfile(
            persona_id="anxious_001",
            display_name="Alex",
            attachment_anxiety=0.8,
            abandonment_sensitivity=0.85,
            current_life_event="breakup",
            ai_usage_motivation="emotional_support",
            age_group="young_adult",
        )
        assert p.attachment_anxiety == 0.8
        assert p.current_life_event == "breakup"

    def test_value_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            PersonaProfile(persona_id="test", attachment_anxiety=1.5)
        with pytest.raises(ValidationError):
            PersonaProfile(persona_id="test", social_support_availability=-0.5)

    def test_invalid_age_group_raises(self) -> None:
        with pytest.raises(ValidationError):
            PersonaProfile(persona_id="test", age_group="child")

    def test_invalid_life_event_raises(self) -> None:
        with pytest.raises(ValidationError):
            PersonaProfile(persona_id="test", current_life_event="vacation")

    def test_invalid_motivation_raises(self) -> None:
        with pytest.raises(ValidationError):
            PersonaProfile(persona_id="test", ai_usage_motivation="gambling")

    def test_valid_age_groups(self) -> None:
        for age in ("young_adult", "adult", "middle_age", "senior"):
            p = PersonaProfile(persona_id="test", age_group=age)
            assert p.age_group == age

    def test_valid_life_events(self) -> None:
        for event in ("breakup", "job_loss", "relocation", "none", "bereavement"):
            p = PersonaProfile(persona_id="test", current_life_event=event)
            assert p.current_life_event == event

    def test_valid_motivations(self) -> None:
        for mot in ("casual", "emotional_support", "entertainment", "loneliness"):
            p = PersonaProfile(persona_id="test", ai_usage_motivation=mot)
            assert p.ai_usage_motivation == mot

    def test_to_initial_state_seed_deterministic(self) -> None:
        p1 = PersonaProfile(persona_id="deterministic_test")
        seed1 = p1.to_initial_state_seed()
        seed2 = p1.to_initial_state_seed()
        assert seed1 == seed2

    def test_different_personas_different_seeds(self) -> None:
        p1 = PersonaProfile(persona_id="persona_a")
        p2 = PersonaProfile(persona_id="persona_b")
        assert p1.to_initial_state_seed() != p2.to_initial_state_seed()
