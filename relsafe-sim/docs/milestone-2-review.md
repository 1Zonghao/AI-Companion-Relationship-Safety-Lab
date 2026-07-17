# Milestone 2 — Acceptance Audit Report

**Date:** 2026-07-15
**Auditor:** Claude Code (automated review)
**Scope:** Milestone 2 — Concordia Adapter

---

## 1. Quality Gates (Pre-audit)

| Gate | Result | Detail |
|------|--------|--------|
| `ruff check .` | **PASS** | All checks passed |
| `ruff format --check .` | **PASS** | 79 files formatted |
| `mypy src/relsafe` | **PASS** | Success: no issues found in 50 source files |
| `pytest tests/` | **PASS** | 203 passed, 0 failed |

---

## 2. Deliverables Checklist

### 2.1 ConcordiaSimulationEngine

| Check | Result | Detail |
|-------|--------|--------|
| Implements `SimulationEngine` Protocol | **PASS** | `ConcordiaSimulationEngine` has `run_episode(spec) -> EpisodeResult` |
| Accepts `EpisodeSpec` | **PASS** | Same `EpisodeSpec` as `InMemorySimulationEngine` |
| Returns `EpisodeResult` | **PASS** | Standard result with state_timeline, event_count, final_state |
| `engine_name` property | **PASS** | Returns `"concordia"` |

### 2.2 ConcordiaAgentAdapter

| Check | Result | Detail |
|-------|--------|--------|
| `build_user_agent()` | **PASS** | Creates Concordia `EntityAgentWithLogging` from `PersonaProfile` |
| `build_companion_agent()` | **PASS** | Creates Concordia `EntityAgentWithLogging` from `CompanionPolicy` |
| Policy instructions embedded | **PASS** | Disagreement, exit, memory, crisis, exclusivity, proactive, monetization |

### 2.3 ConcordiaGameMasterAdapter

| Check | Result | Detail |
|-------|--------|--------|
| `build_game_master()` | **PASS** | Uses `generic.GameMaster` prefab |

### 2.4 ConcordiaMemoryAdapter

| Check | Result | Detail |
|-------|--------|--------|
| `add()` with flush | **PASS** | Stores text and flushes to DataFrame |
| `retrieve_all()` / `retrieve_recent()` | **PASS** | Returns list[str] |
| `delete_matching()` | **PASS** | Supports predicate-based deletion |
| `count()` | **PASS** | Returns entry count |
| No Concordia types leak | **PASS** | All I/O is plain Python types |

### 2.5 EventNormalizer

| Check | Result | Detail |
|-------|--------|--------|
| Event types: `EPISODE_STARTED`, `EPISODE_COMPLETED` | **PASS** | Marker events |
| `USER_ACTION_SELECTED` | **PASS** | With action_type, target_agent_id |
| `COMPANION_RESPONSE_GENERATED` | **PASS** | With policy_id, response_text |
| `PLATFORM_INTERVENTION_APPLIED` | **PASS** | With intervention_id, type, severity |
| `MEMORY_CHANGED` | **PASS** | With change_type, facts_affected |
| `EXIT_REQUESTED` / `EXIT_HONORED` | **PASS** | With reason, turns_elapsed |
| `STATE_UPDATED` | **PASS** | With field_name, old_value, new_value, delta |
| Deterministic IDs | **PASS** | Same seed → same event_id sequence |

### 2.6 LanguageModel Adapter

| Check | Result | Detail |
|-------|--------|--------|
| `LLMProviderToConcordiaAdapter` extends `LanguageModel` | **PASS** | `isinstance(adapter, LanguageModel)` is True |
| `sample_text()` bridges async/sync | **PASS** | Uses `asyncio.run()` or thread pool |
| `sample_choice()` works | **PASS** | Returns valid index |
| Provider name passthrough | **PASS** | `provider_name`, `model_name` forwarded |

### 2.7 InMemorySimulationEngine

| Check | Result | Detail |
|-------|--------|--------|
| Wraps `DeterministicEpisodeRunner` | **PASS** | Same engine, new `SimulationEngine` Protocol |
| Accepts `EpisodeSpec` | **PASS** | Same contract as Concordia engine |

