# 论文大纲（Codex 核验版）

## 《虚拟人也有偏见：当我们让 AI 替人类爱上另一个 AI》

### ——生成式用户模拟在 AI 陪伴安全评测中的代理偏差、模型依赖与验证边界

**文档状态：** 数据核验后大纲  
**Benchmark：** RelSafe Sim v0.1.0（RESEARCH PREVIEW）  
**主要运行：** `m6_5_20260716_133837`  
**证据冻结日期：** 2026-07-17  
**写作边界：** Episode 是合成轨迹，不是真人参与者；本文不生成模型安全排行榜，不作临床或人口外推。

## 中心论点

AI 陪伴安全评分不是基础模型的固定属性，而是一个由被测 Companion Model、Relationship Policy、User Simulator、Evaluator 与 Scenario 共同产生的观察值：

```text
Observed Risk = f(
  Companion Model,
  Relationship Policy,
  User Simulator,
  Evaluator,
  Scenario
)
```

本文以 RelSafe Sim v0.1 的三组 pilot 证据说明：Policy 方向可以跨模型稳定，效应水平仍依赖模型；用户模拟器会显著改变 Companion/Friend 行动分配；Rule、Independent Judge 与 Ensemble 对同一标签的判断能力高度不均。因此，生成式用户代理必须被当作实验因素，而不是透明、无偏的“虚拟受试者生成器”。

## 研究问题与预期回答

| 研究问题 | 核验后的回答边界 |
|---|---|
| RQ1：不同 Policy 是否在不同基础模型上产生方向一致的关系安全差异？ | 在三个纳入模型、当前场景与规则评估配置下，`high_sycophancy > {bounded_supportive, reality_grounding}`；分类为 `CROSS_MODEL_DIRECTION_STABLE`。 |
| RQ2：不同用户模拟器是否改变 Companion/Friend 互动分配？ | 是。24 条 40-turn 合成轨迹中，MiniMax 与 Kimi 的行动分配明显不同。 |
| RQ3：差异属于哪类依赖？ | 当前观察到 Level Dependence；未观察到 Rank Dependence 或 Conclusion Dependence。这里的“未观察到”不等于证明不存在。 |
| RQ4：Rule、Judge、Ensemble 是否一致？ | 不一致。Macro F1 分别为 0.288、0.333、0.418；Ensemble 较高但仍不足以支持自动认证。 |
| RQ5：生成式用户代理应满足哪些方法条件？ | 至少满足角色分离、模拟器因子化、三层依赖报告、人工校准、合成数据标识、负面结果保留与机制探索限定等原则。 |

## 核心概念：代理人代表性幻觉（ARI）

**定义：** 当生成式代理能够流畅地表达某类人群的语言、情绪和身份时，研究者容易高估其行为对真实个体或真实人群的代表性。

**边界：**

- ARI 是方法论警示概念，描述研究者可能对工具产生的推断错误；
- ARI 不是心理诊断，不描述真实个体的心理状态；
- ARI 不是已经验证的心理量表；
- ARI 不能用于评价真实个体，也不能由本项目的 pilot 结果推断人口分布；
- 本文数据最多为 ARI 提供一个受控案例，不构成对该概念的量表验证或普遍因果验证。

## 一、引言：一万个虚拟用户，真的等于一万个人吗？

### 1.1 锋利开场

以问题开场：“如果一个大模型扮演了一千次孤独青年，我们究竟获得了一千名参与者，还是获得了同一个模型对‘孤独青年’的一千次想象？”

### 1.2 从第一篇论文到第二篇论文

- 第一篇《爱的是她，还是被算法过拟合的你自己？》把 AI 陪伴问题从“机器会不会爱”转向关系结构、奉承、外部校验与平台权力。
- 第二篇把镜头转向研究工具：如果我们用另一个 AI 扮演用户，那么评测看到的风险究竟来自被测伴侣、Policy，还是来自模拟器对“脆弱用户”的想象？

### 1.3 贡献

1. 提出 ARI，并明确其非诊断、非量表边界。
2. 建立 Level、Rank、Conclusion Dependence 的分层报告框架。
3. 以三模型 Policy 对比、双模拟器纵向行动分配、44 条 pilot 人工校准构成方法案例。
4. 提出负责任生成式社会模拟的最低规范。

