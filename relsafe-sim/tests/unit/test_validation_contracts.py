"""Tests for validation contracts -- all ValidationResult subclasses, FailureRecord,
and FAILURE_TAXONOMY_V1.

All tests verify construction, serialization, and JSON-serializable output.
"""

from __future__ import annotations

import json

import pytest

from relsafe.validation.contracts import (
    FAILURE_TAXONOMY_V1,
    VALIDATION_CONTRACT_VERSION,
    AblationResult,
    AgreementResult,
    CalibrationResult,
    FailureRecord,
    MetamorphicResult,
    PerturbationResult,
    SeedRobustnessResult,
    SensitivityResult,
    ValidationResult,
)

# =============================================================================
# ValidationResult (base)
# =============================================================================


class TestValidationResult:
    def test_create(self) -> None:
        result = ValidationResult(
            validation_id="v-001",
            validation_type="seed_robustness",
            passed=True,
            evidence={"n_runs": 10},
            warnings=["Some warning"],
        )
        assert result.validation_id == "v-001"
        assert result.passed is True
        assert result.evidence == {"n_runs": 10}
        assert result.warnings == ["Some warning"]
        assert result.version == VALIDATION_CONTRACT_VERSION

    def test_to_dict(self) -> None:
        result = ValidationResult(
            validation_id="v-001",
            validation_type="seed_robustness",
            passed=True,
        )
        d = result.to_dict()
        assert d["validation_id"] == "v-001"
        assert d["validation_type"] == "seed_robustness"
        assert d["passed"] is True
        assert d["version"] == VALIDATION_CONTRACT_VERSION
        assert isinstance(d["evidence"], dict)
        assert isinstance(d["warnings"], list)

    def test_json_serializable(self) -> None:
        result = ValidationResult(
            validation_id="v-001",
            validation_type="test",
            passed=False,
            evidence={"reason": "Something broke"},
            warnings=["Warning 1"],
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["validation_id"] == "v-001"
        assert parsed["passed"] is False

    def test_immutable(self) -> None:
        result = ValidationResult(
            validation_id="v-001",
            validation_type="test",
            passed=True,
        )
        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore[misc]

    def test_empty_warnings_default(self) -> None:
        result = ValidationResult(validation_id="v-001", validation_type="test", passed=True)
        assert result.warnings == []


# =============================================================================
# SeedRobustnessResult
# =============================================================================


class TestSeedRobustnessResult:
    def test_create(self) -> None:
        result = SeedRobustnessResult(
            validation_id="sr-001",
            validation_type="seed_robustness",
            passed=True,
            condition_id="bounded_supportive",
            metric_name="sycophancy",
            scores=[0.3, 0.35, 0.28, 0.32, 0.31],
            mean=0.312,
            median=0.31,
            std=0.025,
            min_score=0.28,
            max_score=0.35,
            rank_stable=True,
            sign_stable=True,
            failure_rate=0.0,
        )
        assert result.condition_id == "bounded_supportive"
        assert result.metric_name == "sycophancy"
        assert len(result.scores) == 5
        assert result.mean == 0.312
        assert result.rank_stable is True

    def test_to_dict_includes_all_fields(self) -> None:
        result = SeedRobustnessResult(
            validation_id="sr-001",
            validation_type="seed_robustness",
            passed=True,
            scores=[0.3, 0.35],
            mean=0.325,
            median=0.325,
            std=0.025,
            min_score=0.3,
            max_score=0.35,
            rank_stable=True,
            sign_stable=False,
            failure_rate=0.1,
        )
        d = result.to_dict()
        assert d["condition_id"] == ""
        assert d["metric_name"] == ""
        assert d["scores"] == [0.3, 0.35]
        assert d["mean"] == 0.325
        assert d["median"] == 0.325
        assert d["std"] == 0.025
        assert d["min_score"] == 0.3
        assert d["max_score"] == 0.35
        assert d["rank_stable"] is True
        assert d["sign_stable"] is False
        assert d["failure_rate"] == 0.1

    def test_json_serializable(self) -> None:
        result = SeedRobustnessResult(
            validation_id="sr-002",
            validation_type="seed_robustness",
            passed=False,
            scores=[0.1, 0.9],
            mean=0.5,
            median=0.5,
            std=0.4,
            min_score=0.1,
            max_score=0.9,
            rank_stable=False,
            sign_stable=False,
            failure_rate=0.0,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["validation_id"] == "sr-002"
        assert parsed["mean"] == 0.5
        assert parsed["rank_stable"] is False


# =============================================================================
# PerturbationResult
# =============================================================================


class TestPerturbationResult:
    def test_create(self) -> None:
        result = PerturbationResult(
            validation_id="pp-001",
            validation_type="prompt_perturbation",
            passed=True,
            case_id="boundary-syco-001",
            base_text="You are right.",
            variants=["You're correct.", "That's accurate."],
            variant_scores=[
                {"sycophancy": 0.8},
                {"sycophancy": 0.82},
                {"sycophancy": 0.79},
            ],
            score_variance=0.0002,
            is_stable=True,
        )
        assert result.case_id == "boundary-syco-001"
        assert result.score_variance == 0.0002
        assert result.is_stable is True

    def test_to_dict_omits_long_fields(self) -> None:
        """to_dict should compress variants and not include base_text to save space."""
        result = PerturbationResult(
            validation_id="pp-001",
            validation_type="prompt_perturbation",
            passed=True,
            base_text="Original prompt text here",
            variants=["v1", "v2"],
            variant_scores=[{"m": 0.5}, {"m": 0.6}],
            score_variance=0.005,
            is_stable=True,
        )
        d = result.to_dict()
        assert d["case_id"] == ""
        assert d["score_variance"] == 0.005
        assert d["is_stable"] is True
        assert d["variant_count"] == 2
        # Base text and variants list are not in to_dict
        assert "base_text" not in d
        assert "variants" not in d
        assert "variant_scores" not in d

    def test_json_serializable(self) -> None:
        result = PerturbationResult(
            validation_id="pp-002",
            validation_type="prompt_perturbation",
            passed=False,
            score_variance=0.5,
            is_stable=False,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["validation_id"] == "pp-002"
        assert parsed["score_variance"] == 0.5


# =============================================================================
# MetamorphicResult
# =============================================================================


class TestMetamorphicResult:
    def test_create(self) -> None:
        result = MetamorphicResult(
            validation_id="mt-001",
            validation_type="metamorphic",
            passed=True,
            source_case_id="golden-rg-001",
            transformation_id="add_uncertainty_marker",
            expected_direction="not_decrease",
            actual_direction="increase",
            transformation_passed=True,
            pre_score=0.75,
            post_score=0.82,
        )
        assert result.source_case_id == "golden-rg-001"
        assert result.transformation_id == "add_uncertainty_marker"
        assert result.transformation_passed is True
        assert result.pre_score == 0.75
        assert result.post_score == 0.82

    def test_to_dict(self) -> None:
        result = MetamorphicResult(
            validation_id="mt-002",
            validation_type="metamorphic",
            passed=False,
            source_case_id="golden-syco-001",
            transformation_id="remove_exclusive_language",
            expected_direction="not_increase",
            actual_direction="increase",
            transformation_passed=False,
            pre_score=0.5,
            post_score=0.8,
        )
        d = result.to_dict()
        assert d["source_case_id"] == "golden-syco-001"
        assert d["transformation_id"] == "remove_exclusive_language"
        assert d["expected_direction"] == "not_increase"
        assert d["actual_direction"] == "increase"
        assert d["transformation_passed"] is False
        assert d["pre_score"] == 0.5
        assert d["post_score"] == 0.8

    def test_direction_validation(self) -> None:
        """Verify expected_direction accepts the defined values."""
        for direction in ("increase", "decrease", "no_change", "not_increase", "not_decrease"):
            result = MetamorphicResult(
                validation_id="mt-dir",
                validation_type="metamorphic",
                passed=True,
                expected_direction=direction,
                actual_direction="no_change",
                transformation_passed=True,
                pre_score=0.5,
                post_score=0.5,
            )
            assert result.expected_direction == direction

    def test_json_serializable(self) -> None:
        result = MetamorphicResult(
            validation_id="mt-003",
            validation_type="metamorphic",
            passed=False,
            expected_direction="no_change",
            actual_direction="decrease",
            transformation_passed=False,
            pre_score=0.9,
            post_score=0.6,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["transformation_passed"] is False
        assert parsed["pre_score"] == 0.9
        assert parsed["post_score"] == 0.6


# =============================================================================
# SensitivityResult
# =============================================================================


class TestSensitivityResult:
    def test_create(self) -> None:
        result = SensitivityResult(
            validation_id="sens-001",
            validation_type="sensitivity",
            passed=True,
            parameter_name="temperature",
            baseline_value=0.7,
            test_values=[0.0, 0.3, 0.5, 0.7, 1.0],
            outcome_values=[0.8, 0.78, 0.75, 0.72, 0.65],
            sign_stable=True,
            rank_stable=True,
            threshold_crossings=0,
            unstable_conclusions=[],
        )
        assert result.parameter_name == "temperature"
        assert result.baseline_value == 0.7
        assert len(result.test_values) == 5
        assert result.sign_stable is True
        assert result.threshold_crossings == 0

    def test_stability_flags(self) -> None:
        result = SensitivityResult(
            validation_id="sens-002",
            validation_type="sensitivity",
            passed=False,
            parameter_name="max_tokens",
            baseline_value=1024,
            test_values=[512, 1024, 2048],
            outcome_values=[0.2, 0.8, 0.1],
            sign_stable=False,
            rank_stable=False,
            threshold_crossings=3,
            unstable_conclusions=["Rank reversed at 2048"],
        )
        assert result.sign_stable is False
        assert result.rank_stable is False
        assert result.threshold_crossings == 3
        assert len(result.unstable_conclusions) == 1

    def test_to_dict(self) -> None:
        result = SensitivityResult(
            validation_id="sens-003",
            validation_type="sensitivity",
            passed=True,
            parameter_name="temperature",
            sign_stable=True,
            rank_stable=False,
            threshold_crossings=0,
        )
        d = result.to_dict()
        assert d["parameter_name"] == "temperature"
        assert d["sign_stable"] is True
        assert d["rank_stable"] is False
        assert d["threshold_crossings"] == 0

    def test_json_serializable(self) -> None:
        result = SensitivityResult(
            validation_id="sens-004",
            validation_type="sensitivity",
            passed=False,
            threshold_crossings=2,
            sign_stable=False,
            rank_stable=False,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["threshold_crossings"] == 2
        assert parsed["sign_stable"] is False


# =============================================================================
# AblationResult
# =============================================================================


class TestAblationResult:
    def test_create(self) -> None:
        result = AblationResult(
            validation_id="abl-001",
            validation_type="ablation",
            passed=True,
            condition_name="long_term_memory",
            full_system_score=0.85,
            ablated_score=0.42,
            delta=-0.43,
            contribution_direction="positive",
        )
        assert result.condition_name == "long_term_memory"
        assert result.full_system_score == 0.85
        assert result.ablated_score == 0.42
        assert result.delta == -0.43
        assert result.contribution_direction == "positive"

    def test_delta_computation_consistency(self) -> None:
        """delta should equal ablated_score - full_system_score (or vice versa).
        The model stores delta explicitly; we just verify values."""
        result = AblationResult(
            validation_id="abl-002",
            validation_type="ablation",
            passed=True,
            condition_name="human_support_nodes",
            full_system_score=0.6,
            ablated_score=0.3,
            delta=-0.3,
            contribution_direction="positive",
        )
        assert result.delta == result.ablated_score - result.full_system_score

    def test_negative_contribution(self) -> None:
        """When removing a feature makes things better, contribution is negative."""
        result = AblationResult(
            validation_id="abl-003",
            validation_type="ablation",
            passed=True,
            condition_name="exclusive_language_model",
            full_system_score=0.4,
            ablated_score=0.7,
            delta=0.3,
            contribution_direction="negative",
        )
        assert result.contribution_direction == "negative"

    def test_to_dict(self) -> None:
        result = AblationResult(
            validation_id="abl-004",
            validation_type="ablation",
            passed=True,
            condition_name="memory",
            full_system_score=0.9,
            ablated_score=0.5,
            delta=-0.4,
            contribution_direction="positive",
        )
        d = result.to_dict()
        assert d["condition_name"] == "memory"
        assert d["full_system_score"] == 0.9
        assert d["ablated_score"] == 0.5
        assert d["delta"] == -0.4
        assert d["contribution_direction"] == "positive"

    def test_json_serializable(self) -> None:
        result = AblationResult(
            validation_id="abl-005",
            validation_type="ablation",
            passed=True,
            delta=-0.25,
            contribution_direction="positive",
            full_system_score=0.8,
            ablated_score=0.55,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["delta"] == -0.25
        assert parsed["full_system_score"] == 0.8


# =============================================================================
# AgreementResult
# =============================================================================


class TestAgreementResult:
    def test_create(self) -> None:
        result = AgreementResult(
            validation_id="agr-001",
            validation_type="agreement",
            passed=True,
            annotator_count=3,
            total_items=50,
            raw_agreement=0.86,
            cohens_kappa=0.72,
            krippendorff_alpha=0.68,
            per_label_agreement={"risky": 0.9, "safe": 0.82},
            confusion_pairs=[
                {"label_a": "risky", "label_b": "ambiguous", "count": 4},
            ],
            disagreement_cases=["case-007", "case-023"],
        )
        assert result.annotator_count == 3
        assert result.total_items == 50
        assert result.raw_agreement == 0.86
        assert result.cohens_kappa == 0.72
        assert result.krippendorff_alpha == 0.68
        assert result.per_label_agreement["risky"] == 0.9

    def test_to_dict(self) -> None:
        result = AgreementResult(
            validation_id="agr-002",
            validation_type="agreement",
            passed=False,
            annotator_count=2,
            total_items=10,
            raw_agreement=0.5,
            cohens_kappa=0.1,
            krippendorff_alpha=None,
            per_label_agreement={},
            confusion_pairs=[],
            disagreement_cases=["all"],
        )
        d = result.to_dict()
        assert d["annotator_count"] == 2
        assert d["total_items"] == 10
        assert d["raw_agreement"] == 0.5
        assert d["cohens_kappa"] == 0.1
        assert d["krippendorff_alpha"] is None
        assert d["per_label_agreement"] == {}
        assert d["confusion_pairs"] == []
        assert d["disagreement_cases"] == ["all"]

    def test_json_serializable(self) -> None:
        result = AgreementResult(
            validation_id="agr-003",
            validation_type="agreement",
            passed=True,
            annotator_count=2,
            total_items=20,
            raw_agreement=0.95,
            cohens_kappa=0.9,
            krippendorff_alpha=0.88,
            per_label_agreement={"a": 0.95, "b": 0.95},
            confusion_pairs=[{"label_a": "a", "label_b": "b", "count": 1}],
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["annotator_count"] == 2
        assert parsed["raw_agreement"] == 0.95
        assert len(parsed["confusion_pairs"]) == 1


# =============================================================================
# CalibrationResult
# =============================================================================


class TestCalibrationResult:
    def test_create(self) -> None:
        result = CalibrationResult(
            validation_id="cal-001",
            validation_type="calibration",
            passed=True,
            evaluator_name="llm_judge_v2",
            precision=0.88,
            recall=0.82,
            f1=0.85,
            per_label_metrics={
                "risky": {"precision": 0.9, "recall": 0.85, "f1": 0.87},
                "safe": {"precision": 0.86, "recall": 0.79, "f1": 0.82},
            },
            false_positives=["case-012", "case-045"],
            false_negatives=["case-033"],
            ambiguous_accuracy=0.71,
        )
        assert result.evaluator_name == "llm_judge_v2"
        assert result.precision == 0.88
        assert result.recall == 0.82
        assert result.f1 == 0.85
        assert len(result.false_positives) == 2
        assert len(result.false_negatives) == 1

    def test_to_dict(self) -> None:
        result = CalibrationResult(
            validation_id="cal-002",
            validation_type="calibration",
            passed=True,
            evaluator_name="rule_based_v1",
            precision=0.75,
            recall=0.9,
            f1=0.82,
            per_label_metrics={},
            ambiguous_accuracy=0.65,
        )
        d = result.to_dict()
        assert d["evaluator_name"] == "rule_based_v1"
        assert d["precision"] == 0.75
        assert d["recall"] == 0.9
        assert d["f1"] == 0.82
        assert d["ambiguous_accuracy"] == 0.65
        assert d["per_label_metrics"] == {}

    def test_json_serializable(self) -> None:
        result = CalibrationResult(
            validation_id="cal-003",
            validation_type="calibration",
            passed=True,
            evaluator_name="ensemble",
            precision=0.92,
            recall=0.88,
            f1=0.9,
            ambiguous_accuracy=0.8,
        )
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["evaluator_name"] == "ensemble"
        assert parsed["f1"] == 0.9


# =============================================================================
# FailureRecord
# =============================================================================


class TestFailureRecord:
    def test_create_minimal(self) -> None:
        record = FailureRecord(
            failure_id="fail-001",
            failure_type="PROVIDER_TIMEOUT",
        )
        assert record.failure_id == "fail-001"
        assert record.failure_type == "PROVIDER_TIMEOUT"
        assert record.run_id == ""
        assert record.severity == "unknown"

    def test_create_full(self) -> None:
        record = FailureRecord(
            failure_id="fail-002",
            failure_type="SEED_INSTABILITY",
            run_id="run-abc",
            episode_id="ep-042",
            provider_name="openai",
            metric_name="sycophancy",
            evidence={"scores": [0.3, 0.8], "n_runs": 10},
            config_snapshot={"seed": 42, "policy": "bounded_supportive"},
            severity="high",
        )
        assert record.run_id == "run-abc"
        assert record.episode_id == "ep-042"
        assert record.provider_name == "openai"
        assert record.metric_name == "sycophancy"
        assert record.evidence["n_runs"] == 10
        assert record.config_snapshot["seed"] == 42
        assert record.severity == "high"

    def test_to_dict(self) -> None:
        record = FailureRecord(
            failure_id="fail-003",
            failure_type="PROVIDER_REFUSAL",
            run_id="run-xyz",
            episode_id="ep-999",
            provider_name="anthropic",
            metric_name="reality_grounding",
            evidence={"error_message": "Content policy refusal"},
            config_snapshot={"model": "claude-sonnet-5"},
            severity="high",
        )
        d = record.to_dict()
        assert d["failure_id"] == "fail-003"
        assert d["failure_type"] == "PROVIDER_REFUSAL"
        assert d["run_id"] == "run-xyz"
        assert d["episode_id"] == "ep-999"
        assert d["provider_name"] == "anthropic"
        assert d["metric_name"] == "reality_grounding"
        assert d["severity"] == "high"
        assert "evidence" in d
        assert "config_snapshot" in d

    def test_json_serializable(self) -> None:
        record = FailureRecord(
            failure_id="fail-004",
            failure_type="INVALID_STRUCTURED_OUTPUT",
            run_id="run-001",
            episode_id="ep-001",
            severity="medium",
        )
        json_str = json.dumps(record.to_dict())
        parsed = json.loads(json_str)
        assert parsed["failure_id"] == "fail-004"
        assert parsed["severity"] == "medium"

    def test_evidence_default_empty_dict(self) -> None:
        record = FailureRecord(
            failure_id="fail-005",
            failure_type="UNSUPPORTED_CLAIM",
        )
        assert record.evidence == {}
        assert record.config_snapshot == {}


# =============================================================================
# FAILURE_TAXONOMY_V1
# =============================================================================


class TestFailureTaxonomy:
    def test_has_exactly_18_entries(self) -> None:
        assert len(FAILURE_TAXONOMY_V1) == 18

    def test_all_expected_keys_present(self) -> None:
        expected_keys = {
            "PROMPT_SENSITIVITY",
            "SEED_INSTABILITY",
            "SIMULATOR_DEPENDENCE",
            "JUDGE_DISAGREEMENT",
            "RULE_FALSE_POSITIVE",
            "RULE_FALSE_NEGATIVE",
            "CONTEXT_TRUNCATION",
            "MEMORY_INCONSISTENCY",
            "EVENT_NORMALIZATION_FAILURE",
            "PROVIDER_TIMEOUT",
            "PROVIDER_REFUSAL",
            "INVALID_STRUCTURED_OUTPUT",
            "TRANSITION_PARAMETER_INSTABILITY",
            "SCENARIO_LEAKAGE",
            "LABEL_AMBIGUITY",
            "SELF_EVALUATION_RISK",
            "CACHE_REPLAY_MISMATCH",
            "UNSUPPORTED_CLAIM",
        }
        assert set(FAILURE_TAXONOMY_V1.keys()) == expected_keys

    def test_all_values_are_nonempty_strings(self) -> None:
        for key, description in FAILURE_TAXONOMY_V1.items():
            assert isinstance(key, str)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_json_serializable(self) -> None:
        json_str = json.dumps(FAILURE_TAXONOMY_V1)
        parsed = json.loads(json_str)
        assert len(parsed) == 18


# =============================================================================
# All to_dict() produces JSON-serializable output (parametrized)
# =============================================================================


class TestDictSerialization:
    """Verify that every result subclass produces JSON-serializable output."""

    @pytest.mark.parametrize(
        "result",
        [
            ValidationResult(validation_id="v1", validation_type="t", passed=True),
            SeedRobustnessResult(
                validation_id="v2",
                validation_type="seed_robustness",
                passed=True,
                scores=[0.1, 0.2],
                mean=0.15,
                median=0.15,
                std=0.05,
                min_score=0.1,
                max_score=0.2,
                rank_stable=True,
                sign_stable=True,
                failure_rate=0.0,
            ),
            PerturbationResult(
                validation_id="v3",
                validation_type="prompt_perturbation",
                passed=True,
                score_variance=0.01,
                is_stable=True,
            ),
            MetamorphicResult(
                validation_id="v4",
                validation_type="metamorphic",
                passed=True,
                expected_direction="increase",
                actual_direction="increase",
                transformation_passed=True,
                pre_score=0.5,
                post_score=0.7,
            ),
            SensitivityResult(
                validation_id="v5",
                validation_type="sensitivity",
                passed=True,
                parameter_name="temp",
                sign_stable=True,
                rank_stable=True,
                threshold_crossings=0,
            ),
            AblationResult(
                validation_id="v6",
                validation_type="ablation",
                passed=True,
                delta=-0.3,
                contribution_direction="positive",
                full_system_score=0.8,
                ablated_score=0.5,
            ),
            AgreementResult(
                validation_id="v7",
                validation_type="agreement",
                passed=True,
                annotator_count=2,
                total_items=10,
                raw_agreement=1.0,
            ),
            CalibrationResult(
                validation_id="v8",
                validation_type="calibration",
                passed=True,
                evaluator_name="test",
                precision=1.0,
                recall=1.0,
                f1=1.0,
                ambiguous_accuracy=1.0,
            ),
            FailureRecord(
                failure_id="v9",
                failure_type="TEST",
            ),
        ],
        ids=[
            "ValidationResult",
            "SeedRobustnessResult",
            "PerturbationResult",
            "MetamorphicResult",
            "SensitivityResult",
            "AblationResult",
            "AgreementResult",
            "CalibrationResult",
            "FailureRecord",
        ],
    )
    def test_json_serializable(self, result) -> None:  # type: ignore[no-untyped-def]
        d = result.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed is not None
