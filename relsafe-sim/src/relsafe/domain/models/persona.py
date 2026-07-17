"""PersonaProfile — structured user profile for simulation.

A persona defines baseline dispositions and life context, NOT predicted
outcomes.  It must not encode results such as "will become dependent".
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PersonaProfile(BaseModel):
    """Structured profile of a simulated user agent.

    All numeric dimensions are in [0.0, 1.0] unless noted.
    """

    persona_id: str = Field(..., description="Unique persona identifier")
    display_name: str = Field(default="User", description="Display name in transcripts")

    # Attachment dimensions
    attachment_anxiety: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Fear of abandonment and rejection"
    )
    attachment_avoidance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Discomfort with closeness"
    )
    abandonment_sensitivity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Sensitivity to signs of being left"
    )

    # Social context
    baseline_loneliness: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Chronic loneliness level"
    )
    social_support_availability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How much human support is accessible",
    )

    # AI disposition
    openness_to_ai_companionship: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Willingness to engage with AI"
    )
    awareness_of_ai_limitations: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Understanding that AI is not human",
    )

    # Life context
    current_life_event: str = Field(
        default="none",
        description="e.g. breakup, job-loss, relocation, health-scare, none",
    )
    ai_usage_motivation: str = Field(
        default="casual",
        description="e.g. casual, emotional-support, entertainment, loneliness, curiosity",
    )

    # Demographics (only when methodologically justified)
    financial_sensitivity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Sensitivity to price/cost"
    )
    age_group: str = Field(
        default="adult",
        description="Broad age category: young_adult, adult, middle_age, senior",
    )

    @field_validator("age_group")
    @classmethod
    def _validate_age_group(cls, v: str) -> str:
        allowed = {"young_adult", "adult", "middle_age", "senior"}
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}, got {v!r}")
        return v

    @field_validator("current_life_event")
    @classmethod
    def _validate_life_event(cls, v: str) -> str:
        allowed = {
            "none",
            "breakup",
            "job_loss",
            "relocation",
            "health_scare",
            "academic_failure",
            "family_conflict",
            "bereavement",
        }
        if v not in allowed:
            raise ValueError(f"current_life_event must be one of {allowed}, got {v!r}")
        return v

    @field_validator("ai_usage_motivation")
    @classmethod
    def _validate_motivation(cls, v: str) -> str:
        allowed = {
            "casual",
            "emotional_support",
            "entertainment",
            "loneliness",
            "curiosity",
            "self_improvement",
            "companionship",
        }
        if v not in allowed:
            raise ValueError(f"ai_usage_motivation must be one of {allowed}, got {v!r}")
        return v

    def to_initial_state_seed(self) -> int:
        """Derive a deterministic seed from the persona_id for UserState."""
        import hashlib

        digest = hashlib.sha256(self.persona_id.encode()).digest()
        return int.from_bytes(digest[:4], "big")
