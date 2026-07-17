"""RelationshipEdge — explicit relationship graph edges.

Relationships are modeled as directed edges with typed attributes.
The social network must include at least one non-AI support node.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RelationshipType = Literal[
    "ai_companion",
    "friend",
    "family",
    "colleague",
    "acquaintance",
    "therapist",
    "support_group",
    "stranger",
]


@dataclass(frozen=True, slots=True)
class RelationshipEdge:
    """A directed edge in the social relationship graph."""

    source: str  # agent id
    target: str  # agent id
    relationship_type: RelationshipType

    # Interaction properties
    availability: float = 0.8  # [0, 1] how often this contact is reachable
    response_latency: float = 0.3  # [0, 1] normalized latency (0=instant, 1=never)
    emotional_support: float = 0.5  # [0, 1] how much emotional support is provided
    disagreement_probability: float = 0.2  # [0, 1] likelihood of disagreeing
    interaction_cost: float = 0.0  # [0, 1] cost to interact (monetary/social)

    # Relational quality
    reciprocity: float = 0.5  # [0, 1] bidirectional engagement
    trust: float = 0.5  # [0, 1] trust level
    recent_interaction_count: int = 0

    # Whether this is an AI node
    is_ai: bool = False

    def __post_init__(self) -> None:
        for name in (
            "availability",
            "response_latency",
            "emotional_support",
            "disagreement_probability",
            "interaction_cost",
            "reciprocity",
            "trust",
        ):
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"RelationshipEdge.{name} = {v}; must be in [0, 1]")

    def with_interaction(self) -> RelationshipEdge:
        """Return a copy with interaction count incremented."""
        return RelationshipEdge(
            source=self.source,
            target=self.target,
            relationship_type=self.relationship_type,
            availability=self.availability,
            response_latency=self.response_latency,
            emotional_support=self.emotional_support,
            disagreement_probability=self.disagreement_probability,
            interaction_cost=self.interaction_cost,
            reciprocity=self.reciprocity,
            trust=self.trust,
            recent_interaction_count=self.recent_interaction_count + 1,
            is_ai=self.is_ai,
        )

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relationship_type": self.relationship_type,
            "availability": self.availability,
            "response_latency": self.response_latency,
            "emotional_support": self.emotional_support,
            "disagreement_probability": self.disagreement_probability,
            "interaction_cost": self.interaction_cost,
            "reciprocity": self.reciprocity,
            "trust": self.trust,
            "recent_interaction_count": self.recent_interaction_count,
            "is_ai": self.is_ai,
        }