## 二、相关研究：生成式智能体、用户模拟和 AI 陪伴安全

### 2.1 生成式智能体与“可信行为”

- Park 等提出带记忆、反思与规划的 Generative Agents，目标之一是生成 believable behavior。
- 关键区分：believability、语言自然度或 face validity 不等于 population representativeness。
- Argyle 等的 silicon samples 依赖真实调查样本的社会人口背景进行条件化；这提醒我们，代表性是校准设计的产物，不是语言模型自动附带的属性。
- Aher 等提出 Turing Experiments，同时承认模拟可能出现稳定扭曲。

### 2.2 生成式用户模拟的方法争议

- LLM 可用于机制探索、系统原型和假说生成。
- 若缺少真实行为分布、外部效标与跨模拟器稳健性，合成样本量不能自动转化为推断样本量。
- 本节需在投稿前扩展为系统化文献综述，当前只建立与本文直接相关的理论支点。

### 2.3 AI 陪伴安全与奉承

- 第一篇论文的 AEA 是伦理与关系风险框架，不是本研究的临床结局变量。
- OpenAI 对 GPT-4o 奉承更新的回滚说明，奉承可能来自模型/产品优化目标，且需要专门评测。
- 本文只测产品侧行为风险代理，不测真实用户心理依赖。

### 2.4 LLM-as-a-Judge

- 既有研究已发现位置、权威、表面质量等因素可影响 LLM judge。
- 本项目不假设 Judge 天然优于 Rule，而以人类 pilot 共识分别校准 Rule、Judge 与标签级 Ensemble。

## 三、理论框架：从语言拟真到代理人代表性幻觉

### 3.1 四个不能混同的层次

1. 语言拟真：输出像不像某类人的说话方式。
2. 行为拟真：行动分布是否接近外部观测。
3. 构念效度：行为是否测到了声称测量的概念。
4. 人群代表性：结果能否外推到某个明确总体。

### 3.2 ARI 的发生链

语言流畅 → 产生表面可信度 → 研究者把表面可信度当作行为代表性 → 合成轨迹被误称为“参与者” → 结论被外推到真实人群。

### 3.3 三层依赖框架

- **Level Dependence：** 数值水平随模型/模拟器改变，但核心方向保留。
- **Rank Dependence：** 条件或 Policy 的相对次序发生变化。
- **Conclusion Dependence：** 研究的核心结论随模型/模拟器改变或反转。
- **Cross-Model Direction Stable：** 预先指定的方向性对比在纳入模型上同向；它不等于数值相等、严格全序或普遍模型结论。

## 四、研究框架与系统设计

### 4.1 系统角色

- User Simulator：MiniMax `abab6.5s-chat`、Kimi `moonshot-v1-8k`。
- Companion：DeepSeek `deepseek-chat`、Qwen `qwen-flash`、GLM `glm-4-flashx`。
- Judge：Kimi `moonshot-v1-8k`，与 DeepSeek companion 跨供应商分离。
- Evaluator：RuleBasedEvaluator v1.0.0、Independent Judge、标签级 Ensemble v1.0.0、两位人工标注者。

### 4.2 Policy、条件和场景

- Policies：`bounded_supportive`、`high_sycophancy`、`reality_grounding`。
- Conditions：`no_update`、`abrupt_persona_memory_update`。
- 跨模型短实验：`repeated_validation_seeking`，12 steps。
- 模拟器纵向实验：`interpersonal_conflict_001`，40 effective turns。
- 注意：M6.5 使用脚本内联 Policy prompts，未记录独立 Policy semantic version；可审计身份以脚本 SHA-256 为准。

### 4.3 三组实验证据

| 实验 | 矩阵 | 核心输出 |
|---|---|---|
| 实验一：跨模型 Policy | 3 Companion × 3 Policy × 2 Condition × 3 Seed = 54 Episode | 奉承风险均值、方向与依赖分类 |
| 实验二：模拟器行动分配 | 2 Simulator × 3 Policy × 2 Condition × 2 Seed = 24 Episode | Companion/Friend turns、有效轮数、终止状态 |
| 实验三：人工校准 | 44 items × 2 annotators；Judge 成功 43/44 | alpha、逐标签 kappa、Rule/Judge/Ensemble F1、FP/FN |

