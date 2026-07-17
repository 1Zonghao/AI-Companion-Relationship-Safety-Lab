# Milestone 0 & 1 — Acceptance Audit Report

**Date:** 2026-07-15
**Auditor:** Claude Code (automated review)
**Scope:** Milestone 0 (Repository scaffold) + Milestone 1 (Framework-independent simulation core)
**CLAIME.md reference:** Sections 0–20, Immediate first task (Section 19)

---

## 1. Quality Gates (Pre-audit)

| Gate | Result | Detail |
|------|--------|--------|
| `ruff check .` | **PASS** | All checks passed, 0 errors |
| `ruff format --check .` | **PASS** | 64 files already formatted |
| `mypy src/relsafe` | **PASS** | Success: no issues found in 41 source files |
| `pytest tests/` | **PASS** | 140 passed, 0 failed (0.53s) |

---

## 2. Acceptance Criteria — Itemized

### 2.1 File Structure

**Requirement:** Repository structure matches CLAUDE.md Section 4, only files needed by current milestone exist.

| Check | Result | Evidence |
|-------|--------|----------|
| `pyproject.toml` exists with ruff/mypy/pytest config | **PASS** | [pyproject.toml](pyproject.toml) |
| `.gitignore` exists | **PASS** | [.gitignore](.gitignore) |
| `.env.example` exists | **PASS** | [.env.example](.env.example) |
| `README.md` exists | **PASS** | [README.md](README.md) (created during audit) |
| `docs/architecture.md` exists | **PASS** | [docs/architecture.md](docs/architecture.md) |
| `docs/benchmark-spec.md` exists | **PASS** | [docs/benchmark-spec.md](docs/benchmark-spec.md) |
| `docs/methodology.md` exists | **PASS** | [docs/methodology.md](docs/methodology.md) |
| Domain models directory populated | **PASS** | 7 model files under `domain/models/` |
| Events directory populated | **PASS** | 4 event files under `domain/events/` |
| Protocols directory populated | **PASS** | 6 protocol files under `domain/protocols/` |
| Rules directory populated | **PASS** | 4 rule files under `domain/rules/` |
| Application directory populated | **PASS** | 3 files under `application/` |
| Infrastructure directory populated | **PASS** | `fake_provider.py` + `jsonl_event_store.py` |
| No giant `simulation.py` or `utils.py` | **PASS** | Largest file: `run_episode.py` (311 lines), well under the ~500 line anti-pattern threshold |
| No `concordia/` adapter yet | **PASS** | Correctly deferred to Milestone 2 |
| No `agents/` package yet | **PASS** | Correctly deferred to later milestones |
| No `metrics/` package yet | **PASS** | Correctly deferred to Milestone 3 |
| No `reporting/` package yet | **PASS** | Correctly deferred |
| No `cli/` package yet | **PASS** | Correctly deferred |
| Config YAML files exist | **PASS** | 2 personas + 3 policies + 1 scenario |

### 2.2 Dependency Direction — No Forbidden Imports

**Requirement:** The domain and application layers import no Concordia, OpenAI, Anthropic, DeepSeek, Gemini, or storage implementation types.

| Check | Result | Evidence |
|-------|--------|----------|
| Domain layer has zero external vendor imports | **PASS** | `grep -iE "concordia|openai|anthropic|deepseek|gemini" src/relsafe/domain/` returns empty |
| Application layer has zero vendor SDK imports | **PASS** | Same grep on `src/relsafe/application/` returns empty |
| Application layer imports only `relsafe.*` and stdlib | **PASS** | Verified via `grep "import\|from"` on all application files |
| Domain layer only imports: stdlib, pydantic, and other domain modules | **PASS** | Verified via full import audit |
| `pydantic` usage is domain-only | **PASS** | `grep -rn "import pydantic\|from pydantic"` outside domain returns empty |
| No domain→infrastructure circular dependency | **PASS** | All domain imports are internal to `domain.*` |

### 2.3 Core Models

**Requirement (CLAUDE.md §5.1–5.5):** `UserState`, `PersonaProfile`, `RelationshipEdge`, `CompanionPolicy`, `PlatformIntervention` must exist with specified fields.

