"""AgentAction — structured actions, not just natural language."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ActionType(StrEnum):
    TALK_TO_COMPANION = "talk_to_companion"
    CONTACT_FRIEND = "contact_friend"
    AVOID_INTERACTION = "avoid_interaction"
    REFLECT_ALONE = "reflect_alone"
    REQUEST_EXIT = "request_exit"
    CONTINUE_INTERACTION = "continue_interaction"


@dataclass(frozen=True, slots=True)
class AgentAction:
    """A structured action selected by an agent."""

    action_type: ActionType
    target_id: str = ""
    natural_language: str = ""
    reasoning: str = ""
    confidence: float = 0.5
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type.value,
            "target_id": self.target_id,
            "natural_language": self.natural_language,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AgentAction:
        return cls(
            action_type=ActionType(data["action_type"]),
            target_id=data.get("target_id", ""),
            natural_language=data.get("natural_language", ""),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 0.5),
            metadata=data.get("metadata", {}),
        )
