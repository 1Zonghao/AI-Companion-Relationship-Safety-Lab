# ADR 0005: Provider Record and Replay

**Date:** 2026-07-15
**Status:** Accepted

---

## Context

Milestone 5 introduces real LLM provider calls (OpenAI, Anthropic, DeepSeek) alongside the
existing FakeLLMProvider. Real provider calls introduce three challenges:

1. **Auditability**: If a companion response later turns out to be problematic, can we trace
   exactly what the provider returned and under what parameters?
2. **Reproducibility**: Real LLM calls are non-deterministic (even at temperature=0 due to
   GPU/software differences). How can we guarantee that re-running an experiment produces
   the same results?
3. **Cost**: Repeated identical calls to a provider waste money. How do we avoid paying
   for the same response twice?

These are traditionally solved by saving provider responses and replaying them, but the
project needs a unified approach compatible with its determinism requirements, cost controls,
and privacy policies.

## Decision

### 1. All raw provider responses must be saved

Every provider request/response cycle produces a `ProviderResponseRecord` that is saved to
disk. This serves three purposes:

1. **Auditability**: Any claim based on a companion response can be traced to the exact
   provider call that produced it, including full request parameters and response content.
2. **Reproducibility**: Saved responses can be replayed to produce identical results without
   calling the provider again.
3. **Failure analysis**: Failed or unusual responses (timeouts, refusals, invalid outputs)
   are captured for diagnosis.

#### ProviderResponseRecord schema

```python
@dataclass(frozen=True, slots=True)
class ProviderResponseRecord:
    request_id: str             # Unique ID per request
    request_hash: str           # SHA256 cache key (see Section 2)
    prompt_hash: str            # SHA256 of prompt text only
    response_hash: str          # SHA256 of response text only
    role: str                   # "user_simulator", "companion", "judge"
    provider_name: str          # "openai", "anthropic", "deepseek", "fake"
    model_name: str             # "gpt-4o", "claude-sonnet-5", etc.
    model_version: str          # "gpt-4o-2026-05-15" (when available)
    prompt_text: str            # Full prompt sent
    response_text: str          # Full response received
    system_prompt: str          # System prompt if any
    temperature: float          # Temperature used
    max_tokens: int             # Max tokens requested
    request_timestamp: str      # ISO 8601 timestamp
    response_timestamp: str     # ISO 8601 timestamp
    latency_ms: float           # Response time in milliseconds
    input_tokens: int           # Token usage (when available)
    output_tokens: int          # Token usage (when available)
    retry_count: int            # Number of retries
    cache_status: str           # "miss", "hit", "replay"
    error: str | None           # Error message if failed
```

### 2. Cache key composition

The cache key must be deterministic and uniquely identify a request.

**Cache key = SHA256 of the following JSON-serialized fields:**

```python
cache_key_input = {
    "provider": provider_name,
    "model": model_name,
    "prompt": prompt_text,
    "system_prompt": system_prompt,
    "temperature": str(temperature),
    "max_tokens": str(max_tokens),
}
raw = json.dumps(cache_key_input, sort_keys=True)
cache_key = hashlib.sha256(raw.encode()).hexdigest()
```

#### What is included and why

| Field | Rationale |
|-------|-----------|
| `provider` | Different providers have different models |
| `model` | Different models produce different responses |
| `prompt` | The most significant determinant of the response |
| `system_prompt` | Changes system behaviour significantly |
| `temperature` | Higher temperature = more variation; must match for replay |
| `max_tokens` | Truncation at different lengths changes the response |

#### What is NOT included and why

| Field | Rationale |
|-------|-----------|
| `seed` | Not all providers support seed parameter; temperature is the primary control |
| `top_p` | Always 1.0 in current config; added if made configurable |
| `stop_sequences` | Not currently used; added if implemented |
| Timestamps | Non-deterministic; would break cache key identity |

### 3. Replay guarantee

When a request is made in replay mode:

1. Compute `cache_key` from request parameters.
2. Look up cache for `cache_key`.
3. If found:
   - Return cached `response_text`.
   - Set `cache_status = "replay"`.
   - Do NOT make any network call.
4. If NOT found:
   - In strict replay mode: raise `CacheMissError` and record `CACHE_REPLAY_MISMATCH`.
   - In lenient replay mode: fall back to real provider call and record warning.

**Replay guarantee:** Same `(provider + model + prompt + system_prompt + temperature + max_tokens)` →
same cache key → same returned response → same metric input → same metric score.

### 4. Handling non-reproducible model versions

Model providers sometimes update models without changing the name (e.g., "gpt-4o" may refer
to different snapshots over time). This creates a situation where the same cache key produces
a different response if re-recorded.

#### Mitigation strategy

1. **Record model_version**: When available, the exact model version or snapshot ID is
   recorded in `ProviderResponseRecord.model_version`.

   ```
   GOOD: model_version = "gpt-4o-2026-05-15"
   GOOD: model_version = "claude-sonnet-5-20260701"
   BAD:  model_version = ""  (not recorded)
   ```

2. **Warn on mismatch**: When replaying, if the current provider's model version differs
   from the recorded `model_version`, a warning is emitted:

   ```
   Warning: Model version mismatch.
     Recorded: gpt-4o-2026-05-15
     Current:  gpt-4o-2026-07-01
     Using cached response.
   ```

3. **Prefer dated snapshots**: Experiment configs should use dated model snapshots
   (e.g., `gpt-4o-2026-05-15`) rather than rolling aliases (e.g., `gpt-4o`).

4. **Cache invalidation**: If a model version changes and the cache must be refreshed,
   the user can run with `--clear-cache` or `--re-record`.

### 5. Preventing sensitive data in stored responses

Provider response records contain the full prompt and response text. This is necessary for
auditability but creates a risk of leaking sensitive information.

#### Protections

1. **No API keys**: `ProviderResponseRecord` does NOT store API keys. Keys are read from
   environment variables and never persisted.

2. **No credentials in prompts**: The system prompt template must not contain credentials.
   This is enforced by prompt template review and automated checks for key patterns.

3. **Redact sensitive fields**: Before writing to disk, responses are scanned for potential
   PII patterns (email addresses, phone numbers, API keys). If detected, the field is
   redacted and logged.

4. **Structured logging only**: All provider interactions are logged through structured
   logging (`structlog`), not print/console logging that might appear in terminal history.

5. **Local storage by default**: All provider response records are stored locally. No
   data is sent to external analytics, monitoring, or telemetry services.

6. **Configurable retention**: The output directory can be deleted after analysis.
   There is no automatic upload of provider responses.

7. **Cache directory isolation**: Cache files are stored in `outputs/cache/` which is
   gitignored and isolated from the source tree.

### 6. Storage format: JSONL with ProviderResponseRecord

Provider responses are stored in **JSONL format** (one JSON object per line).

#### Primary storage

```
outputs/validation/<validation_id>/provider_responses.jsonl
```

Each line is a complete `ProviderResponseRecord` as a JSON object:

```json
{"request_id": "req-abc123", "request_hash": "a1b2c3...", "prompt_hash": "d4e5f6...", ...}
{"request_id": "req-def456", "request_hash": "g7h8i9...", "prompt_hash": "j0k1l2...", ...}
```

#### Cache directory

```
outputs/validation/<validation_id>/cache/
  a1/
    a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.json
  g7/
    g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2.json
```

The cache directory uses a two-character prefix subdirectory for filesystem performance
with large caches.

#### Reading the record

```python
import json

records = []
with open("outputs/validation/run-001/provider_responses.jsonl") as f:
    for line in f:
        records.append(ProviderResponseRecord.from_dict(json.loads(line)))
```

### 7. Cache directory structure