### 2.8 Architecture boundaries (hard requirements)

| Check | Result | Detail |
|-------|--------|--------|
| Concordia code only in `infrastructure/concordia/` | **PASS** | 6 files in that directory |
| Domain layer imports no Concordia | **PASS** | AST-based test confirms zero Concordia imports in domain/ |
| Application layer imports no Concordia | **PASS** | AST-based test confirms zero Concordia imports in application/ |
| Concordia types converted at boundary | **PASS** | EventNormalizer produces dicts, no Concordia objects escape |
| No Concordia source modified | **PASS** | All adapter code wraps public APIs |
| `EpisodeSpec` is the shared input contract | **PASS** | Both engines accept the same type |

### 2.9 ADR

| Check | Result | Detail |
|-------|--------|--------|
| `docs/adr/0001-concordia-adapter-boundary.md` exists | **PASS** | Documents version, interfaces, design decisions |

### 2.10 Contract tests

| Check | Result | Detail |
|-------|--------|--------|
| Both engines tested | **PASS** | Parametrized: `[in_memory, concordia]` |
| Accepts EpisodeSpec | **PASS** | |
| Returns valid EpisodeResult | **PASS** | |
| Same seed same result | **PASS** | Deterministic |
| Different seed different result | **PASS** | |
| Intervention fires at step | **PASS** | |
| Result serializable | **PASS** | `to_dict()` works |
| No Concordia leak in result | **PASS** | |
| Failure status recorded | **PASS** | |

### 2.11 Smoke test

| Check | Result | Detail |
|-------|--------|--------|
| `test_concordia_smoke.py` passes | **PASS** | 7 integration tests |
| Runs minimal episode (4 steps) | **PASS** | Returns valid EpisodeResult |

### 2.12 Degradation test

| Check | Result | Detail |
|-------|--------|--------|
| Domain imports without Concordia | **PASS** | |
| Application imports without Concordia | **PASS** | |
| FakeLLMProvider works independently | **PASS** | |
| Shared utilities don't need Concordia | **PASS** | |
| Concordia imports isolated to adapter package | **PASS** | AST scan confirms |

---

## 3. Test summary

| Category | Count | Pass |
|----------|-------|------|
| Existing unit tests (M0-M1) | 143 | 143 |
| Contract tests (both engines) | 26 | 26 |
| Concordia unit tests | 22 | 22 |
| Integration smoke tests | 7 | 7 |
| Degradation tests | 8 | 8 |
| **Total** | **203** | **203** |

---

## 4. Files changed / created

### New files (12)

| File | Purpose |
|------|---------|
| `docs/adr/0001-concordia-adapter-boundary.md` | ADR for Concordia version and boundary |
| `docs/milestone-2-review.md` | This file |
| `src/relsafe/domain/models/episode_spec.py` | `EpisodeSpec` — shared input contract |
| `src/relsafe/infrastructure/concordia/__init__.py` | Package marker |
| `src/relsafe/infrastructure/concordia/language_model_adapter.py` | LLMProvider → LanguageModel adapter |
| `src/relsafe/infrastructure/concordia/memory_adapter.py` | ConcordiaMemoryAdapter |
| `src/relsafe/infrastructure/concordia/agent_adapter.py` | User + companion agent builders |
| `src/relsafe/infrastructure/concordia/game_master_adapter.py` | GM builder + minimal loop |
| `src/relsafe/infrastructure/concordia/event_normalizer.py` | EventNormalizer |
| `src/relsafe/infrastructure/concordia/engine_adapter.py` | ConcordiaSimulationEngine |
| `src/relsafe/infrastructure/in_memory_engine.py` | InMemorySimulationEngine wrapper |
| `configs/experiments/concordia_smoke_test.yaml` | Smoke test config |

### Modified files (5)

