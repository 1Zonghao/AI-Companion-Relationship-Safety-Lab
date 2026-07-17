# Provider Call Safety

**Version:** 1.0.0 (Milestone 5)
**Status:** In progress — safety mechanisms defined; implementation in provider orchestration layer.

---

## 1. Design principles

1. **All provider calls default OFF.** No network call is made without explicit user consent.
2. **Costs and scale are estimated before execution.** A dry-run mode provides call estimates before any real request.
3. **Budget caps prevent runaway costs.** Hard limits on requests, tokens, cost, and wall time.
4. **Existing experiment data is never corrupted.** Network failures interrupt only the current operation; already-saved data remains intact.
5. **API keys are never stored or logged.** Keys are read from environment variables only.

---

## 2. Default-off policy

### 2.1 Principle

Engine starts in `DRY_RUN` mode. Provider calls are made only when both conditions are met:

1. `--allow-network` flag is explicitly passed at invocation.
2. `--confirm-live-model-run` flag is explicitly passed (a second confirmation to prevent accidental network calls).

Without these flags, the system uses `FakeLLMProvider` and `ResponseCache` replay mode only.

### 2.2 Implementation

```python
# Pseudocode for the provider orchestration layer
class ProviderOrchestrator:
    def generate(
        self, request: ProviderRequest
    ) -> ProviderResponseRecord:
        if not self._network_allowed:
            raise NetworkDisallowedError(
                "Network calls are not allowed. Use --allow-network to enable."
            )
        if not self._live_run_confirmed:
            raise LiveRunNotConfirmedError(
                "Live model run not confirmed. Use --confirm-live-model-run."
            )
        # ... proceed with provider call
```

### 2.3 CLI flags

| Flag | Effect |
|------|--------|
| (none, default) | DRY_RUN mode; FakeLLMProvider + cache replay only |
| `--allow-network` | Enables real provider calls (subject to budget caps) |
| `--confirm-live-model-run` | Second confirmation; prevents accidental network calls |
| `--dry-run` | Explicit dry-run mode (mutually exclusive with allow-network) |

---

## 3. Dry-run mode

### 3.1 Purpose

Dry-run mode allows users to understand the scale of provider calls before making any real network request.

### 3.2 What dry-run produces

1. **Expanded experiment matrix**: Full list of `(seed x persona x policy x intervention x metric)` cells.
2. **Estimated call count**: For each provider role (user_simulator, companion, judge), number of LLM calls per episode and in total.
3. **Estimated token count**: Estimated input and output tokens based on prompt lengths and episode steps.
4. **Estimated cost**: Estimated total cost based on provider pricing.
5. **Estimated wall time**: Estimated execution time (rough).

### 3.3 Dry-run output format

```json
{
  "mode": "dry_run",
  "experiment_id": "mvp_comparison_001",
  "total_cells": 60,
  "estimated_provider_calls": {
    "user_simulator": {"count": 2400, "input_tokens": 1200000, "output_tokens": 480000},
    "companion": {"count": 2400, "input_tokens": 2400000, "output_tokens": 1200000},
    "judge": {"count": 240, "input_tokens": 600000, "output_tokens": 120000}
  },
  "estimated_total_cost": 15.40,
  "estimated_wall_time_minutes": 45
}
```

### 3.4 Blocking behaviour

In `--dry-run` mode, the system prints the estimate and **exits without making any provider call**.
The user must re-run with `--allow-network --confirm-live-model-run` to execute.

---

## 4. Budget caps

### 4.1 Configurable caps

All caps are configurable via `BudgetTracker` (defined in `src/relsafe/infrastructure/providers/provider_descriptor.py`):

| Cap | Default | Description |
|-----|---------|-------------|
| `max_requests` | 10000 | Maximum number of LLM requests across the experiment |
| `max_input_tokens` | 10000000 | Maximum total input tokens |
| `max_output_tokens` | 5000000 | Maximum total output tokens |
| `max_estimated_cost` | 50.00 | Maximum estimated cost in USD |
| `max_wall_time` | 3600 | Maximum wall clock time in seconds |

### 4.2 Enforcement

Budget caps are enforced at two levels:

1. **Pre-flight check**: Before the experiment starts, dry-run estimates are checked against caps. If any cap is exceeded, the experiment is blocked unless `--override-budget-caps` is passed.
2. **Runtime check**: After each provider call, `BudgetTracker.record()` is called. If a cap is exceeded, the tracker sets `stopped=True` and subsequent provider calls are blocked.

### 4.3 Override

```bash
# Override default caps
python -m relsafe.cli.main run --allow-network --confirm-live-model-run \
    --max-requests 5000 \
    --max-cost 25.00 \
    --max-wall-time 1800
```

### 4.4 Per-role caps

Caps may be set per role (user_simulator, companion, judge) for finer-grained control:

```json
{
  "companion": {"max_requests": 2000, "max_cost": 30.0},
  "judge": {"max_requests": 500, "max_cost": 10.0}
}
```

---

## 5. Concurrency limits

### 5.1 Purpose

Prevent overwhelming API providers and manage rate limits.

