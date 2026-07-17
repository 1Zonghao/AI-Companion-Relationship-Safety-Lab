"""EvaluatorOutput and Evaluator Protocol.

Evaluators identify evidence; metrics define what to measure.
This separation ensures metrics can be recomputed with different evaluators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class ScoreDirection(StrEnum):
    """Explicit annotation of what a higher score means.

    Every metric MUST declare its direction so report consumers
    never guess whether 0.9 is good or bad.
    """

    HIGHER_IS_MORE_RISK = "HIGHER_IS_MORE_RISK"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"


class EvaluatorType(StrEnum):
    """Identifies the type of evaluator that produced an observation."""

    RULE_BASED = "rule_based"
    FAKE_JUDGE = "fake_judge"
    LLM_JUDGE = "llm_judge"
    ENSEMBLE = "ensemble"


@dataclass(frozen=True, slots=True)
class EvaluatorOutput:
    """Structured output from a single evaluator.

    An evaluator receives a structured task and returns this output.
    It does NOT produce a final MetricResult — the metric does that.
    """

    evaluator_type: EvaluatorType
    evaluator_version: str
    episode_id: str
    observation_id: str
    subject_id: str = ""
    step_range: tuple[int, int] = (0, 0)
    metric_name: str = ""

    # Scoring
    score: float = 0.0
    score_direction: ScoreDirection = ScoreDirection.HIGHER_IS_MORE_RISK
    confidence: str = "LOW"  # LOW, MEDIUM, HIGH
    confidence_type: str = "rule_coverage"

    # Evidence
    evidence_event_ids: list[str] = field(default_factory=list)
    evidence_excerpt: str = ""
    reason_codes: list[str] = field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = field(default_factory=list)

    # Extra context
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_type": self.evaluator_type.value,
            "evaluator_version": self.evaluator_version,
            "episode_id": self.episode_id,
            "observation_id": self.observation_id,
            "subject_id": self.subject_id,
            "step_range": list(self.step_range),
            "metric_name": self.metric_name,
            "score": self.score,
            "score_direction": self.score_direction.value,
            "confidence": self.confidence,
            "confidence_type": self.confidence_type,
            "evidence_event_ids": list(self.evidence_event_ids),
            "evidence_excerpt": self.evidence_excerpt,
            "reason_codes": list(self.reason_codes),
            "explanation": self.explanation,
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }


@runtime_checkable
class Evaluator(Protocol):
    """Protocol for all evaluators.

    An evaluator receives a structured evaluation task (dict) and
    returns a structured EvaluatorOutput.  It must NOT produce a
    final MetricResult — that is the metric's responsibility.
    """

    @property
    def evaluator_type(self) -> EvaluatorType:
        """The type of this evaluator."""
        ...

    @property
    def version(self) -> str:
        """Evaluator version string."""
        ...

    def evaluate(self, task: dict[str, Any]) -> EvaluatorOutput:
        """Evaluate a task and return structured output.

        The task dict contains metric-specific instructions and evidence.
        """
        ...
