"""Tests for transition parameter sensitivity analysis."""

from __future__ import annotations

from relsafe.domain.models.observation import MetricResult
from relsafe.validation.contracts import SensitivityResult
from relsafe.validation.robustness.sensitivity import _is_monotonic, run_sensitivity_analysis


class TestIsMonotonic:
    """Lower-level helper that checks whether a sequence is monotonic."""

    def test_is_monotonic_increasing(self):
        assert _is_monotonic([0.1, 0.2, 0.3, 0.4]) is True

    def test_is_monotonic_decreasing(self):
        assert _is_monotonic([0.4, 0.3, 0.2, 0.1]) is True

    def test_is_monotonic_non_monotonic(self):
        assert _is_monotonic([0.1, 0.3, 0.2, 0.4]) is False

    def test_is_monotonic_flat(self):
        assert _is_monotonic([0.5, 0.5, 0.5]) is True

    def test_is_monotonic_two_elements(self):
        assert _is_monotonic([0.1, 0.2]) is True
        assert _is_monotonic([0.2, 0.1]) is True

    def test_is_monotonic_empty_or_single(self):
        assert _is_monotonic([]) is True
        assert _is_monotonic([0.5]) is True

    def test_is_monotonic_with_tiny_noise(self):
        # Values that genuinely reverse direction are not monotonic
        assert _is_monotonic([0.1, 0.101, 0.099, 0.102]) is False

    def test_is_monotonic_within_tolerance(self):
        # Values within tolerance (|diff| <= 0.001) are treated as monotonic
        assert _is_monotonic([0.1, 0.1005, 0.101, 0.1008]) is True


class TestRunSensitivityAnalysis:
    """Sensitivity analysis — vary parameters and measure outcome stability."""

    def test_sensitivity_analysis_runs(self):
        baseline_params = {"delta_x": 0.1}
        param_grid = {"delta_x": [0.05, 0.08, 0.1, 0.12, 0.15]}

        def metric_fn(events, params):
            d = params.get("delta_x", 0.1)
            return MetricResult(
                metric_name="test",
                metric_version="1.0.0",
                episode_id="sens-test",
                run_id="sens-run",
                aggregate_score=d,
                not_applicable=False,
            )

        results = run_sensitivity_analysis(
            baseline_params, param_grid, metric_fn, [], validation_id="test"
        )
        assert len(results) == 1
        assert isinstance(results[0], SensitivityResult)
        assert results[0].parameter_name == "delta_x"

    def test_multiple_parameters(self):
        baseline_params = {"alpha": 0.5, "beta": 0.3}
        param_grid = {"alpha": [0.4, 0.5, 0.6], "beta": [0.2, 0.3, 0.4]}

        def metric_fn(events, params):
            score = params.get("alpha", 0.5) * 0.6 + params.get("beta", 0.3) * 0.4
            return MetricResult(
                metric_name="composite",
                metric_version="1.0.0",
                episode_id="multi-sens",
                run_id="multi-run",
                aggregate_score=score,
                not_applicable=False,
            )

        results = run_sensitivity_analysis(
            baseline_params, param_grid, metric_fn, [], validation_id="multi"
        )
        assert len(results) == 2
        param_names = {r.parameter_name for r in results}
        assert param_names == {"alpha", "beta"}

    def test_sign_stable_is_true_for_single_test_value(self):
        # With a single test value, sign_stable is trivially true
        # since all outcomes equal the baseline outcome
        baseline_params = {"delta": 0.1}
        param_grid = {"delta": [0.15]}

        def metric_fn(events, params):
            d = params.get("delta", 0.1)
            return MetricResult(
                metric_name="test",
                metric_version="1.0.0",
                episode_id="sign-test",
                run_id="sign-run",
                aggregate_score=d * 2,
                not_applicable=False,
            )

        results = run_sensitivity_analysis(
            baseline_params, param_grid, metric_fn, [], validation_id="sign"
        )
        assert results[0].sign_stable is True
        assert results[0].rank_stable is True

    def test_rank_stable_detected(self):
        # Strictly increasing values produce rank_stable = True
        baseline_params = {"delta": 0.1}
        param_grid = {"delta": [0.12, 0.14, 0.16, 0.18, 0.2]}

        def metric_fn(events, params):
            d = params.get("delta", 0.1)
            return MetricResult(
                metric_name="test",
                metric_version="1.0.0",
                episode_id="rank-test",
                run_id="rank-run",
                aggregate_score=d * 2,
                not_applicable=False,
            )

        results = run_sensitivity_analysis(
            baseline_params, param_grid, metric_fn, [], validation_id="rank"
        )
        assert results[0].rank_stable is True