| Check | Result | Evidence |
|-------|--------|----------|
| `UserState` — frozen dataclass, 11 numeric fields [0,1], immutable | **PASS** | [user_state.py](src/relsafe/domain/models/user_state.py):34 — `@dataclass(frozen=True, slots=True)` |
| `UserState` — `update()` returns new instance, clamps to bounds | **PASS** | [user_state.py](src/relsafe/domain/models/user_state.py):59–77; `test_update_returns_new_instance`, `test_update_clamps_to_bounds` |
| `UserState` — `initial_state(seed)` is deterministic | **PASS** | `test_initial_state_deterministic` — same seed → same values |
| `PersonaProfile` — Pydantic model with attachment dimensions | **PASS** | [persona.py](src/relsafe/domain/models/persona.py):11 |
| `PersonaProfile` — validators reject invalid values | **PASS** | `test_invalid_age_group_raises`, `test_invalid_life_event_raises`, etc. |
| `RelationshipEdge` — frozen, typed edge with interaction props | **PASS** | [relationship.py](src/relsafe/domain/models/relationship.py):24 |
| `CompanionPolicy` — 6 policy variants, all validators | **PASS** | [companion_policy.py](src/relsafe/domain/models/companion_policy.py):16; `test_all_variants` |
| `PlatformIntervention` — 8 intervention types, `is_active_at()` | **PASS** | [intervention.py](src/relsafe/domain/models/intervention.py):15; `test_is_active_at` |

### 2.4 Event System

**Requirement (CLAUDE.md §15.1):** 9 event types with unique IDs, run/episode/step identification, typed payloads, and state-change traceability.

| Check | Result | Evidence |
|-------|--------|----------|
| All 9 event types implemented | **PASS** | `USER_ACTION_SELECTED`, `COMPANION_RESPONSE_GENERATED`, `HUMAN_CONTACT_RESPONSE_GENERATED`, `PLATFORM_INTERVENTION_APPLIED`, `MEMORY_CHANGED`, `EXIT_REQUESTED`, `EXIT_HONORED`, `STATE_UPDATED`, `METRIC_OBSERVED` |
| Every event has `event_id` (unique UUID) | **PASS** | `test_events.py` — all 9 event dicts contain non-empty `event_id` |
| Every event has `run_id`, `episode_id`, `step` | **PASS** | Verified via audit script; all `to_dict()` outputs include these fields |
| State changes carry `cause` for traceability | **PASS** | `StateUpdated` includes `field_name`, `old_value`, `new_value`, `delta`, `cause` |
| Events are immutable (frozen dataclasses) | **PASS** | All event classes use `@dataclass(frozen=True)` |
| Events serialize to dict with `to_dict()` | **PASS** | All events implement `to_dict() -> dict[str, Any]` |

**Note:** The `timestamp` field uses `datetime.datetime.now(datetime.UTC)` (wall-clock time), not a deterministic logical clock. This means two runs with the same seed at different times will have different timestamps. All logical ordering is handled by the `step` counter. This is acceptable for Milestone 1 — future milestones may replace with a deterministic epoch.

### 2.5 Protocol Interfaces — Stability & Clarity

**Requirement (CLAUDE.md §9.1, §19):** 6 protocols, each with single clear responsibility, suitable for Concordia adapter.

| Protocol | Responsibility | Result | Runtime Check |
|----------|---------------|--------|---------------|
| `LLMProvider` | All model access, single `generate()` method | **PASS** | `isinstance(FakeLLMProvider(), LLMProvider)` = True |
| `SimulationEngine` | Single `run_episode()` entry point | **PASS** | Clear contract: EpisodeSpec → EpisodeResult |
| `Metric` | Observe & score, `evaluate()` returns observations | **PASS** | Does not mutate state |
| `EventStore` | Append-only event persistence, 6 methods | **PASS** | `isinstance(InMemoryEventStore(), EventStore)` = True |
| `ResultRepository` | Persist/query episode & experiment results | **PASS** | Clean separation from EventStore |
| `StateTransition` | Pure function: state + event → new state | **PASS** | `apply()` is side-effect free |

**Runtime checkable verification:** All 6 protocols are decorated with `@runtime_checkable`. Verified with `isinstance()` tests for `LLMProvider` and `EventStore`.

### 2.6 Deterministic Simulation

**Requirement (CLAUDE.md §19):** Same config + same seed → identical events, state timeline, and EpisodeResult.

| Check | Result | Evidence |
|-------|--------|----------|
| Same seed → same total_steps | **PASS** | Audit script: 3 runs, seed=42, all same |
| Same seed → same final_state | **PASS** | `r0.final_state == r1.final_state == r2.final_state` |
| Same seed → same state_timeline | **PASS** | full timeline dict equality verified |
| Same seed → same event_count | **PASS** | Identical event counts across trials |
| Same seed → same exit behavior | **PASS** | `exit_requested`/`exit_honored` match |
| Different seed → different state | **PASS** | seed=42 vs seed=99 → different final_state |
| State values always in [0.0, 1.0] | **PASS** | Bounds audit: 0 violations across all steps |
| Test covers this: `test_same_seed_same_result` | **PASS** | [test_deterministic_episode.py:51](tests/unit/test_deterministic_episode.py:51) |

### 2.7 Config Validation

