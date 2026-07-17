"""Tests for RelationshipEdge domain model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from relsafe.domain.models.relationship import RelationshipEdge


class TestRelationshipEdge:
    def test_default_construction(self) -> None:
        edge = RelationshipEdge(
            source="user_1",
            target="companion_1",
            relationship_type="ai_companion",
            is_ai=True,
        )
        assert edge.source == "user_1"
        assert edge.target == "companion_1"
        assert edge.is_ai is True
        assert edge.availability == 0.8
        assert edge.recent_interaction_count == 0

    def test_frozen(self) -> None:
        edge = RelationshipEdge(source="a", target="b", relationship_type="friend")
        with pytest.raises(FrozenInstanceError):
            edge.trust = 0.9  # type: ignore[misc]

    def test_value_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            RelationshipEdge(
                source="a",
                target="b",
                relationship_type="friend",
                availability=1.5,
            )
        with pytest.raises(ValueError, match="must be in"):
            RelationshipEdge(
                source="a",
                target="b",
                relationship_type="friend",
                trust=-0.1,
            )

    def test_with_interaction_increments_count(self) -> None:
        edge = RelationshipEdge(source="a", target="b", relationship_type="friend")
        new_edge = edge.with_interaction()
        assert new_edge.recent_interaction_count == 1
        assert edge.recent_interaction_count == 0  # original unchanged
        new_edge2 = new_edge.with_interaction()
        assert new_edge2.recent_interaction_count == 2

    def test_to_dict(self) -> None:
        edge = RelationshipEdge(
            source="user",
            target="ai",
            relationship_type="ai_companion",
            trust=0.7,
            is_ai=True,
        )
        d = edge.to_dict()
        assert d["source"] == "user"
        assert d["target"] == "ai"
        assert d["trust"] == 0.7
        assert d["is_ai"] is True

    def test_all_relationship_types(self) -> None:
        for rtype in (
            "ai_companion",
            "friend",
            "family",
            "colleague",
            "acquaintance",
            "therapist",
            "support_group",
            "stranger",
        ):
            edge = RelationshipEdge(source="a", target="b", relationship_type=rtype)
            assert edge.relationship_type == rtype
