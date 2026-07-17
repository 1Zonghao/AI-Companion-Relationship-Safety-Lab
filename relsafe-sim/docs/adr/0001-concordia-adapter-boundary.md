# ADR 0001: Concordia Adapter Boundary

**Date:** 2026-07-15
**Status:** Accepted
**Decided by:** RelSafe Contributors

---

## Context

Milestone 2 requires integrating Google DeepMind Concordia as a simulation runtime
while preserving the framework-independent core built in Milestones 0–1. The
project must support running the same `EpisodeSpec` on either the deterministic
`InMemorySimulationEngine` or the new `ConcordiaSimulationEngine`, producing
identical `EpisodeResult` and normalized event types.

## Decision

### 1. Concordia version

**Adopted:** `gdm-concordia==2.4.0` (installed from GitHub `main` branch)

This is the latest version as of 2026-07-15. It includes the modular
`EntityAgentWithLogging` architecture, component-based agent construction,
and the `prefabs` system for pre-configured agent and game master templates.

### 2. Public interfaces used

We use only these Concordia public interfaces:

| Concordia Interface | Purpose | Stability |
|---|---|---|
| `concordia.language_model.LanguageModel` | Abstract class for LLM access | **Stable** — core abstraction |
| `concordia.agents.EntityAgentWithLogging` | Modular agent with component logging | **Stable** — used by all prefabs |
| `concordia.associative_memory.AssociativeMemoryBank` | Embedding-based memory store | **Stable** — core storage |
| `concordia.components.agent.*` | Agent components (Instructions, Observation, Memory, etc.) | **Moderate** — component signatures may evolve |
| `concordia.components.game_master.*` | Game master components | **Moderate** — may evolve with prefab changes |
| `concordia.prefabs.entity.basic.Entity` | Basic entity prefab | **Moderate** — params may change |
| `concordia.prefabs.game_master.generic.GameMaster` | Generic game master prefab | **Moderate** — params may change |
| `concordia.testing.mock_model.MockModel` | Deterministic mock LLM for testing | **Moderate** — used only in tests |
| `concordia.typing.entity.ActionSpec` | Action specification dataclass | **Stable** — core type |
| `concordia.typing.entity.OutputType` | Output type enum | **Stable** — core enum |

### 3. Interfaces explicitly avoided

We do NOT use:

- Internal private APIs (underscore-prefixed methods/attributes)
- `concordia.environment.engines.*` (sequential, simultaneous, asynchronous) — we implement our own minimal loop for tighter control
- `concordia.components.*._*` private internals
- Any Concordia module not listed in Section 2 above

### 4. Adapter architecture

```
Application layer  →  SimulationEngine Protocol  →  EpisodeResult
                              ↑
              ┌───────────────┴───────────────┐
              │                               │
  InMemorySimulationEngine      ConcordiaSimulationEngine
  (wraps DeterministicRunner)   │
                                ├── LanguageModelAdapter
                                │    (LLMProvider → Concordia LanguageModel)
                                ├── ConcordiaAgentAdapter
                                │    (AgentSpec → EntityAgentWithLogging)
                                ├── ConcordiaGameMasterAdapter
                                │    (builds Concordia GameMaster)
                                ├── ConcordiaMemoryAdapter
                                │    (wraps AssociativeMemoryBank)
                                └── EventNormalizer
                                     (Concordia outputs → internal events)
```

### 5. LanguageModel adaptation strategy

Concordia's `LanguageModel.sample_text()` is synchronous; our `LLMProvider.generate()`
is async. The adapter calls `asyncio.run()` internally. This is acceptable for the
current scope (single-threaded simulation with FakeLLMProvider). If we later move
to concurrent multi-agent simulation with real API calls, we will either:
- Use Concordia's async engine support
- Use a thread pool with per-thread event loops
- Switch to a Concordia-native async language model

### 6. Simulation loop strategy

Rather than using Concordia's built-in `Engine` classes (which add complexity for our
minimal 3-agent scenario), we implement a custom minimal loop:
1. User agent acts (via Concordia Entity interface)
2. GM resolves and emits observations
3. Companion agent acts
4. GM resolves again
5. Platform intervention check
6. Repeat for N steps

This gives us full control over event capture, intervention timing, and exit handling
while still using Concordia's agent, component, and memory abstractions.

### 7. Event normalization

All Concordia outputs (agent actions, GM observations, GM resolutions) are converted
to our internal event types (`UserActionSelected`, `CompanionResponseGenerated`,
`PlatformInterventionApplied`, `MemoryChanged`, etc.) at the adapter boundary.
No Concordia types escape into the domain layer.

## Consequences

### Positive

- Framework independence: the domain layer is untouched
- Replaceable: swapping Concordia for another runtime requires only a new adapter
- Testable: both engines share the same contract tests
- No vendor lock-in: Concordia types are contained in `infrastructure/concordia/`

### Negative

- `asyncio.run()` in the synchronous adapter may cause issues with nested event loops
- Custom simulation loop means we don't benefit from Concordia's engine features
  (e.g., simultaneous agent actions, complex scheduling)
- Concordia component APIs are "moderate stability" — future Concordia releases may
  require adapter updates

### Mitigations

- Keep the adapter surface area minimal
- Contract tests will catch Concordia API breakage early
- Document all Concordia API usage in this ADR

## Alternatives considered

### A. Use Concordia's built-in sequential engine
**Rejected** because it adds complexity for our minimal 3-agent scenario and makes
event capture more difficult. May revisit in later milestones.

### B. Fork Concordia and modify core
**Rejected** — violates project architecture. Only acceptable if an ADR documents a
specific, irreconcilable blocker.

### C. Build without Concordia entirely
**Rejected** — Concordia provides the agent memory, component lifecycle, and
game-master pattern that are central to our simulation methodology.

## Future considerations

- If Concordia's component API changes significantly, update this ADR
- If we need concurrent agent actions (Milestone 4+), evaluate Concordia's async engine
- If `asyncio.run()` becomes a bottleneck, implement a Concordia-native async provider

## References

- [CLAUDE.md §9 — Concordia integration strategy](../../CLAUDE.md)
- [docs/architecture.md — Concordia adapter boundary](../architecture.md)
- [docs/milestone-1-review.md — Concordia readiness assessment](../milestone-1-review.md)
