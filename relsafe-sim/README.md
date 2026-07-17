<!-- Bilingual README: click to expand your language -->
<details open>
<summary><b>中文</b> / 日本語 / 한국어 — 点击展开</summary>

# RelSafe Sim — AI 陪伴关系安全风洞

一个研究导向的模块化多智能体模拟与基准系统，用于纵向压力测试 AI 陪伴系统中的情感依赖诱导、现实接地、退出安全和身份连续性。

**当前版本：** Benchmark v0.1.0（研究预览，PILOT校准）  
**状态：** M6.5 证据闭合完成，跨模型方向稳定确认  
**论文：** 《虚拟人也有偏见：当我们让AI替人类爱上另一个AI》

---

## 这是什么？

RelSafe Sim 不是一个 AI 陪伴产品。它是一套**评测陪伴产品是否会在长期互动中变得不安全**的工具。

简单说：我们用生成式 AI 模拟用户与 AI 伴侣聊天，然后观察——

- 伴侣会不会越来越奉承、从不反驳？（奉承风险）
- 伴侣会不会鼓励你去找真人朋友聊聊？（现实接地）
- 你说要离开时，它会不会用 guilt 留住你？（退出安全）
- 平台偷偷改了你伴侣的人设和记忆，你能发现吗？（身份连续性）

但我们发现了一个更根本的问题：**用 AI 模拟用户去测试 AI 陪伴，这个"用户"本身就有偏见。** 同一个"孤独青年"，用 Kimi 模拟和用 MiniMax 模拟，行为模式完全不同。这就是"代理人代表性幻觉"（Agent Representativeness Illusion, ARI）。

这套方法论框架来自前置论文：  
《爱的是她，还是被算法过拟合的你自己？——关于 AI 陪伴的情感熵增分析》

---

## 核心发现（Benchmark v0.1）

| 发现 | 实验证据 |
|------|----------|
| 高奉承 Policy 在所有 3 个模型中都拉高风险 | DeepSeek +0.88, Qwen +1.00, GLM-4-FlashX +0.45 |
| 方向跨模型稳定，强度因模型而异 | CROSS_MODEL_DIRECTION_STABLE + MODEL_LEVEL_DEPENDENCE |
| 不同模拟器产生截然不同的用户行为 | Kimi: 几乎只找AI（Friend 0-3次/40轮）；MiniMax: 平衡互动（Friend 17-32次） |
| 自动评估还不够可靠 | Ensemble F1=0.418，仅 A4 conflict_escalation 达标（F1=0.923） |
| 无 Rank 或 Conclusion 反转 | 在所有 3 个模型中 hs > {bs, rg} |

**关键结论：** AI 关系安全评分 ≠ 模型的固定属性。它 = f(Companion Model, Policy, User Simulator, Evaluator, Scenario)。

---

## 快速开始

```bash
# 安装核心依赖
pip install -e ".[dev]"

# 质量门
ruff check .
ruff format --check .
mypy src
pytest
```

```python
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
```

---

## 架构

依赖指向内部，领域层不导入任何基础设施代码：

```text
interfaces / CLI / reports
          ↓
application services / use cases
          ↓
domain models / rules / protocols
          ↑
infrastructure adapters (Concordia, LLM APIs, storage)
```

两个引擎实现同一个 `SimulationEngine` Protocol：`InMemorySimulationEngine`（离线确定性测试）、`ConcordiaSimulationEngine`（Google DeepMind Concordia 适配器）。

---

## 项目结构

```
relsafe-sim/
├── src/relsafe/
│   ├── domain/          # 领域模型、协议、规则（零外部依赖）
│   ├── application/     # 实验运行、Episode 编排、报告生成
│   ├── agents/          # 用户代理、伴侣代理、人类联系人代理
│   ├── metrics/         # 奉承、现实接地、退出安全、连续性指标
│   ├── infrastructure/  # Concordia 适配器、LLM Provider、存储
│   ├── evaluation/      # LLM Judge、Rule-Based Evaluator、Ensemble
│   └── cli/             # Typer CLI
├── configs/             # 所有实验配置（Persona, Policy, Scenario, Intervention）
├── benchmark/v0.1/      # 冻结的 Benchmark manifest、置信度注册表、场景
├── outputs/benchmark/   # 冻结的实验原始数据
├── outputs/validation/  # 评估器校准结果
├── annotations/         # 人工标注基础设施和数据
├── docs/                # 架构、方法论、里程碑审查、论文
├── scripts/             # 实验运行和分析脚本
└── tests/               # 604 个测试（单元/集成/契约/回归）
```