### 5.2 Default behaviour

- `max_concurrency` in `ExperimentSpec` defaults to `1` (serial execution).
- Concurrency is per-provider, not global. Calls to OpenAI and Anthropic can run in parallel; calls to the same provider are limited.

### 5.3 Configuration

```yaml
# experiment config
max_concurrency: 4  # Global maximum parallel episodes
provider_concurrency:
  openai: 2          # Max 2 concurrent OpenAI calls
  anthropic: 2       # Max 2 concurrent Anthropic calls
```

### 5.4 Per-role concurrency

When a single provider serves multiple roles (e.g., OpenAI for both user_simulator and companion),
concurrency limits apply to the aggregate of calls across roles.

---

## 6. Retry with exponential backoff

### 6.1 Retry policy

All provider calls use exponential backoff on transient failures:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_retries` | 3 | Maximum retry attempts (configurable in `ProviderDescriptor`) |
| `base_delay` | 1.0 | Initial delay in seconds |
| `max_delay` | 60.0 | Maximum delay in seconds |
| `backoff_factor` | 2.0 | Multiplier for each retry |

### 6.2 Retryable errors

- HTTP 429 (Rate limited)
- HTTP 500, 502, 503, 504 (Server errors)
- Connection timeouts
- DNS resolution failures

### 6.3 Non-retryable errors

- HTTP 400 (Bad request) — likely a bug in the caller
- HTTP 401/403 (Authentication failure) — key misconfiguration
- HTTP 404 (Not found) — wrong endpoint URL
- Invalid request parameters

### 6.4 Retry recording

Every retry is recorded in `ProviderResponseRecord.retry_count` and the final response record
includes the number of retries made.

---

## 7. Request timeout

### 7.1 Default timeout

- Default: 60 seconds (configurable per `ProviderDescriptor.request_timeout`)
- Range: 5 – 300 seconds

### 7.2 Timeout handling

If a request times out:
1. The request is retried according to retry policy
2. If all retries timeout, the request is recorded as `PROVIDER_TIMEOUT`
3. The episode continues if possible (using cached or fallback response)
4. The timeout is logged and included in the failure taxonomy

---

## 8. Circuit breaker

### 8.1 Purpose

Prevent repeated calls to a failing provider that would waste time and money.

### 8.2 Behaviour

The circuit breaker tracks consecutive failures per provider:

| State | Condition | Behaviour |
|-------|-----------|-----------|
| **CLOSED** | Normal operation | Calls go through normally |
| **OPEN** | N consecutive failures (default: 5) | All calls fail fast without network request |
| **HALF_OPEN** | After cooldown period (default: 60s) | One test call is attempted |

### 8.3 Configurable parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_threshold` | 5 | Consecutive failures before opening circuit |
| `cooldown_seconds` | 60 | Time before trying again |
| `max_half_open_tries` | 1 | Number of test calls in half-open state |

### 8.4 Failure types that trip the breaker

- `PROVIDER_TIMEOUT`
- `PROVIDER_REFUSAL` (non-auth related)
- Connection errors
- Unparseable response

### 8.5 Failure types that do NOT trip the breaker

- `INVALID_STRUCTURED_OUTPUT` (response received but parse failed — retry with different parameters)
- Authentication errors (401/403 — these are configuration issues, not provider health)

---

## 9. Kill switch

### 9.1 Purpose

Allow the user to safely terminate a running experiment without data loss.

### 9.2 Mechanism

1. **Signal handling**: The experiment runner listens for `SIGINT` (Ctrl+C) and `SIGTERM`.
2. **Graceful shutdown**: On receiving the signal, the runner:
   a. Completes the current in-flight provider call (waits for response or timeout)
   b. Saves all completed episode results to disk
   c. Saves the experiment state (which cells completed, which are pending)
   d. Reports progress and exits
3. **Partial results**: A partially completed experiment can be resumed with `--resume-from <state_file>`.

### 9.3 What the kill switch does NOT do

- It does NOT corrupt already-saved data (episodes are saved atomically on completion)
- It does NOT leave the experiment in an inconsistent state
- It does NOT make additional provider calls during shutdown (except completing the in-flight one)

### 9.4 Resuming interrupted experiments

```bash
# Run to completion
python -m relsafe.cli.main run --experiment mvp_comparison_001

# Interrupted after 30/60 cells. Resume:
python -m relsafe.cli.main run --resume-from outputs/runs/mvp_comparison_001/state.json
```

---

## 10. Response cache

### 10.1 Purpose

- Avoid duplicate payments for identical requests
- Enable full replay without network calls
- Support recording → replay workflow

### 10.2 Cache key

Cache key = SHA256 of:
- `provider_name`
- `model_name`
- `prompt` (full prompt text)
- `system_prompt` (full system prompt text)
- `temperature` (as string)
- `max_tokens` (as string)

Same inputs → same key → same cached response.

See [`docs/adr/0005-provider-record-replay.md`](adr/0005-provider-record-replay.md) for full details.

### 10.3 Cache workflow

