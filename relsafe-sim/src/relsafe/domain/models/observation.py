"""Observation — structured metric observations, scoring results, and
aggregated metric outcomes.

This is the unified output contract for all metrics in the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from relsafe.domain.models.evaluator_output import ScoreDirection


@dataclass(frozen=True, slots=True)
class MetricObservation:
    """A single point-in-time metric evaluation with full traceability.

    This replaces the earlier minimal version with complete evidence
    tracking, confidence annotation, and reason codes.
    """

    observation_id: str
    metric_name: str
    metric_version: str
    episode_id: str
    run_id: str = ""
    step: int = 0
    step_range: tuple[int, int] = (0, 0)
    subject_id: str = ""

    # Scoring
    score: float = 0.0
    score_direction: ScoreDirection = ScoreDirection.HIGHER_IS_MORE_RISK
    confidence: str = "LOW"
    confidence_type: str = "rule_coverage"

    # Evidence
    evidence_event_ids: list[str] = field(default_factory=list)
    evidence_excerpt: str = ""
    evaluator_type: str = "rule_based"
    reason_codes: list[str] = field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = field(default_factory=list)

    # Raw evaluator outputs (for ensemble/debug)
    raw_evaluator_outputs: list[dict[str, Any]] = field(default_factory=list)

    # Extra
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "metric_name": self.metric_name,
            "metric_version": self.metric_version,
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "step": self.step,
            "step_range": list(self.step_range),
            "subject_id": self.subject_id,
            "score": self.score,
            "score_direction": self.score_direction.value,
            "confidence": self.confidence,
            "confidence_type": self.confidence_type,
            "evidence_event_ids": list(self.evidence_event_ids),
            "evidence_excerpt": self.evidence_excerpt,
            "evaluator_type": self.evaluator_type,
            "reason_codes": list(self.reason_codes),
            "explanation": self.explanation,
            "warnings": list(self.warnings),
            "raw_evaluator_outputs": self.raw_evaluator_outputs,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Aggregated result for one metric across an entire episode.

    A metric collects N observations (potentially from multiple
    evaluators) and aggregates them into a single result.
    """

    metric_name: str
    metric_version: str
    episode_id: str
    run_id: str = ""

    # Status
    valid: bool = True
    not_applicable: bool = False
    failure_reason: str | None = None

    # Aggregated scores
    aggregate_score: float = 0.0
    score_direction: ScoreDirection = ScoreDirection.HIGHER_IS_MORE_RISK
    observation_count: int = 0
    component_scores: dict[str, float] = field(default_factory=dict)
    observations: list[MetricObservation] = field(default_factory=list)

    # Quality
    warnings: list[str] = field(default_factory=list)
    evaluator_versions: dict[str, str] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    # Extra
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "metric_version": self.metric_version,
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "valid": self.valid,
            "not_applicable": self.not_applicable,
            "failure_reason": self.failure_reason,
            "aggregate_score": self.aggregate_score,
            "score_direction": self.score_direction.value,
            "observation_count": self.observation_count,
            "component_scores": dict(self.component_scores),
            "observations": [o.to_dict() for o in self.observations],
            "warnings": list(self.warnings),
            "evaluator_versions": dict(self.evaluator_versions),
            "limitations": list(self.limitations),
            "metadata": self.metadata,
        }


# Keep backward compatibility
@dataclass(frozen=True, slots=True)
class DimensionScore:
    """Aggregated score for one risk dimension across an episode.

    Deprecated: prefer MetricResult for new code.
    """

    dimension: str
    mean: float
    std: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    observation_count: int = 0
    failed: bool = False
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "mean": self.mean,
            "std": self.std,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "observation_count": self.observation_count,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
        }