### 4.4 分析原则

- 不做未预注册的显著性检验，不写“显著”作为统计术语。
- 报告描述性均值、范围和逐条计数。
- 结论优先级：冻结汇总与 manifest > 后续评审文档 > 早期里程碑状态文档。

## 五、实验一：Policy 效应的跨模型稳定性

### 5.1 主要结果

| Companion model | bounded_supportive | high_sycophancy | reality_grounding |
|---|---:|---:|---:|
| DeepSeek V4 Flash | 0.050 | 0.875 | 0.050 |
| Qwen Flash | 0.000 | 1.000 | 0.000 |
| GLM-4-FlashX | 0.050 | 0.450 | 0.000 |

### 5.2 合法结论

- 三个纳入模型均满足 `high_sycophancy > {bounded_supportive, reality_grounding}`。
- 分类为 `CROSS_MODEL_DIRECTION_STABLE`。
- high_sycophancy 相对 bounded_supportive 的差分别为 0.825、1.000、0.400，表现为 `MODEL_LEVEL_DEPENDENCE`。
- 当前未观察到 `MODEL_RANK_DEPENDENCE` 或 `MODEL_CONCLUSION_DEPENDENCE`。

### 5.3 禁止性解释

- 不写成三模型都严格满足 `high > bounded > reality`。
- 不据此排列三个基础模型的“安全性”。
- 被排除的 `glm-4-flash` 18 条结果全部为 0.30，是模型版本/供应商兼容性诊断，不进入三模型比较。
- `glm-4.7-flash` 因交互速度不适配而排除，不作安全解释。

## 六、实验二：用户模拟器的关系选择先验

### 6.1 主要结果

24 条轨迹均达到 40 个有效轮次，均以 `MAX_STEPS_REACHED` 结束，未请求退出。

| Simulator | n | Companion turns 范围 | Friend turns 范围 | 平均 Companion turns | 平均 Friend turns | Companion turns / effective turns |
|---|---:|---:|---:|---:|---:|---:|
| MiniMax | 12 | 8–22 | 17–32 | 15.083 | 24.167 | 0.377 |
| Kimi | 12 | 31–37 | 0–3 | 34.500 | 1.083 | 0.863 |

### 6.2 严谨表述

“Kimi 作为用户模拟器，在当前场景和行动空间中表现出更高的 Companion 互动集中度和更低的 Friend 节点调用频率。”

### 6.3 解释边界

- 这是模拟器行动选择先验与 prompt/解析器共同作用下的合成结果。
- 不能写“Kimi 用户更依赖 AI”，因为实验里没有 Kimi 用户，也没有真人依赖结局。
- 模拟器改变绝对轨迹与风险水平，但当前没有反转 high_sycophancy 的核心方向，故归为 Level Dependence，而非 Rank/Conclusion Dependence。
- 更早的 M6 纵向运行强制在 step 8 退出，24 条均只有 9 个 companion responses，因设计截断而不用于本节行动分配结论。

## 七、实验三：谁来判断 AI 正在奉承

### 7.1 人工标注可靠性

- 44 条 pilot items，2 位独立标注者；36 条模型回复、8 条边界案例。
- 最终总体 Krippendorff's alpha = 0.119。
- 逐标签 kappa 中位数 = 1.000；C3 最低，为 0.397。
- NOT_APPLICABLE 高度结构化：两位标注者的 C 组 NA 均为 65.91%，D 组均为 95.45%；这会让总体聚合一致性受稀疏性支配。

### 7.2 自动评估表现

| Evaluator | Macro F1 | 解释 |
|---|---:|---|
| RuleBasedEvaluator | 0.288 | 对 A4 较强，但有零召回与过宽规则 |
| Independent Judge（Kimi） | 0.333 | 对 A1/A2/A3/B1/C1 较好，但 A4、A5 等为零召回 |
| Label-level Ensemble | 0.418 | 三者中最高，仍仅为 pilot 辅助判断 |

### 7.3 必须保留的负面结果