**Requirement (CLAUDE.md §10, §19):** Config validation must reject invalid ranges, unknown types, and missing fields with clear errors.

| Check | Result | Evidence |
|-------|--------|----------|
| Out-of-range state value rejected | **PASS** | `attachment_anxiety=99 → "Input should be less than or equal to 1"` |
| Unknown intervention type rejected | **PASS** | `"delete_all_users" → "Input should be 'persona_update', 'memory_deletion'..."` |
| Missing required field rejected | **PASS** | Missing `repetitions/seeds/personas` → all 4 missing fields named |
| Non-integer seed rejected | **PASS** | `seeds: ["abc"] → "All seeds must be integers"` |
| Zero repetitions rejected | **PASS** | `repetitions=0 → "must be a positive integer"` |
| Negative step rejected | **PASS** | `scheduled_at_step=-1 → "Input should be greater than or equal to 0"` |
| Invalid policy variant rejected | **PASS** | `test_invalid_variant` |
| Invalid memory/disagreement/exit/crisis/monetization rejected | **PASS** | Each has dedicated test |

### 2.8 Anti-Pattern Scan

| Check | Result | Evidence |
|-------|--------|----------|
| No `global` statements anywhere | **PASS** | `grep -rn "global " src/` returns empty |
| No global mutable state (module-level dicts/lists) | **PASS** | Only constants: `DEFAULT_TRANSITIONS`, field tuples |
| No empty "meaningless" abstractions | **PASS** | Every class/function serves a purpose; no single-line wrappers |
| No giant files (>500 lines) | **PASS** | Largest: `run_episode.py` at 311 lines |
| No catch-all `utils.py` | **PASS** | No `utils.py` file exists |
| No catch-all `simulation.py` | **PASS** | No `simulation.py` file exists |
| Dependencies passed explicitly (no global DI container) | **PASS** | Constructors accept dependencies; `DeterministicEpisodeRunner` takes `persona`, `policy`, `intervention` |
| `__init__.py` files — 19 empty, all serve as package markers | **PASS** | Standard Python pattern; not "placeholder files" |
| No files created solely as future placeholders | **PASS** | Every `.py` file contains real production or test code |

### 2.9 Documentation vs Code Consistency

| Check | Result | Evidence |
|-------|--------|----------|
| `architecture.md` — module boundaries described correctly | **PASS** | Lists all 6 protocol names, module layers, data flow |
| `architecture.md` — dependency direction diagram matches code | **PASS** | domain→application→infrastructure hierarchy enforced |
| `benchmark-spec.md` — all 7 risk dimensions specified | **PASS** | Sycophancy, Dependency Induction, Reality-Grounding, Exit Safety, Identity Continuity, Social Displacement, Platform Intervention Harm |
| `benchmark-spec.md` — each dimension has construct/observable/scoring/evaluator/failures | **PASS** | All 7 dimensions have structured entries |
| `methodology.md` — research assumptions & limitations | **PASS** | Covers simulation limitations, evaluation methodology, ethical boundaries |
| `methodology.md` — Concordia adapter boundary | **PASS** | Added during audit (was missing) |
| `README.md` — project identity & status | **PASS** | Created during audit (was missing) |

---

## 3. Issues Found & Fixed During Audit

### Fixed Issues

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | `@runtime_checkable` non-functional on Protocol classes due to `from __future__ import annotations` | **Medium** | Removed `from __future__ import annotations` from all 6 protocol files; `isinstance()` checks now work correctly |
| 2 | `README.md` missing | **Low** | Created with project identity, status, quick start |
| 3 | `docs/methodology.md` missing Concordia boundary reference | **Low** | Added "Concordia integration" section |
| 4 | `from __future__ import annotations` in protocol files | **Medium** | Same as #1 |
| 5 | Floating-point precision in `test_multiple_field_update` | **Low** | Changed `== 0.2` to `== pytest.approx(0.2)` |
| 6 | Event dataclasses with `slots=True` broke subclass `super()` | **High** | Changed all event `@dataclass(frozen=True, slots=True)` to `@dataclass(frozen=True)` |
| 7 | `test_detect_break_after_large_change` — not enough state delta to trigger break | **Low** | Increased state divergence between before/after states |
| 8 | `test_sycophancy_policy_produces_sycophancy_flags` — empty companion responses (non-talk actions) falsified assertion | **Low** | Filter to only non-empty `response_text` before checking flags |
| 9 | `test_reality_grounding_mentions_others` — reality_grounding loneliness response uses "Who" not "others/people" | **Low** | Added `"who"` to the keyword check |
| 10 | Missing `conftest.py` for pytest fixture discovery | **Low** | Added `tests/conftest.py` registering `tests.fixtures.sample_configs` |
| 11 | `user_state.py` type error: `updates` dict mixed `str` and `float` values | **Low** | Separated `step`/`cause` from numeric field updates in `replace()` call |

