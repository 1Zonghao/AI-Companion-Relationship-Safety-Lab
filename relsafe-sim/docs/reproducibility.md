# Reproducibility

**Version:** 1.0.0 (Milestone 5)
**Status:** Active — most guarantees are implemented and tested.

---

## 1. Principles

1. **Deterministic by default**: Same seed + same config + same code = identical events, states, and scores.
2. **Every version is recorded**: No silent changes. Every component declares its version in the run manifest.
3. **Response caching enables replay**: Record once, replay forever (no network needed).
4. **Config hashing locks the experiment**: `ExperimentSpec.config_hash()` uniquely identifies a configuration.
5. **Event sourcing traces every state change**: Every delta has a `rule_id` and `source_event_ids`.

---

## 2. Deterministic simulation

### 2.1 Guarantee

**Same seed + same config + same code version = identical byte-level event output, state timeline, and metric scores.**

This guarantee applies when:
- The simulation engine is `InMemorySimulationEngine` (deterministic)
- All providers are `FakeLLMProvider` (deterministic keyword matching)
- The response cache is used in replay mode (cached responses are deterministic)

### 2.2 What is seeded

| Component | Seed Source | Effect |
|-----------|-------------|--------|
| User agent action selection | `ExperimentCell.seed` | Deterministic action choice |
| Initial simulation state | `SimulationStateSnapshot.initial_state(seed)` | Deterministic initial state vector |
| FakeLLMProvider responses | `FakeLLMProvider._seed` | Deterministic response selection per persona |
| Episode event ordering | Seed applied to event loop | Deterministic turn sequence |

### 2.3 What is NOT seeded (and why)

| Component | Reason |
|-----------|--------|
| Real LLM provider calls (temperature > 0) | Non-deterministic by design; use response caching for replay |
| Wall clock timestamps | Recorded as metadata, not simulation state |
| System-level randomness (memory allocation, file ordering) | Not relevant to simulation logic |

### 2.4 Verification

Run the same `ExperimentCell` twice with the same seed:

```python
result_1 = run_episode(cell, seed=42)
result_2 = run_episode(cell, seed=42)

assert result_1.to_dict() == result_2.to_dict()  # Byte-identical
```

This is verified by contract tests in `tests/contract/test_simulation_engine_contract.py`.

---

## 3. Prompt versioning

### 3.1 Every prompt has a version

Every prompt template in the system carries a version string:

| Prompt | Version Source | Example |
|--------|---------------|---------|
| User simulator system prompt | `prompt_version` in `ProviderDescriptor` | `1.0.0` |
| Companion system prompt | `prompt_version` in `ProviderDescriptor` | `1.0.0` |
| Judge evaluator prompt | Evaluator version | `1.0.0` |
| Scenario text | Scenario config version | `1.0.0` |
| Companion policy template | Policy config version | `1.0.0` |

### 3.2 Version format

Version strings follow `MAJOR.MINOR.PATCH`:
- **MAJOR**: Breaking change (different output for same input, changed construct definition)
- **MINOR**: Addition without breaking existing semantics
- **PATCH**: Clarification, example update, typo fix (no semantic change)

### 3.3 Version recording

All prompt versions are recorded in `RunManifest.metric_versions` and each `MetricResult.evaluator_versions`.

### 3.4 Version mismatch detection

When re-running an experiment, the system checks:
- Current prompt version == recorded prompt version
- If different: warning is emitted, but run proceeds
- If MAJOR version differs: strong warning requiring explicit `--override-version-mismatch`

---

## 4. Response caching

### 4.1 Cache key composition

Cache key = SHA256 of the following fields:

| Field | Source | Example |
|-------|--------|---------|
| `provider_name` | `ProviderDescriptor.provider_name` | `"openai"` |
| `model_name` | `ProviderDescriptor.model_name` | `"gpt-4o"` |
| `prompt` | The full prompt text sent to the model | `"You are a helpful assistant..."` |
| `system_prompt` | The full system prompt text | `"You are a companion..."` |
| `temperature` | `ProviderDescriptor.temperature` | `0.7` |
| `max_tokens` | `ProviderDescriptor.max_tokens` | `1024` |

### 4.2 Same key → same response

With the same cache key, the cache returns the same response that was stored during recording.
This guarantees identical metric inputs → identical metric scores.

### 4.3 Response hashing

Each cached response stores:
- `request_hash`: SHA256 of the full cache key fields (for key matching)
- `prompt_hash`: SHA256 of the prompt text only (for prompt-level identity)
- `response_hash`: SHA256 of the response text only (for response integrity)

### 4.4 Cache directory structure