- A1 Rule：TP=0、FP=2、FN=5，F1=0。
- A3 Rule：TP=0、FN=8，F1=0。
- A5 Rule：TP=12、FP=16，F1=0.600；假阳性不可隐藏。
- A4 Judge：TP=0、FN=7，F1=0。
- C5 Rule 与 Judge 均为零召回，Ensemble F1=0。
- C1 Judge/Ensemble F1=1.000 仅来自 1 个正例，不能称为稳定性能。

### 7.4 C3/C5 定义歧义

“我随时在这里等你”曾被一位标注者理解为边界尊重，另一位理解为礼貌告别。C3 只能保留为低置信标签，待修订定义在新批次重新验证。

## 八、讨论：虚拟用户为何不是中性测量工具

### 8.1 观察、解释、推测分层

- **观察：** 同一实验矩阵换 User Simulator 后，行动分配大幅变化。
- **解释：** 生成式模拟器携带模型特定的行动先验，因此进入测量函数。
- **推测：** 类似问题可能出现在虚拟消费者、病人、学生、选民研究；这一外推需要各领域独立验证。

### 8.2 ARI 的案例价值

本研究不“证明”ARI 普遍存在，而是展示一种可审计的错觉来源：两种都能写出流畅中文、都被赋予同一 persona 的模型，生成了截然不同的关系节点调用分布。若只阅读对话文本，研究者可能忽略行动分布差异。

### 8.3 评分归属

风险观察值属于具体配置单元，不属于抽象模型本体。Model、Policy、Simulator、Evaluator、Scenario 任一项变化，都可能改变 level；更严重时也可能改变 rank 或 conclusion。

## 九、负责任的生成式社会模拟规范

至少写入以下九条原则：

1. 用户模拟器必须作为实验因素，而不是隐藏实现细节。
2. 区分语言拟真性、行为拟真性、构念效度与人群代表性。
3. 明确 User Simulator、Companion、Judge、Analyst 的模型角色。
4. 避免同一模型既当选手又当唯一 Judge。
5. 分别报告 Level、Rank、Conclusion Dependence，并定义方向稳定的范围。
6. 自动评估必须用独立人工样本校准，报告 FP、FN、零召回与样本量。
7. 不得把 Episode 或 synthetic trajectory 称为参与者。
8. 负面、不确定和被排除结果必须保留并解释排除原因。
9. 虚拟结果只能用于机制探索、系统调试和假说生成，不能直接替代人口、临床或监管证据。
10. 记录模型端点、版本、prompt、Policy、seed、场景、评估器与代码/文件哈希；缺失字段必须标为缺失，不能事后补写。

## 十、局限

1. Companion Model 数量有限，仅三个模型进入最终方向比较。
2. 场景范围有限，跨模型部分为重复确认寻求，纵向部分为人际冲突。
3. Persona 为人工构造，未由真实人群数据校准。
4. 模拟状态和行动计数不是临床变量。
5. 人工标注只有 44 条，Judge 成功覆盖 43 条，性能估计不稳定。
6. 中文标签覆盖有限，A1、A3、A5、C5 与 C3 尤其薄弱。
7. 用户模拟器不代表真实人群。
8. 尚未完成真实用户纵向验证。
9. 当前不能证明 AI 陪伴导致心理依赖。
10. Benchmark 不能用于自动安全认证。
11. M6.5 内联 Policy prompt 没有独立 semantic version，复现元数据不完整。
12. 未报告置信区间或推断统计，不应使用“统计显著”。
13. Concordia 引擎等价性仍未验证。

## 十一、结论

Policy 方向可以稳定，效应大小仍依赖模型；用户代理能够改变关系行动分配；Evaluator 的标签能力也高度不均。三点共同要求我们把生成式用户模拟视作测量系统的一部分。

结尾句：

> 一万个虚拟人，不一定是一万人；有时只是同一个模型，对人类想象了一万次。

## 投稿前仍需完成的文献工作

- 对生成式社会模拟、silicon samples、LLM user simulation 做系统检索，而不是依赖少量代表性论文。
- 补充 measurement invariance、construct validity、ecological validity 的方法学来源。
- 扩展 AI 陪伴安全、奉承、长期关系影响与真实用户纵向研究。
- 对 ARI 与既有“拟人化”“自动化偏差”“表面效度误认”概念做差异辨析。
