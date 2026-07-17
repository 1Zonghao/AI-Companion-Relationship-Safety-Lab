"""Validation contracts — versioned result types for all validation activities.

All validators return typed results. No validator modifies original data.

This module imports ONLY EpisodeResult, MetricResult, and ExperimentResult
from the domain layer. No Concordia or vendor SDK types are imported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALIDATION_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class ValidationResult:
    """Base validation result — all validators return this or a subclass."""

    validation_id: str
    validation_type: str  # "seed_robustness", "prompt_perturbation", etc.
    passed: bool
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    version: str = VALIDATION_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "validation_type": self.validation_type,
            "passed": self.passed,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "version": self.version,
        }


@dataclass(frozen=True)
class SeedRobustnessResult(ValidationResult):
    """Results of seed robustness testing."""

    condition_id: str = ""
    metric_name: str = ""
    scores: list[float] = field(default_factory=list)
    mean: float = 0.0
    median: float = 0.0
    std: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    rank_stable: bool = True
    sign_stable: bool = True
    failure_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "condition_id": self.condition_id,
                "metric_name": self.metric_name,
                "scores": self.scores,
                "mean": self.mean,
                "median": self.median,
                "std": self.std,
                "min_score": self.min_score,
                "max_score": self.max_score,
                "rank_stable": self.rank_stable,
                "sign_stable": self.sign_stable,
                "failure_rate": self.failure_rate,
            }
        )
        return base


@dataclass(frozen=True)
class PerturbationResult(ValidationResult):
    """Results of prompt perturbation testing."""

    case_id: str = ""
    base_text: str = ""
    variants: list[str] = field(default_factory=list)
    variant_scores: list[dict[str, float]] = field(default_factory=list)
    score_variance: float = 0.0
    is_stable: bool = True  # variance within acceptable range

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "case_id": self.case_id,
                "score_variance": self.score_variance,
                "is_stable": self.is_stable,
                "variant_count": len(self.variants),
            }
        )
        return base


@dataclass(frozen=True)
class MetamorphicResult(ValidationResult):
    """Results of metamorphic testing."""

    source_case_id: str = ""
    transformation_id: str = ""
    expected_direction: str = ""  # "increase", "decrease", "no_change"
    actual_direction: str = ""
    transformation_passed: bool = False
    pre_score: float = 0.0
    post_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "source_case_id": self.source_case_id,
                "transformation_id": self.transformation_id,
                "expected_direction": self.expected_direction,
                "actual_direction": self.actual_direction,
                "transformation_passed": self.transformation_passed,
                "pre_score": self.pre_score,
                "post_score": self.post_score,
            }
        )
        return base


@dataclass(frozen=True)
class SensitivityResult(ValidationResult):
    """Results of parameter sensitivity analysis."""

    parameter_name: str = ""
    baseline_value: float = 0.0
    test_values: list[float] = field(default_factory=list)
    outcome_values: list[float] = field(default_factory=list)
    sign_stable: bool = True
    rank_stable: bool = True
    threshold_crossings: int = 0
    unstable_conclusions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "parameter_name": self.parameter_name,
                "baseline_value": self.baseline_value,
                "test_values": self.test_values,
                "sign_stable": self.sign_stable,
                "rank_stable": self.rank_stable,
                "threshold_crossings": self.threshold_crossings,
            }
        )
        return base


@dataclass(frozen=True)
class AblationResult(ValidationResult):
    """Results of ablation study."""

    condition_name: str = ""
    full_system_score: float = 0.0
    ablated_score: float = 0.0
    delta: float = 0.0
    contribution_direction: str = ""  # "positive", "negative", "neutral"

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "condition_name": self.condition_name,
                "full_system_score": self.full_system_score,
                "ablated_score": self.ablated_score,
                "delta": self.delta,
                "contribution_direction": self.contribution_direction,
            }
        )
        return base


@dataclass(frozen=True)
class AgreementResult(ValidationResult):
    """Results of inter-rater agreement analysis."""

    annotator_count: int = 0
    total_items: int = 0
    raw_agreement: float = 0.0
    cohens_kappa: float | None = None
    krippendorff_alpha: float | None = None
    per_label_agreement: dict[str, float] = field(default_factory=dict)
    confusion_pairs: list[dict[str, Any]] = field(default_factory=list)
    disagreement_cases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "annotator_count": self.annotator_count,
                "total_items": self.total_items,
                "raw_agreement": self.raw_agreement,
                "cohens_kappa": self.cohens_kappa,
                "krippendorff_alpha": self.krippendorff_alpha,
                "per_label_agreement": self.per_label_agreement,
                "confusion_pairs": self.confusion_pairs,
                "disagreement_cases": self.disagreement_cases,
            }
        )
        return base


@dataclass(frozen=True)
class CalibrationResult(ValidationResult):
    """Results of evaluator calibration against human labels."""

    evaluator_name: str = ""
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    per_label_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    false_positives: list[str] = field(default_factory=list)
    false_negatives: list[str] = field(default_factory=list)
    ambiguous_accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "evaluator_name": self.evaluator_name,
                "precision": self.precision,
                "recall": self.recall,
                "f1": self.f1,
                "per_label_metrics": self.per_label_metrics,
                "ambiguous_accuracy": self.ambiguous_accuracy,
            }
        )
        return base


@dataclass(frozen=True)
class FailureRecord:
    """A single classified failure with full traceability."""

    failure_id: str
    failure_type: str  # from FailureTaxonomy
    run_id: str = ""
    episode_id: str = ""
    provider_name: str = ""
    metric_name: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    severity: str = "unknown"  # "critical", "high", "medium", "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "failure_type": self.failure_type,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "provider_name": self.provider_name,
            "metric_name": self.metric_name,
            "evidence": self.evidence,
            "config_snapshot": self.config_snapshot,
            "severity": self.severity,
        }


FAILURE_TAXONOMY_V1: dict[str, str] = {
    "PROMPT_SENSITIVITY": (
        "Metric scores change substantially with semantically equivalent prompt rewrites"
    ),
    "SEED_INSTABILITY": "Metric score rankings or signs invert across different seeds",
    "SIMULATOR_DEPENDENCE": "Conclusions change when user simulator model changes",
    "JUDGE_DISAGREEMENT": "Evaluators disagree beyond acceptable threshold on same input",
    "RULE_FALSE_POSITIVE": "Rule-based evaluator flags safe content as risky",
    "RULE_FALSE_NEGATIVE": "Rule-based evaluator misses genuine risk pattern",
    "CONTEXT_TRUNCATION": "Long conversation context exceeded model or evaluator limits",
    "MEMORY_INCONSISTENCY": "Simulated memory state contradicts event history",
    "EVENT_NORMALIZATION_FAILURE": "Event emitted with missing or malformed fields",
    "PROVIDER_TIMEOUT": "Model provider request timed out",
    "PROVIDER_REFUSAL": "Model provider refused the request",
    "INVALID_STRUCTURED_OUTPUT": "Judge model returned unparseable JSON",
    "TRANSITION_PARAMETER_INSTABILITY": "Small parameter changes cause large outcome changes",
    "SCENARIO_LEAKAGE": "Risk signals from scenario text bleed into metric scoring",
    "LABEL_AMBIGUITY": "Human annotators disagree beyond acceptable threshold",
    "SELF_EVALUATION_RISK": "Same model used as companion and judge",
    "CACHE_REPLAY_MISMATCH": "Replayed response differs from original recorded response",
    "UNSUPPORTED_CLAIM": "Code or report makes claim beyond what the simulation supports",
}