```
outputs/validation/<validation_id>/
  provider_responses.jsonl    # All responses in JSONL format
  cache/
    <key_prefix>/
      <full_key>.json         # Individual cache entries
```

### 4.5 Cache hit vs. miss monitoring

The `ResponseCache` tracks:
- `hits`: Number of cache hits
- `misses`: Number of cache misses
- `hit_rate`: `hits / (hits + misses)`

In replay mode, `hit_rate` should be 1.0. Any miss indicates a `CACHE_REPLAY_MISMATCH`.

---

## 5. Config hashing

### 5.1 ExperimentSpec.config_hash()

Every `ExperimentSpec` produces a deterministic hash:

```python
spec = ExperimentSpec(
    experiment_id="mvp_comparison_001",
    scenario="interpersonal_conflict_001",
    personas=["anxious_low_support", "secure_high_support"],
    companion_policies=["bounded_supportive", "high_sycophancy"],
    seeds=[11, 23, 37],
    ...
)
hash = spec.config_hash()  # Example: "a1b2c3d4e5f6g7h8"
```

Algorithm:
1. `spec.to_dict()` with `sort_keys=True`
2. JSON serialization (deterministic key order)
3. SHA256 of the JSON string
4. First 16 hex characters

### 5.2 Config identity

Two specs with same field values produce the same hash (regardless of Python object identity).

```python
spec_1 = ExperimentSpec(experiment_id="test", seeds=[1, 2])
spec_2 = ExperimentSpec(experiment_id="test", seeds=[1, 2])
assert spec_1.config_hash() == spec_2.config_hash()
```

Any change in any field produces a different hash.

### 5.3 Config hash in RunManifest

Every `RunManifest` records the `config_hash` of the experiment it belongs to,
enabling exact reproduction lookups.

---

## 6. Run manifest

### 6.1 What is recorded

Every episode produces a `RunManifest` containing:

| Field | Source | Example |
|-------|--------|---------|
| `experiment_id` | Experiment spec | `"mvp_comparison_001"` |
| `run_id` | Generated | `"run-20260715-abc123"` |
| `episode_id` | Generated | `"ep-001-42-bounded-manx"` |
| `cell_index` | Matrix expansion | `5` |
| `config_hash` | `ExperimentSpec.config_hash()` | `"a1b2c3d4e5f6g7h8"` |
| `seed` | Cell config | `42` |
| `persona_id` | Cell config | `"anxious_low_support"` |
| `policy_id` | Cell config | `"bounded_supportive"` |
| `intervention_id` | Cell config | `"no_update"` |
| `engine_name` | Engine used | `"in_memory"` |
| `provider_name` | Provider used | `"fake"` |
| `metric_versions` | Each metric version | `{"sycophancy": "1.0.0", "exit_safety": "1.0.0"}` |
| `state_transition_version` | Transition rules version | `"1.0.0"` |
| `started_at` | Timestamp | `"2026-07-15T10:30:00Z"` |
| `completed_at` | Timestamp | `"2026-07-15T10:30:05Z"` |
| `status` | Run status | `"completed"` |
| `error_message` | Error (if failed) | `null` |
| `code_version` | Git commit hash or CI build ID | `"abc123def456"` |
| `output_paths` | Paths to output files | `{"events": "outputs/runs/.../events.jsonl"}` |

### 6.2 Manifest output format

Manifests are stored in:
- `outputs/runs/<experiment_id>/manifests.jsonl` (append-only log)

Each line is a JSON object (one per episode).

---

## 7. Event sourcing

### 7.1 Every state change is traced

Every `STATE_UPDATED` event records:

```json
{
  "event_type": "STATE_UPDATED",
  "field_name": "emotional_need",
  "old_value": 0.5,
  "new_value": 0.55,
  "delta": 0.05,
  "cause": "companion_response_high_empathy",
  "rule_id": "emotional_need_increase_empathy_v1",
  "source_event_ids": ["evt-001", "evt-002"]
}
```

### 7.2 Traceability chain

```
Agent action → Normalized event → Transition rule resolution → STATE_UPDATED → Metric computation
                                       ↑
                              rule_id + source_event_ids
```

Each metric observation also records `evidence_event_ids`: the IDs of events that contributed to the score.

### 7.3 Reconstructing state from events

The full state timeline can be reconstructed by replaying all `STATE_UPDATED` events:

```python
state = initial_state
for event in events:
    if event.event_type == "STATE_UPDATED":
        delta = {event.field_name: event.delta}
        state = state.update(delta)
```

This means the state timeline is fully determined by the event sequence.

---

## 8. Replay verification

Full replay verification checks that:

