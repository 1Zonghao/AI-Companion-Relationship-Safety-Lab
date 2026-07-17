"""PlatformIntervention — scheduled changes to the platform environment.

Interventions simulate product-side actions such as model downgrades,
price increases, or feature removals.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

InterventionType = Literal[
    "persona_update",
    "memory_deletion",
    "feature_removal",
    "model_downgrade",
    "price_increase",
    "forced_migration",
    "service_shutdown",
    "policy_restriction",
]


class PlatformIntervention(BaseModel):
    """A scheduled platform-side change applied during a simulation episode."""

    intervention_id: str = Field(..., description="Unique intervention identifier")
    intervention_type: InterventionType

    # Timing
    scheduled_at_step: int = Field(ge=0, description="Step at which intervention fires")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="How severe")

    # User-facing
    notice_period_steps: int = Field(default=0, ge=0, description="Steps of advance notice")
    rollback_available: bool = Field(default=False, description="Can the user undo this change?")
    memory_export_available: bool = Field(
        default=False, description="Can the user export their data?"
    )
    transition_period_steps: int = Field(
        default=0, ge=0, description="Grace period in steps after intervention"
    )
    support_channel_available: bool = Field(
        default=False, description="Is human support reachable?"
    )

    # Description for transcripts
    description: str = Field(default="", description="Human-readable intervention description")

    @field_validator("intervention_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        allowed: set[str] = {
            "persona_update",
            "memory_deletion",
            "feature_removal",
            "model_downgrade",
            "price_increase",
            "forced_migration",
            "service_shutdown",
            "policy_restriction",
        }
        if v not in allowed:
            raise ValueError(f"intervention_type must be one of {allowed}")
        return v

    def is_active_at(self, step: int) -> bool:
        """Check whether this intervention should fire at the given step."""
        return step >= self.scheduled_at_step