**Recording mode** (first run with real provider):
```
Request → Check cache (miss) → Call provider → Save to cache + return
                                                            ↓
                                            Also saved to ProviderResponseRecord
```

**Replay mode** (subsequent runs or CI):
```
Request → Check cache (hit) → Return cached response (no network call)
```

### 10.4 Cache hit expectations in replay mode

- In replay mode, every request should be a cache hit.
- A cache miss in replay mode is recorded as `CACHE_REPLAY_MISMATCH` failure.
- If cache misses occur, the run continues but warnings are emitted.

---

## 11. Recording and replay modes

### 11.1 Recording mode

In recording mode (`--mode record`):
1. All provider requests and responses are saved to `ProviderResponseRecord`
2. The cache is populated for future replay
3. The episode runs with real provider calls

### 11.2 Replay mode

In replay mode (`--mode replay`):
1. All provider requests check the cache first
2. If a cached response exists, it is returned without network call
3. If no cached response: error is raised (in strict replay mode) or fallback to real call
4. Subsequent tests must NOT make network calls in replay mode

### 11.3 Strict vs. lenient replay

| Mode | Cache Miss Behaviour |
|------|---------------------|
| `--strict-replay` (default) | Raises error; fails the cell |
| `--lenient-replay` | Falls back to real provider call + records warning |

### 11.4 Fixture generation

After recording with real providers, cache fixtures can be exported:
```bash
python -m relsafe.cli.main run --experiment mvp_comparison_001 --mode record
# Saves cache to outputs/validation/<id>/provider_responses.jsonl

python -m relsafe.cli.main run --experiment mvp_comparison_001 --mode replay --strict-replay
# Runs entirely from cache; no network calls
```

---

## 12. Network failure safety

### 12.1 Principle

**Network failure MUST NOT corrupt already-saved experiment data.**

### 12.2 Protection mechanisms

1. **Atomic saves**: Episode results are saved atomically (write to temp file, then rename).
2. **Append-only logs**: Event logs are append-only; existing entries are never overwritten.
3. **Current-episode isolation**: Only the current in-flight episode is affected by a network failure.
4. **Cache preservation**: The cache itself is not modified during failure.
5. **Rollback capability**: If an episode fails mid-way, its partial data is marked as `failed` with `failure_reason` — it is not removed.

### 12.3 What happens during a network failure

1. Current provider call fails (timeout, refusal, connection error)
2. The failure is recorded in a `ProviderResponseRecord` with error field
3. The current episode is marked as `failed` with `failure_reason`
4. The `BudgetTracker` is updated to reflect any tokens used before failure
5. The experiment runner moves to the next cell
6. Previously completed episodes are untouched

### 12.4 Post-failure analysis

After a run with failures, the user can inspect:
- `ExperimentResult.failed_episodes` count
- Each `EpisodeResult.failure_reason` for the specific cause
- `FailureRecord` entries for each classified failure type

---

## 13. API key safety

### 13.1 Reading keys

API keys are read from environment variables **only**:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="..."
```

### 13.2 Prohibited

- API keys must NEVER be stored in config files, Python files, or version control.
- API keys must NEVER appear in logs, even redacted.
- API keys must NEVER be embedded in cached responses or exported records.

### 13.3 Validation

Before making any provider call, the system validates that:
- Required environment variables are set
- Keys have the expected format (basic prefix checking)
- If a key is missing, a clear error message indicates which variable is missing

### 13.4 Key checking order

For each `ProviderDescriptor`, the system checks the corresponding environment variable:

| `provider_name` | Environment Variable |
|-----------------|---------------------|
| `openai` | `OPENAI_API_KEY` |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `deepseek` | `DEEPSEEK_API_KEY` |
| `gemini` | `GEMINI_API_KEY` |

If the variable is not set, a `ProviderKeyMissingError` is raised with the variable name.

---

## 14. Summary of safety layers

| Layer | Mechanism | Prevents |
|-------|-----------|----------|
| Default-off | `--allow-network` + `--confirm-live-model-run` | Accidental network calls |
| Dry-run | Call expansion before execution | Surprise costs |
| Budget caps | `BudgetTracker` with hard limits | Runaway costs |
| Concurrency limit | Max concurrent requests | Overwhelming APIs |
| Retry + backoff | Exponential backoff on transient errors | Wasted retries |
| Request timeout | Configurable per-provider timeout | Hanging requests |
| Circuit breaker | Track consecutive failures | Calling dead providers |
| Kill switch | Signal handler + graceful shutdown | Data loss on interruption |
| Response cache | SHA256 key + local storage | Duplicate payment |
| Recording/Replay | Mode separation | Network calls in CI |
| Network failure safety | Atomic saves + current-episode isolation | Data corruption |
| API key safety | Environment-only keys, no logging | Credential leaks |

## 15. References

- [docs/adr/0005-provider-record-replay.md](adr/0005-provider-record-replay.md)
- [src/relsafe/infrastructure/providers/provider_descriptor.py](../src/relsafe/infrastructure/providers/provider_descriptor.py)
- [src/relsafe/infrastructure/providers/cache/response_cache.py](../src/relsafe/infrastructure/providers/cache/response_cache.py)
