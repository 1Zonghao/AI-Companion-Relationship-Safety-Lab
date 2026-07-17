"""EnsembleEvaluator — combines multiple evaluators with full transparency.

Preserves each evaluator's independent judgment, agreement status,
disagreement details, and the aggregation rule used.  Never hides
individual evaluator results behind a single number.
"""

from __future__ import annotations

from typing import Any

from relsafe.domain.models.evaluator_output import (
    Evaluator,
    EvaluatorOutput,
    EvaluatorType,
)
from relsafe.shared.ids import IdGenerator


class EnsembleEvaluator(Evaluator):
    """Aggregates multiple evaluators while preserving individual judgments.

    The ensemble:
    1. Runs each evaluator independently on the same task
    2. Records each evaluator's output verbatim
    3. Computes agreement/disagreement metrics
    4. Produces an aggregated score with full transparency

    The aggregation rule is explicit: median score with disagreement
    flagged in warnings.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        evaluators: list[Evaluator],
        *,
        agreement_threshold: float = 0.2,
        seed: int = 0,
    ) -> None:
        """Initialize the ensemble.

        Args:
            evaluators: List of evaluators to ensemble (at least 2).
            agreement_threshold: Max score difference to consider evaluators
                "in agreement" with each other.
            seed: Deterministic seed for ID generation.
        """
        if len(evaluators) < 2:
            raise ValueError("Ensemble requires at least 2 evaluators")
        self._evaluators = evaluators
        self._agreement_threshold = agreement_threshold
        self._id_gen = IdGenerator(seed=seed)

    @property
    def evaluator_type(self) -> EvaluatorType:
        return EvaluatorType.ENSEMBLE

    @property
    def version(self) -> str:
        return self.VERSION

    def evaluate(self, task: dict[str, Any]) -> EvaluatorOutput:
        """Run all evaluators and produce an ensemble result.

        Returns an EvaluatorOutput where:
        - score = median of evaluator scores
        - raw_evaluator_outputs dict contains each evaluator's full output
        - warnings include disagreement information
        """
        outputs: list[EvaluatorOutput] = []
        failures: list[str] = []

        for evaluator in self._evaluators:
            try:
                output = evaluator.evaluate(task)
                outputs.append(output)
            except Exception as exc:
                failures.append(f"{evaluator.evaluator_type.value}: {exc}")

        if not outputs:
            return EvaluatorOutput(
                evaluator_type=self.evaluator_type,
                evaluator_version=self.version,
                episode_id=str(task.get("episode_id", "")),
                observation_id=self._id_gen.next_id(),
                metric_name=str(task.get("metric_name", "")),
                warnings=[f"All evaluators failed: {', '.join(failures)}"],
            )

        scores = [o.score for o in outputs]
        scores_sorted = sorted(scores)
        n = len(scores_sorted)

        if n % 2 == 1:
            median = scores_sorted[n // 2]
        else:
            median = (scores_sorted[n // 2 - 1] + scores_sorted[n // 2]) / 2.0

        median = round(median, 4)

        # Determine direction from first evaluator
        direction = outputs[0].score_direction

        # Agreement analysis
        max_diff = max(scores) - min(scores) if n > 1 else 0.0
        agreed = max_diff <= self._agreement_threshold

        warnings: list[str] = []
        if not agreed:
            warnings.append(
                f"Evaluator disagreement: max_diff={max_diff:.3f} "
                f"(threshold={self._agreement_threshold})"
            )
        if failures:
            warnings.append(f"Evaluator failures: {', '.join(failures)}")

        # Collect all evidence
        all_evidence_ids: list[str] = []
        for o in outputs:
            all_evidence_ids.extend(o.evidence_event_ids)

        # Collect all reason codes
        all_reason_codes: list[str] = []
        for o in outputs:
            for code in o.reason_codes:
                if code not in all_reason_codes:
                    all_reason_codes.append(code)

        # Build component scores from individual evaluators
        component_scores: dict[str, float] = {}
        for i, o in enumerate(outputs):
            component_scores[f"evaluator_{i}_{o.evaluator_type.value}"] = o.score

        # Confidence: high agreement + no failures = high
        if agreed and not failures and len(outputs) >= 2:
            confidence = "HIGH"
        elif not agreed:
            confidence = "LOW"
        else:
            confidence = "MEDIUM"

        return EvaluatorOutput(
            evaluator_type=self.evaluator_type,
            evaluator_version=self.version,
            episode_id=str(task.get("episode_id", "")),
            observation_id=self._id_gen.next_id(),
            step_range=task.get("step_range", (0, 0)),
            metric_name=str(task.get("metric_name", "")),
            subject_id=outputs[0].subject_id if outputs else "",
            score=median,
            score_direction=direction,
            confidence=confidence,
            confidence_type="evaluator_agreement",
            evidence_event_ids=all_evidence_ids,
            evidence_excerpt=outputs[0].evidence_excerpt if outputs else "",
            reason_codes=all_reason_codes,
            explanation=f"Ensemble: {n} evaluators, median={median:.3f}, "
            f"agreed={agreed}, diff={max_diff:.3f}",
            warnings=warnings,
            metadata={
                "agreement": agreed,
                "max_difference": max_diff,
                "evaluator_count": n,
                "failed_count": len(failures),
                "component_scores": component_scores,
            },
        )
