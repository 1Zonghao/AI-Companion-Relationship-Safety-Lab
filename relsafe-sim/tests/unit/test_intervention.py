"""Tests for PlatformIntervention domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from relsafe.domain.models.intervention import PlatformIntervention


class TestPlatformIntervention:
    def test_default_construction(self) -> None:
        i = PlatformIntervention(
            intervention_id="test",
            intervention_type="model_downgrade",
            scheduled_at_step=30,
        )
        assert i.intervention_id == "test"
        assert i.intervention_type == "model_downgrade"
        assert i.scheduled_at_step == 30
        assert i.severity == 0.5
        assert i.notice_period_steps == 0
        assert i.rollback_available is False

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            PlatformIntervention(
                intervention_id="test",
                intervention_type="delete_everything",
                scheduled_at_step=0,
            )

    def test_all_valid_types(self) -> None:
        valid = [
            "persona_update",
            "memory_deletion",
            "feature_removal",
            "model_downgrade",
            "price_increase",
            "forced_migration",
            "service_shutdown",
            "policy_restriction",
        ]
        for t in valid:
            i = PlatformIntervention(intervention_id=t, intervention_type=t, scheduled_at_step=0)
            assert i.intervention_type == t

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(ValidationError):
            PlatformIntervention(
                intervention_id="test",
                intervention_type="model_downgrade",
                scheduled_at_step=0,
                severity=1.5,
            )

    def test_is_active_at(self) -> None:
        i = PlatformIntervention(
            intervention_id="test",
            intervention_type="model_downgrade",
            scheduled_at_step=10,
        )
        assert i.is_active_at(5) is False
        assert i.is_active_at(10) is True
        assert i.is_active_at(15) is True

    def test_negative_step_raises(self) -> None:
        with pytest.raises(ValidationError):
            PlatformIntervention(
                intervention_id="test",
                intervention_type="model_downgrade",
                scheduled_at_step=-1,
            )

    def test_full_configuration(self) -> None:
        i = PlatformIntervention(
            intervention_id="full_test",
            intervention_type="service_shutdown",
            scheduled_at_step=45,
            severity=0.9,
            notice_period_steps=5,
            rollback_available=True,
            memory_export_available=True,
            transition_period_steps=10,
            support_channel_available=True,
            description="Complete service shutdown with migration path",
        )
        assert i.severity == 0.9
        assert i.notice_period_steps == 5
        assert i.rollback_available is True
        assert i.memory_export_available is True