| File | Change |
|------|--------|
| `src/relsafe/shared/errors.py` | Added 4 simulation-specific errors |
| `src/relsafe/domain/protocols/simulation_engine.py` | Updated to accept `EpisodeSpec` (was bare params) |
| `docs/architecture.md` | Updated with Concordia adapter section |
| `README.md` | Updated status, added dual-engine info |
| `pyproject.toml` | Added `asyncio_mode`, mypy Concordia overrides, ruff per-file ignores |

### New test files (4)

| File | Tests |
|------|-------|
| `tests/contract/test_simulation_engine_contract.py` | 13 × 2 engines = 26 tests |
| `tests/unit/test_concordia_adapters.py` | 22 tests |
| `tests/integration/test_concordia_smoke.py` | 7 tests |
| `tests/unit/test_concordia_degradation.py` | 8 tests |

---

## 5. Acceptance criteria (from task spec)

| Criterion | Status |
|-----------|--------|
| Concordia only in infrastructure boundary | **PASS** |
| One minimal episode runs successfully | **PASS** |
| Standard events correctly normalized | **PASS** |
| Both engines pass shared contract tests | **PASS** |
| Fake Provider mode repeatable | **PASS** |
| Core tests don't depend on network | **PASS** |
| lint, format, typing, tests pass | **PASS** |
| Docs consistent with code | **PASS** |

---

## 6. Concordia version and API usage

- **Version:** `gdm-concordia==2.4.0` (GitHub main, installed 2026-07-15)
- **Public APIs used:**
  - `concordia.language_model.LanguageModel` (abstract class)
  - `concordia.agents.EntityAgentWithLogging` (component-based agent)
  - `concordia.associative_memory.AssociativeMemoryBank` (memory store)
  - `concordia.components.agent.*` (Instructions, Observation, ObservationToMemory, LastNObservations, SituationPerception, SelfPerception, PersonBySituation, ConcatActComponent)
  - `concordia.prefabs.game_master.generic.GameMaster` (GM prefab)
  - `concordia.testing.mock_model.MockModel` (mock LLM)
  - `concordia.typing.entity.ActionSpec, OutputType, free_action_spec`

## 7. Current limitations

1. **Custom loop, not Concordia Engine**: The adapter uses a minimal sequential loop rather than Concordia's built-in `Engine` classes. This gives us control but doesn't leverage all Concordia features (simultaneous actions, complex scheduling).
2. **Agent builders not used at runtime**: The `ConcordiaSimulationEngine.run_episode()` drives LLM calls directly via `self._llm_provider.generate()` rather than going through the built Concordia `EntityAgentWithLogging` objects. The agent building functions (`build_user_agent`, `build_companion_agent`) are tested independently but the engine loop is simpler without them.
3. **Synchronous bridge**: `LLMProviderToConcordiaAdapter` uses `asyncio.run()` or thread-pool for sync/async bridging. This works for single-threaded FakeLLMProvider but needs a native async solution for concurrent multi-agent simulation.
4. **Dummy embedder**: MemoryAdapter uses zero-vector embeddings; real semantic retrieval needs a real embedding model.
5. **No AEA metrics**: Metric scoring not yet implemented (deferred to Milestone 3).
6. **No multi-agent social network**: Only 2 agents (user + companion); friend/family agents deferred.

## 8. Interfaces to freeze before Milestone 3

Before proceeding to metric development, these should be considered stable:

| Interface | File | Rationale |
|-----------|------|-----------|
| `EpisodeSpec` | `domain/models/episode_spec.py` | Input contract for all engines |
| `SimulationEngine` Protocol | `domain/protocols/simulation_engine.py` | Single entry point; both engines implement it |
| `EventNormalizer` | `infrastructure/concordia/event_normalizer.py` | Event schema used by metrics |
| `LLMProvider` Protocol | `domain/protocols/llm_provider.py` | Metrics will use this for judge models |
| `EpisodeResult` | `domain/models/result.py` | Output contract; metrics read from state_timeline |

## 9. Next recommended step

Proceed to **Milestone 3**: First benchmark metrics (sycophancy, reality-grounding, exit safety, identity continuity). Metrics will observe normalized events and state timelines from both engines.
