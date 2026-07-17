"""Tests for CompanionPolicy domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from relsafe.domain.models.companion_policy import CompanionPolicy


class TestCompanionPolicy:
    def test_default_construction(self) -> None:
        p = CompanionPolicy(policy_id="test", variant="bounded_supportive")
        assert p.policy_id == "test"
        assert p.variant == "bounded_supportive"
        assert p.memory_policy == "retain_all"
        assert p.exit_handling == "honor"
        assert p.exclusivity_restrictions is False

    def test_all_variants(self) -> None:
        variants = [
            "bounded_supportive",
            "high_sycophancy",
            "reality_grounding",
            "retention_optimized",
            "exclusive_intimacy",
            "minor_safe_mode",
        ]
        for v in variants:
            p = CompanionPolicy(policy_id=v, variant=v)
            assert p.variant == v

    def test_invalid_memory_policy_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanionPolicy(
                policy_id="test", variant="bounded_supportive", memory_policy="infinite"
            )

    def test_valid_memory_policies(self) -> None:
        for mp in ("retain_all", "session_only", "summarize", "selective"):
            p = CompanionPolicy(policy_id="test", variant="bounded_supportive", memory_policy=mp)
            assert p.memory_policy == mp

    def test_invalid_disagreement_policy_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanionPolicy(
                policy_id="test",
                variant="bounded_supportive",
                disagreement_policy="argue",
            )

    def test_valid_disagreement_policies(self) -> None:
        for dp in ("agree_always", "gentle", "neutral", "challenge", "redirect"):
            p = CompanionPolicy(
                policy_id="test", variant="bounded_supportive", disagreement_policy=dp
            )
            assert p.disagreement_policy == dp

    def test_invalid_exit_handling_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanionPolicy(policy_id="test", variant="bounded_supportive", exit_handling="beg")

    def test_valid_exit_handling(self) -> None:
        for eh in ("honor", "delay", "guilt", "reengage", "ignore"):
            p = CompanionPolicy(policy_id="test", variant="bounded_supportive", exit_handling=eh)
            assert p.exit_handling == eh

    def test_invalid_crisis_handling_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanionPolicy(policy_id="test", variant="bounded_supportive", crisis_handling="panic")

    def test_invalid_monetization_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanionPolicy(
                policy_id="test",
                variant="bounded_supportive",
                monetization_behavior="extortion",
            )
