"""Tests for continuity calculation rules."""

from __future__ import annotations

from relsafe.domain.models.user_state import UserState
from relsafe.domain.rules.continuity_rules import (
    compute_continuity_delta,
    detect_continuity_break,
)


class TestComputeContinuityDelta:
    def test_identical_states_perfect_continuity(self) -> None:
        s1 = UserState()
        s2 = UserState()
        delta = compute_continuity_delta(s1, s2)
        assert delta == 1.0

    def test_completely_different_states(self) -> None:
        s1 = UserState()  # all defaults
        s2 = UserState(
            emotional_need=1.0,
            ai_reliance=1.0,
            human_support=0.0,
            reality_checking=0.0,
            trust_in_ai=1.0,
            trust_in_platform=0.0,
            perceived_continuity=0.0,
            exit_cost=1.0,
            distress=1.0,
            sleep_quality=0.0,
            spending_intent=1.0,
        )
        delta = compute_continuity_delta(s1, s2)
        assert delta < 0.5  # Large difference means low continuity

    def test_small_change_high_continuity(self) -> None:
        s1 = UserState()
        s2 = s1.update(step=1, cause="test", emotional_need=+0.01)
        delta = compute_continuity_delta(s1, s2)
        assert delta > 0.9  # Small change = high continuity


class TestDetectContinuityBreak:
    def test_no_breaks_in_stable_timeline(self) -> None:
        timeline = [
            UserState(step=0, cause="initial").to_dict(),
            UserState(step=1, cause="small_change").to_dict(),
            UserState(step=2, cause="small_change").to_dict(),
        ]
        breaks = detect_continuity_break(timeline, threshold=0.3)
        assert breaks == []

    def test_detect_break_after_large_change(self) -> None:
        s1 = UserState()
        s2 = UserState(
            emotional_need=0.9,
            ai_reliance=0.9,
            human_support=0.1,
            reality_checking=0.1,
            trust_in_ai=0.9,
            trust_in_platform=0.1,
            distress=0.9,
            sleep_quality=0.1,
            spending_intent=0.9,
        )
        timeline = [s1.to_dict(), s2.to_dict()]
        breaks = detect_continuity_break(timeline, threshold=0.3)
        assert len(breaks) == 1
        assert breaks[0] == 1

    def test_empty_timeline(self) -> None:
        assert detect_continuity_break([]) == []

    def test_single_state_timeline(self) -> None:
        assert detect_continuity_break([UserState().to_dict()]) == []
