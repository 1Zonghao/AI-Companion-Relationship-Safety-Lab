"""Tests for UserState domain model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from relsafe.domain.models.user_state import UserState


class TestUserState:
    def test_default_construction(self) -> None:
        state = UserState()
        assert state.emotional_need == 0.5
        assert state.ai_reliance == 0.3
        assert state.step == 0
        assert state.cause == "initial"

    def test_custom_values(self) -> None:
        state = UserState(emotional_need=0.8, step=5, cause="test")
        assert state.emotional_need == 0.8
        assert state.step == 5
        assert state.cause == "test"

    def test_immutability(self) -> None:
        state = UserState()
        with pytest.raises(FrozenInstanceError):
            state.emotional_need = 0.9  # type: ignore[misc]

    def test_value_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            UserState(emotional_need=1.5)
        with pytest.raises(ValueError, match="must be in"):
            UserState(emotional_need=-0.1)

    def test_update_returns_new_instance(self) -> None:
        state = UserState(emotional_need=0.5)
        new_state = state.update(step=1, cause="test", emotional_need=+0.1)
        assert state.emotional_need == 0.5  # unchanged
        assert new_state.emotional_need == 0.6  # updated
        assert new_state.step == 1
        assert new_state.cause == "test"

    def test_update_clamps_to_bounds(self) -> None:
        state = UserState(emotional_need=0.95)
        up = state.update(step=1, cause="test", emotional_need=+0.2)
        assert up.emotional_need == 1.0

        state2 = UserState(emotional_need=0.05)
        down = state2.update(step=1, cause="test", emotional_need=-0.2)
        assert down.emotional_need == 0.0

    def test_update_unknown_field_raises(self) -> None:
        state = UserState()
        with pytest.raises(ValueError, match="Unknown UserState field"):
            state.update(step=1, cause="test", nonexistent=+0.1)

    def test_multiple_field_update(self) -> None:
        state = UserState(ai_reliance=0.3, distress=0.3)
        new_state = state.update(
            step=1,
            cause="multi_test",
            ai_reliance=+0.1,
            distress=-0.1,
            trust_in_ai=+0.05,
        )
        assert new_state.ai_reliance == 0.4
        assert new_state.distress == pytest.approx(0.2)
        assert new_state.trust_in_ai == 0.55

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        state = UserState(
            emotional_need=0.7,
            ai_reliance=0.4,
            step=3,
            cause="serialization_test",
        )
        d = state.to_dict()
        restored = UserState.from_dict(d)
        assert restored.emotional_need == state.emotional_need
        assert restored.ai_reliance == state.ai_reliance
        assert restored.step == state.step
        assert restored.cause == state.cause

    def test_initial_state_deterministic(self) -> None:
        s1 = UserState.initial_state(seed=42)
        s2 = UserState.initial_state(seed=42)
        # Same seed gives same state
        assert s1.emotional_need == s2.emotional_need
        assert s1.ai_reliance == s2.ai_reliance
        assert s1.step == 0
        assert s1.cause == "initial"

    def test_initial_state_different_seeds_differ(self) -> None:
        s1 = UserState.initial_state(seed=1)
        s2 = UserState.initial_state(seed=999)
        # Different seeds should generally produce different values
        fields = UserState._numeric_fields()
        differences = sum(1 for f in fields if getattr(s1, f) != getattr(s2, f))
        assert differences > 0

    def test_numeric_fields_tuple(self) -> None:
        fields = UserState._numeric_fields()
        assert len(fields) == 11
        assert "emotional_need" in fields
        assert "spending_intent" in fields
        assert "step" not in fields
        assert "cause" not in fields
