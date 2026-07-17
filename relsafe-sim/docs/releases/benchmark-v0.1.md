# Benchmark Card ！ RelSafe Sim v0.1.0

**Status: RESEARCH PREVIEW ！ PILOT CALIBRATED ！ NOT FOR CLINICAL USE ！ NOT FOR AUTOMATED CERTIFICATION**

## Intended Use
Controlled simulation-based product risk evaluation of AI companion systems.
Compares companion policies under identical simulated conditions.
Generates hypotheses for human-subject research (must be separately validated).

## Inappropriate Use
- Clinical diagnosis or real-user psychological assessment
- Model safety ranking or certification
- Real-world harm prediction
- Regulatory compliance
- Determining "safe" vs "unsafe" thresholds

## Metrics (v0.1.0)

| Metric | Confidence Tier | Ensemble F1 | Status |
|--------|----------------|-------------|--------|
| A4 conflict_escalation | TIER 1 | 0.923 | PILOT SUPPORTED |
| A2 belief_reinforcement | TIER 2 | 0.769 | SEMANTIC JUDGE |
| B1 feeling_fact_separation | TIER 2 | 0.900 | SEMANTIC JUDGE |
| A3 exclusive_validation | TIER 2 | 0.545 | SEMANTIC JUDGE (rule LOW) |
| B5 human_support_referral | TIER 2 | 0.500 | SEMANTIC JUDGE |
| C1 guilt_based_retention | TIER 2 | 1.000 | SEMANTIC JUDGE (low prevalence) |
| A1/A5/C3/C5 | LOW | < 0.5 | REQUIRES HUMAN REVIEW |

## Calibration
- Human sample: 44 items (PILOT ！ NOT GENERALIZABLE)
- Median per-label kappa: 1.000
- Ensemble macro F1: 0.418

## Synthetic Data
All personas, conversations, and test fixtures are synthetic.
No real user data is collected or processed.

## Reproducibility
- Same seed + config + code version = identical results
- Real responses recorded for offline replay
- All components versioned and frozen

## Known Limitations
1. Chinese phrase coverage insufficient for A1/A3/A5
2. C3 boundary_respect label definition under revision (m5h-002)
3. Short episodes only (8-12 steps); longitudinal validation is exploratory
4. Calibrated on 44 pilot items only
5. Concordia engine equivalence not yet validated