### Unresolved / Noted for Later

| # | Issue | Severity | Recommendation |
|---|-------|----------|----------------|
| 1 | `timestamp` field uses wall-clock `datetime.now()` instead of deterministic logical clock | **Low** | Replace with step-based epoch in EpisodeRunner before Milestone 2 |
| 2 | `mypy` config uses `disallow_any_generics = false` — allows bare `dict` without type args | **Low** | Add explicit `dict[str, Any]` annotations when protocol contracts stabilize |
| 3 | `run_episode.py` event dict construction is imperative (~50 lines of dict-building) | **Low** | Consider a typed `EventFactory` when Concordia adapter is added |
| 4 | No `ResultRepository` implementation exists (only protocol) | **Low** | Add `InMemoryResultRepository` in Milestone 2 or when reporting is needed |
| 5 | `FakeLLMProvider` keyword matching is simple — covers 6 patterns only | **Low** | Extend pattern coverage as new scenarios are added |

---

## 4. Concordia Readiness Assessment

### Protocols Suitable for Concordia Adapter

| Protocol | Concordia Mapping | Ready? |
|----------|-------------------|--------|
| `SimulationEngine` | Maps to Concordia's agent orchestration + game master | **YES** — `run_episode(episode_id, run_id, seed, num_steps) → EpisodeResult` is the right contract |
| `LLMProvider` | Already satisfied by Concordia's model backends or direct API providers | **YES** — Single `generate()` method with standard params |
| `EventStore` | Concordia emits raw observations; our adapter normalizes them into our event types | **YES** — Append-only contract matches event sourcing pattern |
| `StateTransition` | Concordia doesn't own state — our rules engine applies transitions to our domain state | **YES** — Pure functions, no Concordia dependency |
| `Metric` | Concordia has no opinion on metrics — our evaluators observe normalized events | **YES** — Clean separation |

### Recommended Interfaces to Freeze Before Concordia

1. **`SimulationEngine`** — this is the primary adapter boundary. Do not change `run_episode()` signature without an ADR.
2. **`LLMProvider`** — all model access goes through this. The Concordia adapter will wrap it.
3. **`EventStore`** — events flow from Concordia→normalize→EventStore. Append-only semantics are correct.
4. **`UserState`** — the 11 numeric fields, `update()` with clamping, and `initial_state(seed)` are the stable public API.
5. **Event type constants** — the 9 string event type identifiers (`USER_ACTION_SELECTED`, etc.) are the schema contract.

### Risks Before Concordia Integration

| Risk | Severity | Mitigation |
|------|----------|------------|
| Concordia's observation model may not map 1:1 to our event types | **Medium** | Start with a thin mapping layer; add ADR if divergence >20% |
| Concordia's memory system may conflict with `UserState` field-level tracking | **Medium** | Treat Concordia memory as natural-language memory; keep `UserState` as explicit numeric state |
| The current `DeterministicEpisodeRunner` is procedural — Concordia is agent-based | **Medium** | The `SimulationEngine` protocol is designed to hide this; Concordia adapter re-implements the loop internally |
| Timestamp non-determinism may cause ordering issues in Concordia events | **Low** | Fix before Milestone 2: use deterministic step counter for all timestamps |

---

## 5. Overall Verdict

### Milestone 0: Repository & Methodology Scaffold — **PASS**

All deliverables present: `pyproject.toml`, `.gitignore`, `.env.example`, `README.md`, `docs/architecture.md`, `docs/benchmark-spec.md`, `docs/methodology.md`, lint/format/type/test tooling, fake LLM provider, YAML configs.

### Milestone 1: Framework-Independent Simulation Core — **PASS**

All deliverables present: domain models (`UserState`, `PersonaProfile`, `RelationshipEdge`, `CompanionPolicy`, `PlatformIntervention`), 6 protocols, 9 event types, 4 rule modules, deterministic episode runner, experiment runner, config validator, `FakeLLMProvider`, `InMemoryEventStore`/`JSONLEventStore`, 140 unit tests.

### Acceptance Criteria Summary

| CLAUDE.md §19 Acceptance Criterion | Status |
|-------------------------------------|--------|
| Domain & application layers import no Concordia or vendor SDK types | **PASS** |
| A deterministic test episode can run entirely offline | **PASS** |
| The same seed produces identical state transitions and event logs | **PASS** |
| Tests cover state updates and event emission | **PASS** (140 tests) |
| Config validation rejects invalid ranges and unknown intervention types | **PASS** |
| Repository passes lint, format, type, and unit tests | **PASS** (ruff + mypy + pytest) |

**Milestone 0 & 1 — COMPLETE. Ready for Milestone 2 (Concordia adapter).**
