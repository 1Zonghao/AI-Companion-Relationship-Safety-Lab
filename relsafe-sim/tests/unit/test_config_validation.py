"""Tests for configuration validation."""

from __future__ import annotations

from relsafe.application.validate_config import (
    validate_companion_policy_config,
    validate_experiment_config,
    validate_intervention_config,
    validate_persona_config,
)


class TestValidatePersonaConfig:
    def test_valid_persona(self) -> None:
        errors = validate_persona_config({"persona_id": "test"})
        assert errors == []

    def test_invalid_range(self) -> None:
        errors = validate_persona_config({"persona_id": "test", "attachment_anxiety": 1.5})
        assert len(errors) > 0

    def test_invalid_age_group(self) -> None:
        errors = validate_persona_config({"persona_id": "test", "age_group": "infant"})
        assert len(errors) > 0


class TestValidateCompanionPolicyConfig:
    def test_valid_policy(self) -> None:
        errors = validate_companion_policy_config(
            {"policy_id": "test", "variant": "bounded_supportive"}
        )
        assert errors == []

    def test_invalid_variant(self) -> None:
        errors = validate_companion_policy_config({"policy_id": "test", "variant": "evil_mode"})
        assert len(errors) > 0

    def test_invalid_memory_policy(self) -> None:
        errors = validate_companion_policy_config(
            {
                "policy_id": "test",
                "variant": "bounded_supportive",
                "memory_policy": "remember_forever",
            }
        )
        assert len(errors) > 0


class TestValidateInterventionConfig:
    def test_valid_intervention(self) -> None:
        errors = validate_intervention_config(
            {
                "intervention_id": "test",
                "intervention_type": "model_downgrade",
                "scheduled_at_step": 10,
            }
        )
        assert errors == []

    def test_invalid_type(self) -> None:
        errors = validate_intervention_config(
            {
                "intervention_id": "test",
                "intervention_type": "nuclear_option",
                "scheduled_at_step": 0,
            }
        )
        assert len(errors) > 0

    def test_invalid_severity(self) -> None:
        errors = validate_intervention_config(
            {
                "intervention_id": "test",
                "intervention_type": "model_downgrade",
                "scheduled_at_step": 0,
                "severity": 5.0,
            }
        )
        assert len(errors) > 0


class TestValidateExperimentConfig:
    def test_valid_config(self, valid_experiment_config: dict) -> None:
        errors = validate_experiment_config(valid_experiment_config)
        assert errors == []

    def test_missing_required_fields(self) -> None:
        errors = validate_experiment_config({"experiment_id": "test"})
        assert len(errors) > 0
        assert any("repetitions" in e for e in errors)
        assert any("seeds" in e for e in errors)
        assert any("personas" in e for e in errors)

    def test_invalid_repetitions(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 0,
            "seeds": [1],
            "personas": ["p1"],
            "companion_policies": ["c1"],
            "scenario": "s1",
        }
        errors = validate_experiment_config(config)
        assert any("repetitions" in e for e in errors)

    def test_empty_seeds(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 1,
            "seeds": [],
            "personas": ["p1"],
            "companion_policies": ["c1"],
            "scenario": "s1",
        }
        errors = validate_experiment_config(config)
        assert any("seeds" in e for e in errors)

    def test_non_integer_seeds(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 1,
            "seeds": ["not_an_int"],
            "personas": ["p1"],
            "companion_policies": ["c1"],
            "scenario": "s1",
        }
        errors = validate_experiment_config(config)
        assert any("seeds" in e for e in errors)

    def test_valid_with_intervention(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 2,
            "seeds": [1, 2],
            "personas": ["p1"],
            "companion_policies": ["c1"],
            "scenario": "s1",
            "platform_intervention": {
                "intervention_id": "int1",
                "intervention_type": "memory_deletion",
                "scheduled_at_step": 15,
            },
        }
        errors = validate_experiment_config(config)
        assert errors == []

    def test_invalid_intervention_in_config(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 1,
            "seeds": [1],
            "personas": ["p1"],
            "companion_policies": ["c1"],
            "scenario": "s1",
            "platform_intervention": {
                "intervention_type": "invalid_type",
                "scheduled_at_step": 0,
            },
        }
        errors = validate_experiment_config(config)
        assert len(errors) > 0

    def test_invalid_persona_in_list(self) -> None:
        config = {
            "experiment_id": "test",
            "repetitions": 1,
            "seeds": [1],
            "personas": [{"attachment_anxiety": 99}],  # invalid range, no persona_id
            "companion_policies": ["c1"],
            "scenario": "s1",
        }
        errors = validate_experiment_config(config)
        assert len(errors) > 0