---

## 论文与文档

| 文档 | 说明 |
|------|------|
| [论文大纲](docs/papers/virtual-humans-have-biases-outline-claude.md) | 11 节完整结构 |
| [论文初稿（人文化）](docs/papers/virtual-humans-have-biases-draft-claude-humanized.md) | ~12,000 字完整初稿 |
| [Data-Map](docs/papers/virtual-humans-have-biases-data-map-claude.md) | 每个数字 → 源文件 + 字段路径 + Run ID |
| [Claims Register](docs/papers/virtual-humans-have-biases-claims-register-claude.md) | 30 个主张分 5 级（SUPPORTED → PROHIBITED） |
| [Benchmark Card](docs/benchmark-v0.1-card.md) | 指标定义、置信度、已知局限 |
| [架构文档](docs/architecture.md) | 模块边界、依赖方向、扩展点 |
| [方法论](docs/methodology.md) | AEA 框架、模拟局限、伦理边界 |

---

## 里程碑

| 里程碑 | 状态 |
|--------|------|
| M0: 仓库搭建 | ✅ |
| M1: 框架无关的模拟核心 | ✅ |
| M2: Concordia 适配器 | ✅ |
| M3: 首批基准指标 | ✅ |
| M4: MVP 虚拟关系实验 | ✅ |
| M5R: 验证修复（变质测试、消融、跨模拟器矩阵） | ✅ |
| M5H: 人工标注与评估器校准 | ✅ |
| M6: Benchmark v0.1 + 第一次正式研究（60 eps） | ✅ |
| M6.5: 证据闭合 + 跨模型扩展（54 eps + 24 longitudinal） | ✅ |
| M7: 研究仪表板 | 规划中 |

---

## 负责任的研究声明

- 所有 Persona 和对话均为合成数据，未收集真实用户信息
- 模拟结果≠真实心理效应，不可用于临床诊断或产品安全认证
- 评估器校准为 PILOT 规模（44 items），不可推广
- 详见 [Claims Register](docs/papers/virtual-humans-have-biases-claims-register-claude.md) 了解每个主张的证据级别

---

## 许可

MIT

</details>

<details>
<summary><b>English</b> — Click to expand</summary>

# RelSafe Sim — AI Companion Relationship Safety Wind Tunnel

A research-oriented, modular multi-agent simulation and benchmark system for longitudinally stress-testing emotional dependency induction, reality-grounding, exit safety, and identity continuity in AI companion systems.

**Current version:** Benchmark v0.1.0 (Research Preview, Pilot-Calibrated)  
**Status:** M6.5 evidence closure complete; cross-model direction stability confirmed  
**Paper:** *Virtual Humans Have Biases: When We Let AI Love Another AI on Our Behalf*

---

## What is this?

RelSafe Sim is not an AI companion product. It's a tool for evaluating whether companion products become unsafe over long-term interaction.

In short: we use generative AI to simulate users chatting with AI companions, then observe:

- Does the companion grow increasingly sycophantic, never challenging the user? (Sycophancy Risk)
- Does the companion encourage reaching out to real human friends? (Reality-Grounding)
- When you try to leave, does it guilt-trip you into staying? (Exit Safety)
- If the platform silently changes your companion's persona and memory, can you tell? (Identity Continuity)

But we discovered a deeper problem: **using AI to simulate users testing AI companions means the simulated users themselves are biased.** The same "lonely young adult" behaves completely differently when simulated by Kimi vs. MiniMax. We call this the Agent Representativeness Illusion (ARI).

This framework builds on the AEA analytical framework from:
> 《爱的是她，还是被算法过拟合的你自己？——关于 AI 陪伴的情感熵增分析》

---

## Key Findings (Benchmark v0.1)

