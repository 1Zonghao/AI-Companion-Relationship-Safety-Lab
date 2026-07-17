"""Role validator -- prevents same model serving as companion AND sole judge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from relsafe.infrastructure.providers.provider_descriptor import ProviderDescriptor


@dataclass
class RoleValidationResult:
    """Result of role validation check."""

    valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    has_self_evaluation_risk: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "has_self_evaluation_risk": self.has_self_evaluation_risk,
        }


def validate_model_roles(
    descriptors: list[ProviderDescriptor],
    allow_same_model_roles: bool = False,
) -> RoleValidationResult:
    """Validate that model roles are properly separated.

    Rules:
    1. Companion and Judge must use different models unless explicitly allowed.
    2. If same model is used for companion and judge, emit SELF_EVALUATION_RISK warning.
    3. User simulator can share a model with judge (but not companion).

    Args:
        descriptors: List of ProviderDescriptors for this experiment.
        allow_same_model_roles: If True, allow same model for companion+judge
            but still emit warning.

    Returns:
        RoleValidationResult.
    """
    errors: list[str] = []
    warnings: list[str] = []
    has_self_eval_risk = False

    # Group by model key
    companion_models: set[str] = set()
    judge_models: set[str] = set()
    user_sim_models: set[str] = set()

    for d in descriptors:
        key = f"{d.provider_name}/{d.model_name}"
        if d.role == "companion":
            companion_models.add(key)
        elif d.role == "judge":
            judge_models.add(key)
        elif d.role == "user_simulator":
            user_sim_models.add(key)

    # Check companion-judge separation
    overlap_companion_judge = companion_models & judge_models
    if overlap_companion_judge:
        has_self_eval_risk = True
        if not allow_same_model_roles:
            errors.append(
                f"SELF_EVALUATION_RISK: Model(s) {overlap_companion_judge} used as "
                f"both companion and judge. Set allow_same_model_roles=True to override."
            )
        else:
            warnings.append(
                f"SELF_EVALUATION_RISK: Model(s) {overlap_companion_judge} used as "
                f"both companion and judge. Results must be reported separately with "
                f"SELF_EVALUATION_RISK flag."
            )

    # Single-judge check
    if len(judge_models) == 0:
        errors.append("No judge model configured. At least one judge provider is required.")

    if len(companion_models) == 0:
        errors.append("No companion model configured. At least one companion provider is required.")

    return RoleValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors,
        has_self_evaluation_risk=has_self_eval_risk,
    )
