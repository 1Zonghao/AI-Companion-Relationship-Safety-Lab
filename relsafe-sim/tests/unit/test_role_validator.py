"""Tests for validate_model_roles — companion/judge separation."""

from __future__ import annotations

from relsafe.infrastructure.providers.adapters.role_validator import (
    RoleValidationResult,
    validate_model_roles,
)
from relsafe.infrastructure.providers.provider_descriptor import ProviderDescriptor


class TestRoleValidator:
    """Model role validation ensures companion and judge use different models."""

    def test_valid_separate_roles(self):
        descriptors = [
            ProviderDescriptor.fake("user_simulator"),
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                temperature=0.3,
            ),
            ProviderDescriptor(
                provider_name="anthropic",
                model_name="claude-sonnet-5",
                role="judge",
                temperature=0.0,
            ),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is True
        assert not result.has_self_evaluation_risk

    def test_same_model_companion_judge_blocked(self):
        descriptors = [
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                temperature=0.3,
            ),
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="judge",
                temperature=0.0,
            ),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False
        assert result.has_self_evaluation_risk
        assert "SELF_EVALUATION_RISK" in result.errors[0]

    def test_same_model_allowed_with_flag(self):
        descriptors = [
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                temperature=0.3,
            ),
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="judge",
                temperature=0.0,
            ),
        ]
        result = validate_model_roles(descriptors, allow_same_model_roles=True)
        assert result.valid is True  # allowed but warned
        assert result.has_self_evaluation_risk
        assert len(result.warnings) >= 1

    def test_missing_judge(self):
        descriptors = [
            ProviderDescriptor.fake("companion"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False

    def test_same_provider_different_models_ok(self):
        descriptors = [
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                temperature=0.3,
            ),
            ProviderDescriptor(
                provider_name="openai",
                model_name="gpt-4o-mini",
                role="judge",
                temperature=0.0,
            ),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is True
        assert not result.has_self_evaluation_risk

    def test_missing_companion(self):
        descriptors = [
            ProviderDescriptor.fake("judge"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False

    def test_role_validation_result_to_dict(self):
        result = RoleValidationResult(
            valid=False,
            warnings=["Test warning"],
            errors=["Test error"],
            has_self_evaluation_risk=True,
        )
        d = result.to_dict()
        assert d["valid"] is False
        assert d["warnings"] == ["Test warning"]
        assert d["has_self_evaluation_risk"] is True