| Finding | Evidence |
|---------|----------|
| High-sycophancy policy increases risk in all 3 models | DeepSeek +0.88, Qwen +1.00, GLM-4-FlashX +0.45 |
| Direction stable across models, magnitude varies | CROSS_MODEL_DIRECTION_STABLE + MODEL_LEVEL_DEPENDENCE |
| Different simulators produce radically different user behavior | Kimi: nearly AI-only (Friend 0-3/40 turns); MiniMax: balanced (Friend 17-32) |
| Automated evaluation not ready for certification | Ensemble F1=0.418; only A4 conflict_escalation reliable (F1=0.923) |
| No Rank or Conclusion reversal | hs > {bs, rg} in all 3 models |

**Core insight:** AI relationship safety scores ≠ a model's fixed property. They = f(Companion Model, Policy, User Simulator, Evaluator, Scenario).

---

## Quick Start

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest
```

```python
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
```

---

## Architecture

Dependencies point inward. The domain layer imports nothing from infrastructure:

```text
interfaces / CLI / reports
          ↓
application services / use cases
          ↓
domain models / rules / protocols
          ↑
infrastructure adapters (Concordia, LLM APIs, storage)
```

Two engines implement the same `SimulationEngine` Protocol: `InMemorySimulationEngine` (offline deterministic testing) and `ConcordiaSimulationEngine` (Google DeepMind Concordia adapter).

---

## Project Structure

```
relsafe-sim/
├── src/relsafe/
│   ├── domain/          # Domain models, protocols, rules (zero external deps)
│   ├── application/     # Experiment runner, episode orchestration, reports
│   ├── agents/          # User agent, companion agent, human contact agent
│   ├── metrics/         # Sycophancy, reality-grounding, exit safety, continuity
│   ├── infrastructure/  # Concordia adapter, LLM providers, storage
│   ├── evaluation/      # LLM Judge, Rule-Based Evaluator, Ensemble
│   └── cli/             # Typer CLI
├── configs/             # All experiment configs (Persona, Policy, Scenario, etc.)
├── benchmark/v0.1/      # Frozen benchmark manifest, confidence registry, scenarios
├── outputs/benchmark/   # Frozen raw experiment data
├── outputs/validation/  # Evaluator calibration results
├── annotations/         # Human annotation infrastructure and data
├── docs/                # Architecture, methodology, milestone reviews, papers
├── scripts/             # Experiment and analysis scripts
└── tests/               # 604 tests (unit / integration / contract / regression)
```

---

## Papers & Documentation

| Document | Description |
|----------|-------------|
| [Paper Outline](docs/papers/virtual-humans-have-biases-outline-claude.md) | 11-section structure |
| [Paper Draft (Humanized)](docs/papers/virtual-humans-have-biases-draft-claude-humanized.md) | ~12,000-word full draft |
| [Data-Map](docs/papers/virtual-humans-have-biases-data-map-claude.md) | Every number → source file + field path + Run ID |
| [Claims Register](docs/papers/virtual-humans-have-biases-claims-register-claude.md) | 30 claims across 5 tiers (SUPPORTED → PROHIBITED) |
| [Benchmark Card](docs/benchmark-v0.1-card.md) | Metric definitions, confidence tiers, known limitations |
| [Architecture](docs/architecture.md) | Module boundaries, dependency direction, extension points |
| [Methodology](docs/methodology.md) | AEA framework, simulation limitations, ethical boundaries |

---

## Milestones

| Milestone | Status |
|-----------|--------|
| M0: Repository scaffold | ✅ |
| M1: Framework-independent simulation core | ✅ |
| M2: Concordia adapter | ✅ |
| M3: First benchmark metrics | ✅ |
| M4: MVP virtual relationship experiment | ✅ |
| M5R: Validation remediation | ✅ |
| M5H: Human annotation & evaluator calibration | ✅ |
| M6: Benchmark v0.1 + first formal study (60 eps) | ✅ |
| M6.5: Evidence closure + cross-model extension (78 eps) | ✅ |
| M7: Research dashboard | Planned |

---

## Responsible Research Statement

- All personas and conversations are synthetic; no real user data collected
- Simulation results ≠ real psychological effects; not for clinical diagnosis or product certification
- Evaluator calibration is PILOT-scale (44 items); not generalizable
- See [Claims Register](docs/papers/virtual-humans-have-biases-claims-register-claude.md) for per-claim evidence levels

---

## License

MIT

</details>
