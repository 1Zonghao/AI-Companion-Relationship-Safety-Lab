# Validation Plan

**Status:** Draft — Milestone 3

## Internal validation

### Regression testing
- 60 golden fixtures across 4 metrics (15 each)
- Every metric change runs regression via `python -m relsafe.cli.main benchmark`
- Expected score ranges validated per fixture

### Cross-evaluator agreement
- RuleBasedEvaluator vs FakeJudgeEvaluator score correlation
- Ensemble disagreement rate tracked
- Future: inter-evaluator agreement statistics

### Seed stability
- Same seed × same metric × same events = identical scores
- Verified by contract tests

## Public case calibration

### Planned
- Identify publicly documented AI companion interaction patterns
- Adapt into anonymized test cases
- Compare automated metric scores against published expert analyses

### Status: Not yet started (Milestone 4+)

## Cross-model validation

### Planned
- Run same metrics with different judge models
- Compare score distributions across model families
- Identify model-specific biases in metric scoring

### Status: Not yet started (requires real LLM access)

## Human calibration

### Planned
- Export metric results via `export-human-review` CLI
- Have 2+ independent reviewers rate the same conversation excerpts
- Compute inter-rater reliability (Cohen's kappa, Krippendorff's alpha)
- Calibrate automated score thresholds against human judgments

### Status: Export format defined, review process not yet conducted

## Threshold validation

**Important: Metric thresholds are NOT empirically validated.**

Current score thresholds (0.0–1.0) are normalized representations of
rule-matching density. They do NOT represent:
- Probability of real-world harm
- Clinical significance
- Population prevalence
- Validated risk categories

Threshold validation requires:
1. Human calibration studies
2. Cross-model consistency checks
3. Real-world outcome correlation (if ethically feasible)
4. Expert consensus panels

Until these are completed, scores should be interpreted as
"density of pattern matches" not "risk probability."
