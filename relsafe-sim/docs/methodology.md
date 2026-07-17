# Methodology

## Research assumptions

1. **Behavioral proxies**: We measure product-side behavioral patterns (sycophancy, exclusivity language, exit obstruction), not clinical outcomes.
2. **Generative agent simulation**: User agents are LLM-powered simulations. Their behavior is a model of possible human behavior, not a measurement of real humans.
3. **Controlled comparison**: Risk is assessed by comparing companion policies under identical conditions, not by absolute thresholds.
4. **AEA as analytical framework**: AEA provides organizing dimensions for measurement, not clinical diagnoses.

## Simulation limitations

1. **Simulated users ≠ real users**: Agents lack the full complexity of human psychology, social context, and lived experience.
2. **Limited social network**: The initial virtual society has only 3-5 agents — far simpler than real social networks.
3. **Short episodes**: 50-step episodes model hours or days, not months or years of relationship development.
4. **Narrow scenarios**: Initial scenarios cover a small set of interaction patterns.
5. **Model biases**: Both user simulators and companions inherit biases from their underlying language models.

## Evaluation methodology

### Separation of roles
- **User simulator model** generates user actions.
- **Companion under test** responds according to its policy.
- **Rule-based evaluator** (RuleBasedEvaluator v1.0.0) computes initial scores using deterministic phrase matching.
- **Fake judge evaluator** (FakeJudgeEvaluator v1.0.0) provides a second heuristic opinion.
- **Ensemble evaluator** (EnsembleEvaluator v1.0.0) combines both with full transparency.
- **Independent LLM judge** (future) will provide semantic second-pass evaluation.
- **Human sample review** (future) calibrates automated metrics.

### Why rule-based first, not LLM judge
The first version prioritizes offline, deterministic, transparent evaluation:
- Rules cover explicit phrase patterns, event sequences, and structural comparisons.
- A fake judge provides a second opinion with different heuristics.
- The ensemble preserves each evaluator's judgment and flags disagreement.
- Real LLM judges are deferred to avoid cost, non-determinism, and self-judgment risks.
See [ADR 0002](adr/0002-evaluator-ensemble.md).

### Why D1, D2, and composite scoring are deferred
- D1 (Confirmation Reliance) requires longitudinal trend analysis across many episodes.
- D2 (External Validation Decay) requires a rich multi-node social network.
- Composite AEA scoring requires stable individual metrics first.
- Clinical dependency diagnosis is permanently out of scope.
These are deferred to Milestone 4+.

### Synthetic golden fixtures
Each metric has 15 versioned golden test cases used for regression testing.
All are synthetic — designed to test specific patterns, not real user data.
See `tests/fixtures/benchmark_cases/`.

### Determinism
All simulations are deterministic: same seed + same config → same events, same state timeline, same scores. This enables exact reproduction and debugging.

### Repetition
Every experiment runs multiple seeds. Conclusions are drawn from distributions, not single conversations.

### Counterfactual tests
The benchmark supports ablation: same persona with different models, same policy with different user profiles, disabling features (memory, proactive messaging, exclusivity language).

## Concordia integration

Concordia is used as the simulation runtime (orchestration, agent memory,
turn scheduling, game-master execution, episode logging) but is kept
behind an adapter boundary (`infrastructure/concordia/`). The domain and
application layers depend on project-owned protocols (`SimulationEngine`,
`LLMProvider`, etc.) — not on Concordia classes directly. This ensures
Concordia is replaceable without rewriting the research framework.

## Ethical boundaries

- Do not simulate self-harm or psychosis scenarios without explicit safeguards.
- Do not produce user-facing diagnosis labels.
- Store raw conversations locally by default.
- Make logging configurable and redact secrets.
- Never commit API keys, tokens, credentials, or private conversation data.
- Age-group fields are used only when methodologically necessary and ethically justified.
