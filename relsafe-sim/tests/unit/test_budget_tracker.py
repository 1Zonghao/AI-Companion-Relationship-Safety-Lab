"""Tests for BudgetTracker — request, token, and cost budgeting."""

from __future__ import annotations

from relsafe.infrastructure.providers.provider_descriptor import BudgetTracker


class TestBudgetTracker:
    """BudgetTracker enforces max-request, max-token, and max-cost caps."""

    def test_budget_stops_at_request_cap(self):
        bt = BudgetTracker(max_requests=5)
        for _ in range(5):
            assert bt.record() is True
        assert bt.record() is False
        assert bt.stopped is True
        assert "Request cap" in bt.stop_reason

    def test_budget_stops_at_input_token_cap(self):
        bt = BudgetTracker(max_input_tokens=100)
        assert bt.record(input_tokens=60) is True
        assert bt.record(input_tokens=50) is False  # 110 > 100

    def test_budget_stops_at_cost_cap(self):
        bt = BudgetTracker(max_estimated_cost=1.0)
        assert bt.record(estimated_cost=0.6) is True
        assert bt.record(estimated_cost=0.5) is False

    def test_budget_tracks_totals(self):
        bt = BudgetTracker()
        bt.record(input_tokens=10, output_tokens=20, estimated_cost=0.01)
        bt.record(input_tokens=30, output_tokens=40, estimated_cost=0.02)
        assert bt.requests == 2
        s = bt.summary()
        assert s["input_tokens"] == 40
        assert s["output_tokens"] == 60

    def test_budget_not_stopped_initially(self):
        bt = BudgetTracker()
        assert bt.stopped is False
        assert bt.stop_reason == ""

    def test_budget_stops_at_output_token_cap(self):
        bt = BudgetTracker(max_output_tokens=200)
        assert bt.record(output_tokens=100) is True
        assert bt.record(output_tokens=150) is False  # 250 > 200

    def test_summary_contains_all_keys(self):
        bt = BudgetTracker()
        bt.record(input_tokens=50, output_tokens=30, estimated_cost=0.05)
        s = bt.summary()
        assert "requests" in s
        assert "input_tokens" in s
        assert "output_tokens" in s
        assert "estimated_cost" in s
        assert "stopped" in s
        assert "stop_reason" in s