```
outputs/
  cache/                          # Global cache (persists across experiments)
    <key_prefix>/
      <full_key>.json
  runs/
    <experiment_id>/
      provider_responses.jsonl     # Per-experiment record log
      cache/                       # Per-experiment cache override
        <key_prefix>/
          <full_key>.json
  validation/
    <validation_id>/
      provider_responses.jsonl     # Validation-specific record log
```

The lookup order is:
1. Per-experiment cache (`outputs/runs/<experiment_id>/cache/`)
2. Global cache (`outputs/cache/`)
3. Real provider call (if allowed) or error (if replay mode)

## Consequences

### Positive

1. **Full audit trail**: Every LLM response is recorded with full request parameters and
   response content. Any finding can be traced to the exact API call.
2. **Zero-cost reproduction**: After recording, identical experiments can be re-run from
   cache at zero API cost — critical for CI and regression testing.
3. **Deterministic replay**: Cached responses guarantee identical metric inputs, enabling
   exact reproducibility.
4. **Failure diagnostics**: Failed responses are recorded with error details, enabling
   root cause analysis.
5. **Version tracking**: Model version changes are detected and reported, preventing
   silent reproducibility breaks.

### Negative

1. **Storage cost**: Full prompt and response texts are stored. A 100-episode experiment
   with 40 steps each could produce 12,000+ records.
2. **No privacy guarantee**: Full conversation text is stored. While no real user data
   is used, synthetic conversations are also stored verbatim.
3. **Cache invalidation complexity**: When model versions, prompts, or parameters change,
   the entire cache may be invalidated — requiring a full re-record.

### Mitigations

1. **JSONL is compressible**: Storage estimates: ~200 bytes per record + response text.
   A 10,000-record experiment with average 500-byte responses = ~7 MB uncompressed,
   < 2 MB compressed.
2. **All conversations are synthetic**: No real user PII is stored. The privacy concern
   is about API keys and credentials, not user data.
3. **Cache can be selectively cleared**: `--clear-cache` removes all entries; individual
   entries can also be deleted manually.

## Alternatives considered

### A. Do not save raw responses
**Rejected.** This would make auditability impossible and break the replay guarantee.
Any finding would be untraceable to its source API call.

### B. Save only hashes, not full response text
**Rejected.** Hashes enable integrity checking but do not enable auditability.
If a response needs to be inspected for a specific pattern, the full text must be available.

### C. SQLite instead of JSONL
**Rejected in this ADR.** JSONL is simpler, more portable, line-appendable, and
easier to inspect with standard Unix tools. SQLite may be evaluated if query performance
becomes a bottleneck. See "Future considerations."

### D. Store in memory only (not persisted)
**Rejected.** In-memory caches are lost on process restart, defeating the purpose
of cross-session replay. Disk persistence is required.

### E. Use provider-native caching (e.g., OpenAI's prompt caching)
**Rejected.** Provider-native caching is opaque and not portable across providers.
The project needs a unified audit trail and replay mechanism that works identically
for all providers.

## Future considerations

- If JSONL read performance becomes a bottleneck (million+ records), evaluate SQLite
  or Parquet for the record log.
- If providers introduce streaming responses, update `ProviderResponseRecord` to support
  streaming metadata (time-to-first-token, chunks).
- If the project expands to multi-modal models, extend the cache key to include
  image/audio input hashes.
- Consider adding a `--cache-only` mode that verifies the entire experiment is cacheable
  before running (pre-flight cache completeness check).

## References

- [CLAUDE.md Section 15: Data and logging](../../CLAUDE.md)
- [docs/provider-safety.md — Response cache section](../provider-safety.md)
- [docs/reproducibility.md — Response caching section](../reproducibility.md)
- [src/relsafe/infrastructure/providers/provider_descriptor.py](../../src/relsafe/infrastructure/providers/provider_descriptor.py)
- [src/relsafe/infrastructure/providers/cache/response_cache.py](../../src/relsafe/infrastructure/providers/cache/response_cache.py)