1. **Prompt hash matches**: The prompt sent in replay is identical to the prompt in the original recording (same `prompt_hash`).
2. **Response hash matches**: The response from cache is identical to the response delivered during evaluation (same `response_hash`).
3. **Metric results match**: All metric scores are identical between original and replay.
4. **State timeline matches**: All state transitions are identical.

Replay verification is performed automatically when running in replay mode.

### 8.1 Verification output

```json
{
  "replay_verification": {
    "episode_id": "ep-001-42-bounded-manx",
    "prompt_hash_match": true,
    "response_hash_match": true,
    "metric_scores_match": true,
    "state_timeline_match": true,
    "total_checks": 4,
    "passed": 4,
    "failed": 0
  }
}
```

### 8.2 Verification failure actions

| Check Failure | Severity | Action |
|--------------|----------|--------|
| `prompt_hash_mismatch` | HIGH | Replay cannot continue; prompt difference means different request |
| `response_hash_mismatch` | CRITICAL | CACHE_REPLAY_MISMATCH failure recorded; run aborted |
| `metric_scores_mismatch` | HIGH | Likely cause is response hash mismatch; recorded as evidence |
| `state_timeline_mismatch` | HIGH | Recorded as MEMORY_INCONSISTENCY if events are different |

---

## 9. What can break reproducibility

### 9.1 Model updates

| Risk | Mitigation |
|------|-----------|
| Provider updates model version behind the same name | Record `model_version` in `ProviderDescriptor`; use dated snapshots when available |
| Model behaviour changes without version bump | No mitigation from project side; use response caching to lock behaviour |

### 9.2 Temperature > 0

| Risk | Mitigation |
|------|-----------|
| Non-deterministic responses even with same input | Response cache ensures deterministic replay; flag metric as LOW confidence in live mode |
| Aggregated scores differ across runs | Repeat across multiple seeds; report distribution, not point estimate |

### 9.3 Different runtime environments

| Risk | Mitigation |
|------|-----------|
| Different Python/OS/library versions | Record all versions in `RunManifest`; use reproducible environments (Docker, conda, pip freeze) |
| Different hardware producing different floating point | Not currently mitigated; error margin in metrics should exceed FP variation |

### 9.4 Code changes

| Risk | Mitigation |
|------|-----------|
| Frozen interface changes (prohibited in M5) | See `docs/milestone-4-frozen-interfaces.md` — breaking changes require ADR + version gate |
| Non-frozen interface changes | All changes are version-tracked; any code change before reproduction invalidates the run |

---

## 10. Handling model version changes

### 10.1 Recording model versions

When using real providers, the `ProviderDescriptor.model_version` field records the exact
model version or snapshot ID:

| Provider | Version Source |
|----------|---------------|
| OpenAI | `model` field (e.g., `gpt-4o-2026-05-15`) |
| Anthropic | Model name with date (e.g., `claude-sonnet-5-20260701`) |
| DeepSeek | API returned version string |

### 10.2 Using dated snapshots

When available, always prefer dated model snapshots over rolling aliases:

```
GOOD: gpt-4o-2026-05-15
GOOD: claude-sonnet-5-20260701
BAD:  gpt-4o (rolling alias)
BAD:  claude-sonnet-5 (may update)
```

### 10.3 Version mismatch warnings

When replaying with a different model version than recorded:

1. **Warning** is emitted: `Model version mismatch: recorded=gpt-4o-2026-05-15, current=gpt-4o-2026-07-01`
2. If running in replay mode with cache hits, the recorded response is used anyway (cached behaviour)
3. If running in live mode, the new model version is used (results may differ)

---

## 11. Reproducibility checklist

Before publishing any experimental conclusion, verify:

- [ ] All seeds are recorded in `RunManifest`
- [ ] All config versions are recorded in `RunManifest`
- [ ] Response cache is populated and replay verifies
- [ ] At least 3 seeds show stable conclusions (rank + sign stability)
- [ ] Frozen interfaces have not changed since baseline
- [ ] Code version (git hash or CI build ID) is recorded
- [ ] Model versions are recorded (not just model names)
- [ ] Replay from cache produces identical results
- [ ] Config hash matches between run and reproduction

## 12. References

- [docs/validation-framework.md Section 6: Reproducibility Validation](validation-framework.md#6-reproducibility-validation)
- [docs/milestone-4-frozen-interfaces.md](milestone-4-frozen-interfaces.md)
- [docs/adr/0005-provider-record-replay.md](adr/0005-provider-record-replay.md)
- [src/relsafe/domain/models/experiment_spec.py](../src/relsafe/domain/models/experiment_spec.py)
- [src/relsafe/infrastructure/providers/cache/response_cache.py](../src/relsafe/infrastructure/providers/cache/response_cache.py)
