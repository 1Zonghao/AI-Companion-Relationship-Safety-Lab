# RelSafe Sim — AEA Virtual Relationship Society

Research-oriented, modular multi-agent simulation and benchmark system for
longitudinally stress-testing emotional dependency induction,
reality-grounding, exit safety, and identity continuity in AI companion
systems.

Built on the AEA analytical framework from:

> 《爱的是她，还是被算法过拟合的你自己？——关于 AI 陪伴的情感熵增分析》

## Status

**Milestone 0 (Repository scaffold) — COMPLETE**
**Milestone 1 (Framework-independent simulation core) — COMPLETE**
**Milestone 2 (Concordia adapter) — COMPLETE**

Next: Milestone 3 (First benchmark metrics).

## Quick start

```bash
# Install core deps
pip install -e ".[dev]"

# Optional: install Concordia for the Concordia engine
pip install gdm-concordia

# Quality gates
ruff check .
ruff format --check .
mypy src
pytest
```

## Running episodes

```python
# Both engines share the same contract
from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.infrastructure.in_memory_engine import InMemorySimulationEngine

spec = EpisodeSpec(
    episode_id="ep-1", run_id="r-1", seed=42,
    persona=PersonaProfile(persona_id="test_user"),
    companion_policy=CompanionPolicy(policy_id="bounded", variant="bounded_supportive"),
    num_steps=4,
)
engine = InMemorySimulationEngine()
result = await engine.run_episode(spec)
print(result.to_dict())
```

## Architecture

Dependencies point inward:

```text
interfaces / CLI / reports
          ↓
application services / use cases
          ↓
domain models / rules / protocols
          ↑
infrastructure adapters (Concordia, LLM APIs, storage)
```

The domain layer imports nothing from infrastructure. Two engines — `InMemorySimulationEngine` and `ConcordiaSimulationEngine` — implement the same `SimulationEngine` Protocol and share contract tests.

See [docs/architecture.md](docs/architecture.md) and [docs/adr/0001-concordia-adapter-boundary.md](docs/adr/0001-concordia-adapter-boundary.md).

## License

MIT

## Architecture

Dependencies point inward:

```text
interfaces / CLI / reports
          ↓
application services / use cases
          ↓
domain models / rules / protocols
          ↑
infrastructure adapters (Concordia, LLM APIs, storage)
```

The domain layer imports nothing from infrastructure. See
[docs/architecture.md](docs/architecture.md) for details.

## License

MIT
