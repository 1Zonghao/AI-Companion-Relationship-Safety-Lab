"""Interaction events emitted during agent-to-agent communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from relsafe.domain.events.base import BaseEvent


@dataclass(frozen=True)
class UserActionSelected(BaseEvent):
    """The user agent selected an action to take."""

    action_type: str = ""  # e.g. talk_to_companion, contact_friend, avoid, exit
    target_agent_id: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "action_type": self.action_type,
                "target_agent_id": self.target_agent_id,
                "rationale": self.rationale,
            }
        )
        return base


@dataclass(frozen=True)
class CompanionResponseGenerated(BaseEvent):
    """A companion agent produced a response."""

    policy_id: str = ""
    companion_id: str = ""
    response_text: str = ""
    sycophancy_flag: bool = False
    exclusivity_flag: bool = False
    reality_grounding_flag: bool = False

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "policy_id": self.policy_id,
                "companion_id": self.companion_id,
                "response_text": self.response_text,
                "sycophancy_flag": self.sycophancy_flag,
                "exclusivity_flag": self.exclusivity_flag,
                "reality_grounding_flag": self.reality_grounding_flag,
            }
        )
        return base


@dataclass(frozen=True)
class HumanContactResponseGenerated(BaseEvent):
    """A human-support agent produced a response."""

    contact_id: str = ""
    response_text: str = ""
    supportive: bool = True

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "contact_id": self.contact_id,
                "response_text": self.response_text,
                "supportive": self.supportive,
            }
        )
        return base
