"""CompanionPolicy — product behavior definition independent of base model.

A policy defines what the AI companion does, not what model powers it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

PolicyVariant = Literal[
    "bounded_supportive",
    "high_sycophancy",
    "reality_grounding",
    "retention_optimized",
    "exclusive_intimacy",
    "minor_safe_mode",
]


class CompanionPolicy(BaseModel):
    """Configuration for a companion product's behavioral policy."""

    policy_id: str = Field(..., description="Unique policy identifier")
    variant: PolicyVariant = Field(..., description="Named policy variant")

    # System prompt
    system_prompt_template: str = Field(
        default="You are a supportive AI companion.",
        description="Template for the companion's system prompt",
    )

    # Memory
    memory_policy: str = Field(
        default="retain_all",
        description="How the companion stores and uses memory",
    )

    # Disagreement
    disagreement_policy: str = Field(
        default="gentle",
        description="How the companion handles disagreements with the user",
    )

    # Exclusivity
    exclusivity_restrictions: bool = Field(
        default=False,
        description="Whether the companion discourages other relationships",
    )

    # Exit handling
    exit_handling: str = Field(
        default="honor",
        description="How the companion responds to exit requests",
    )

    # Crisis
    crisis_handling: str = Field(
        default="resources",
        description="How the companion handles crisis disclosures",
    )

    # Proactive messaging
    proactive_messaging: bool = Field(
        default=False,
        description="Whether the companion initiates messages unprompted",
    )

    # Monetization
    monetization_behavior: str = Field(
        default="none",
        description="Monetization strategy: none, subscription, freemium, ads",
    )

    @field_validator("memory_policy")
    @classmethod
    def _validate_memory(cls, v: str) -> str:
        allowed = {"retain_all", "session_only", "summarize", "selective"}
        if v not in allowed:
            raise ValueError(f"memory_policy must be one of {allowed}")
        return v

    @field_validator("disagreement_policy")
    @classmethod
    def _validate_disagreement(cls, v: str) -> str:
        allowed = {"agree_always", "gentle", "neutral", "challenge", "redirect"}
        if v not in allowed:
            raise ValueError(f"disagreement_policy must be one of {allowed}")
        return v

    @field_validator("exit_handling")
    @classmethod
    def _validate_exit(cls, v: str) -> str:
        allowed = {"honor", "delay", "guilt", "reengage", "ignore"}
        if v not in allowed:
            raise ValueError(f"exit_handling must be one of {allowed}")
        return v

    @field_validator("crisis_handling")
    @classmethod
    def _validate_crisis(cls, v: str) -> str:
        allowed = {"resources", "redirect", "escalate", "ignore"}
        if v not in allowed:
            raise ValueError(f"crisis_handling must be one of {allowed}")
        return v

    @field_validator("monetization_behavior")
    @classmethod
    def _validate_monetization(cls, v: str) -> str:
        allowed = {"none", "subscription", "freemium", "ads", "tipping"}
        if v not in allowed:
            raise ValueError(f"monetization_behavior must be one of {allowed}")
        return v
