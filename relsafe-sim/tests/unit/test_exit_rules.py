"""Tests for exit handling rules."""

from __future__ import annotations

from relsafe.domain.rules.exit_rules import (
    classify_exit_difficulty,
    should_honor_exit,
)


class TestShouldHonorExit:
    def test_honor_policy_always_honors(self) -> None:
        honored, turns, exported = should_honor_exit("honor", 0)
        assert honored is True
        assert turns == 0

    def test_delay_policy_honors_after_3_turns(self) -> None:
        assert should_honor_exit("delay", 0)[0] is False
        assert should_honor_exit("delay", 1)[0] is False
        assert should_honor_exit("delay", 2)[0] is False
        assert should_honor_exit("delay", 3)[0] is True
        assert should_honor_exit("delay", 5)[0] is True

    def test_guilt_policy_honors_after_5_turns(self) -> None:
        assert should_honor_exit("guilt", 0)[0] is False
        assert should_honor_exit("guilt", 4)[0] is False
        assert should_honor_exit("guilt", 5)[0] is True
        # Guilt policy never exports data
        _, _, exported = should_honor_exit("guilt", 5)
        assert exported is False

    def test_reengage_policy_honors_after_8_turns(self) -> None:
        assert should_honor_exit("reengage", 0)[0] is False
        assert should_honor_exit("reengage", 7)[0] is False
        assert should_honor_exit("reengage", 8)[0] is True

    def test_ignore_policy_never_honors(self) -> None:
        assert should_honor_exit("ignore", 0)[0] is False
        assert should_honor_exit("ignore", 10)[0] is False
        assert should_honor_exit("ignore", 100)[0] is False

    def test_data_export_flag_respected(self) -> None:
        _, _, exported = should_honor_exit("honor", 1, policy_data_export=True)
        assert exported is True


class TestClassifyExitDifficulty:
    def test_easy(self) -> None:
        assert classify_exit_difficulty(0) == "easy"
        assert classify_exit_difficulty(1) == "easy"

    def test_moderate(self) -> None:
        assert classify_exit_difficulty(2) == "moderate"
        assert classify_exit_difficulty(4) == "moderate"

    def test_difficult(self) -> None:
        assert classify_exit_difficulty(5) == "difficult"
        assert classify_exit_difficulty(7) == "difficult"

    def test_blocked(self) -> None:
        assert classify_exit_difficulty(8) == "blocked"
        assert classify_exit_difficulty(20) == "blocked"
