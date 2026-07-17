# Architecture

## Dependency direction

Dependencies must point inward:

```text
interfaces / CLI / reports
          ↓
application services / use cases
          ↓
domain models / rules / protocols
          ↑
infrastructure adapters
  Concordia / LLM APIs / storage
```

The domain layer must never import from `infrastructure`.

## Module boundaries

### `relsafe/domain/models/`
Immutable data structures. `UserState`, `PersonaProfile`, `RelationshipEdge`, `CompanionPolicy`, `PlatformIntervention`, and result types. Zero external dependencies beyond stdlib + Pydantic.

### `relsafe/domain/events/`
Normalized event value objects. Each event is a frozen dataclass with a `to_dict()` serializer. Event types: `USER_ACTION_SELECTED`, `COMPANION_RESPONSE_GENERATED`, `HUMAN_CONTACT_RESPONSE_GENERATED`, `PLATFORM_INTERVENTION_APPLIED`, `MEMORY_CHANGED`, `EXIT_REQUESTED`, `EXIT_HONORED`, `STATE_UPDATED`, `METRIC_OBSERVED`.

### `relsafe/domain/protocols/`
Structural interfaces (Python Protocols). `LLMProvider`, `SimulationEngine`, `Metric`, `StateTransition`, `EventStore`, `ResultRepository`. Application code depends on these, not on concrete implementations.

### `relsafe/domain/rules/`
Pure functions for state transitions, exit handling, continuity calculation, and safety checks. No I/O, no randomness — fully deterministic.

### `relsafe/application/`
Use-case orchestrators. `run_episode.py` runs a single deterministic episode. `run_experiment.py` repeats episodes across a config matrix. `validate_config.py` validates experiment configs before execution.

### `relsafe/infrastructure/`
Concrete implementations of domain protocols. `FakeLLMProvider` for offline testing. `InMemoryEventStore` / `JSONLEventStore` for persistence. Concordia adapter, real LLM providers, and SQLite storage will be added in later milestones.

### `relsafe/shared/`
Cross-cutting utilities: `DeterministicClock`, `IdGenerator`, domain exceptions, logging configuration.

## Extension points

1. **New LLM provider**: Implement `LLMProvider` protocol in `infrastructure/llm/`.
2. **New metric**: Implement `Metric` protocol in a new file under a future `metrics/` package.
3. **New engine**: Implement `SimulationEngine` protocol (e.g., `ConcordiaSimulationEngine`).
4. **New event store**: Implement `EventStore` protocol.

## Concordia adapter boundary

Concordia integration is implemented in Milestone 2. All Concordia-specific code lives in `infrastructure/concordia/`. The domain layer never imports Concordia types.

### Adapter components

| Component | File | Purpose |
|---|---|---|
| `ConcordiaSimulationEngine` | `infrastructure/concordia/engine_adapter.py` | Main engine implementing `SimulationEngine` Protocol |
| `LLMProviderToConcordiaAdapter` | `infrastructure/concordia/language_model_adapter.py` | Wraps RelSafe `LLMProvider` as Concordia `LanguageModel` |
| `build_user_agent` / `build_companion_agent` | `infrastructure/concordia/agent_adapter.py` | Build Concordia agents from `PersonaProfile` / `CompanionPolicy` |
| `build_game_master` | `infrastructure/concordia/game_master_adapter.py` | Build Concordia GameMaster from prefabs |
| `ConcordiaMemoryAdapter` | `infrastructure/concordia/memory_adapter.py` | Wraps `AssociativeMemoryBank` with simplified API |
| `EventNormalizer` | `infrastructure/concordia/event_normalizer.py` | Converts Concordia outputs to RelSafe event dicts |
| `InMemorySimulationEngine` | `infrastructure/in_memory_engine.py` | Wraps `DeterministicEpisodeRunner` as a `SimulationEngine` |

### Dual-engine contract

Both `InMemorySimulationEngine` and `ConcordiaSimulationEngine` implement the same `SimulationEngine` Protocol:
- Accept `EpisodeSpec` (with `persona`, `companion_policy`, `intervention`, `seed`, `num_steps`)
- Return `EpisodeResult` (with `state_timeline`, `event_count`, `final_state`)
- Are tested by shared contract tests in `tests/contract/test_simulation_engine_contract.py`

### Concordia version

`gdm-concordia==2.4.0` (installed from GitHub). See [ADR 0001](adr/0001-concordia-adapter-boundary.md).

## Data flow

```text
Config (YAML) → validate_config → run_experiment
    → run_episode (per persona × policy × seed)
        → select action → generate response → apply transitions
        → emit events → update state → repeat
    → EpisodeResult × N → ExperimentResult
```
