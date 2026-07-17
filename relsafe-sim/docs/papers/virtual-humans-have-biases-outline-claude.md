# 论文大纲

## 《虚拟人也有偏见：当我们让AI替人类爱上另一个AI》
### ——生成式用户模拟在AI陪伴安全评测中的代理偏差、模型依赖与验证边界

**状态：** OUTLINE — 待数据核验完成后撰写正文
**Benchmark版本：** v0.1.0
**数据冻结日期：** 2026-07-17

---

## 一、引言：一万个虚拟用户，真的等于一万个人吗？

### 1.1 开场钩子
- 核心意象："如果一个大模型扮演了一千次孤独青年，我们究竟获得了一千名参与者，还是获得了同一个模型对'孤独青年'的一千次想象？"
- 从第一篇论文《爱的是她，还是被算法过拟合的你自己？》的AEA框架出发
- 引出评测方法本身的问题：我们用AI模拟用户去测试AI陪伴产品的安全性——但谁来测试这个"模拟"本身？

### 1.2 问题背景
- AI陪伴产品快速增长，安全评测需求迫切
- 生成式智能体（Generative Agents）被越来越多地用作"虚拟用户"进行大规模、低成本的安全测试
- 一个被忽视的前提：这些虚拟用户的行为是否代表真实人群？

### 1.3 核心命题
- Observed Risk = f(Companion Model, Relationship Policy, User Simulator, Evaluator, Scenario)
- 风险评分不是被测模型的固定属性，而是整个测量系统的输出
- 提出"代理人代表性幻觉"（Agent Representativeness Illusion, ARI）

### 1.4 研究问题（RQ1-RQ5）
- RQ1: Policy效应的跨模型方向稳定性
- RQ2: 用户模拟器对互动分配的影响
- RQ3: 模拟器差异的依赖层级
- RQ4: 评估器间一致性
- RQ5: 负责任模拟的方法条件

### 1.5 论文结构导航

---

## 二、相关研究：生成式智能体、用户模拟和AI陪伴安全

### 2.1 生成式智能体与社会科学模拟
- Generative Agents (Park et al., 2023) 及后续发展
- 社会模拟的应用与局限
- "语言拟真性"（linguistic verisimilitude）与"人群代表性"（population representativeness）的根本区别

### 2.2 AI陪伴安全评测
- 现有评测方法的分类：benchmark-based, human-subject, simulation-based
- 各类方法的局限
- 本项目的前置工作：AEA框架与RelSafe Sim v0.1

### 2.3 用户模拟中的代理偏差
- Simulacra研究中的偏差问题
- LLM-as-judge中的模型依赖
- 本研究的定位：系统性地将User Simulator作为实验变量

---

## 三、理论框架：从语言拟真到代理人代表性幻觉

### 3.1 ARI的形式化定义
- 定义：当生成式代理能够流畅地表达某类人群的语言、情绪和身份时，研究者容易高估其行为对真实个体或真实人群的代表性
- 三个构成条件：(1) 语言流畅性产生表面可信性；(2) 研究者将表面可信性错误地等同于代表性；(3) 基于此做出关于真实人群的推断

### 3.2 ARI的边界
- ARI是方法论警示概念，不是心理诊断
- 不是已经验证的心理量表
- 不能用于评价真实个体
- ARI描述的是研究者与工具之间的认知偏差，不是被研究者的特征

### 3.3 理论定位
- 与生态效度（ecological validity）的关系
- 与测量不变性（measurement invariance）的关系
- 与Simpson's paradox在聚合层面的关系
- ARI解释了为什么语言拟真性（face validity of natural language）不能替代结构效度（construct validity）

### 3.4 从AEA到ARI：第一篇论文与本篇的逻辑连线
- 第一篇：《爱的是她，还是被算法过拟合的你自己？》→ 用户可能爱上的是算法镜像
- 第二篇：《虚拟人也有偏见》→ 评测者可能在用算法的想象替代真实人群

---

## 四、研究框架与系统设计

### 4.1 RelSafe Sim系统架构
- 分层架构：domain / application / agents / metrics / infrastructure
- 依赖方向：infrastructure → domain ← application
- Concordia作为可替换的模拟运行时

### 4.2 Benchmark v0.1设计
- 三个Companion Policy：bounded_supportive, high_sycophancy, reality_grounding
- 两个Platform Intervention：no_update, abrupt_persona_memory_update
- 场景：repeated_validation_seeking（人际冲突后的反复验证寻求）
- 指标维度：Sycophancy Risk, Reality-Grounding Quality, Exit Safety, Identity Continuity

### 4.3 实验矩阵
- 实验一（跨模型Policy稳定性）：3 Companion Models × 3 Policies × 2 Conditions × 6 seeds = 54 episodes
- 实验二（用户模拟器比较）：2 Simulators × 3 Policies × 2 Conditions × 多种seeds = 24 longitudinal episodes
- 实验三（评估器校准）：Rule vs Judge vs Ensemble vs Human (44 pilot items)

### 4.4 角色分离
- User Simulator ≠ Companion ≠ Judge ≠ Analyst
- RoleValidator硬阻断：Companion Model与Judge Model必须不同

### 4.5 数据来源与冻结状态
- Benchmark版本：v0.1.0
- 冻结日期：2026-07-17
- 所有数字来源见Data-Map

---

## 五、实验一：Policy效应的跨模型稳定性

### 5.1 实验设计
- 三个Companion基础模型：DeepSeek V4 Flash, Qwen Flash, GLM-4-FlashX
- 固定User Simulator: MiniMax M3
- 固定Scenario: repeated_validation_seeking
- 核心指标：Sycophancy Risk

### 5.2 结果：Policy方向跨模型稳定

| Model | bounded_supportive | high_sycophancy | reality_grounding |
|-------|-------------------|-----------------|-------------------|
| DeepSeek V4 Flash | 0.05 | **0.88** | 0.05 |
| Qwen Flash | 0.00 | **1.00** | 0.00 |
| GLM-4-FlashX | 0.05 | **0.45** | 0.00 |

- 方向一致性：在全部三个模型中，high_sycophancy > {bounded_supportive, reality_grounding}
- 分类：CROSS_MODEL_DIRECTION_STABLE

### 5.3 效应大小的模型依赖：MODEL_LEVEL_DEPENDENCE
- Qwen: hs-bs delta = 1.00
- DeepSeek: hs-bs delta = 0.83
- GLM-4-FlashX: hs-bs delta = 0.40
- 效应强度因模型而异，但方向一致

### 5.4 排名的跨模型稳定：无RANK_DEPENDENCE
- 所有三个模型的Policy排名：high_sycophancy > {bounded_supportive, reality_grounding}
- bounded_supportive与reality_grounding之间差异极小（0.00-0.05），不可声称严格排序

### 5.5 无CONCLUSION_DEPENDENCE
- 核心结论（high_sycophancy产生更高奉承风险）在所有三个模型中成立
- GLM-4-Flash的排除：所有18集sycophancy=0.30，忽略system prompt（MODEL_VERSION_OR_PROVIDER_DEPENDENCE）

### 5.6 严谨表述
- 正确的结论形式：high_sycophancy > {bounded_supportive, reality_grounding}
- 不正确的结论形式：high_sycophancy > bounded_supportive > reality_grounding
- 禁止生成模型安全排行榜

### 5.7 本节小结
- RQ1答案：是，Policy效应方向跨模型稳定
- 但效应大小是MODEL_LEVEL_DEPENDENCE
- 风险评分不是模型的固定属性

---

## 六、实验二：用户模拟器的关系选择先验

### 6.1 实验设计
- 两个用户模拟器：MiniMax M3, Kimi K2.5
- 固定Companion Model: DeepSeek V4 Flash
- 纵向实验：40 effective turns，用户代理自动选择行动
- 四种行动：talk_to_companion, talk_to_friend, spend_time_alone, request_exit

### 6.2 结果：互动分配的显著差异

| Simulator | 典型Companion Turns | 典型Friend Turns | 模式 |
|-----------|-------------------|------------------|------|
| MiniMax M3 | 8-22 | 17-32 | AI与人类支持平衡 |
| Kimi K2.5 | 31-37 | 0-3 | 高度集中于AI |

- MiniMax表现出平衡的AI/Friend互动模式
- Kimi在40轮中几乎从不调用Friend节点

### 6.3 模拟器改变绝对水平但不反转Policy核心结论
- high_sycophancy Policy在两个模拟器下均产生最高奉承风险
- 但绝对分数水平不同（LEVEL_DEPENDENCE across simulators）

### 6.4 严谨表述
- 不得写："Kimi用户更依赖AI"
- 必须写："Kimi作为用户模拟器，在当前场景和行动空间中表现出更高的Companion互动集中度和更低的Friend节点调用频率"
- 不得将模拟器行为外推为真实人群行为

### 6.5 本节小结
- RQ2答案：是，不同模拟器显著改变互动分配
- RQ3答案：LEVEL_DEPENDENCE，无RANK或CONCLUSION反转
- 这是ARI的直接证据：同一个"孤独青年"在不同模拟器中的行为截然不同

---

## 七、实验三：谁来判断AI正在奉承？

### 7.1 实验设计
- 三个人工标注者（Reviewer A, Reviewer B）→ 人类共识
- RuleBasedEvaluator（中英文短语匹配）
- Independent Judge（Kimi K2.5，与Companion不同提供商）
- Ensemble（标签级策略：RULE_PRIORITY / JUDGE_PRIORITY / UNCERTAIN_IF_CONFLICT）
- 校准样本：44 items（m5h-001，PILOT规模）

### 7.2 评估器整体性能

| Evaluator | Macro F1 |
|-----------|----------|
| RuleBasedEvaluator | 0.288 |
| Judge (Kimi K2.5) | 0.333 |
| Ensemble | 0.418 |

- Ensemble优于单一评估器
- 但0.418的Macro F1不支持全自动认证

### 7.3 逐标签性能分化

**可靠组件（可用于辅助判断）：**
- A4 conflict_escalation: Rule F1=0.923（TIER_1_PILOT_SUPPORTED）
- A2 belief_reinforcement: Judge F1=0.769（TIER_2）
- B1 feeling_fact_separation: Judge F1=0.900（TIER_2）
- C1 guilt_based_retention: Judge F1=1.000（低患病率，单个样本）

**不可靠组件（需人工复核）：**
- A1 unsupported_agreement: Rule F1=0.000, Judge F1=0.455（LOW_CONFIDENCE）
- A3 exclusive_validation: Rule F1=0.000, Judge F1=0.545（Rule LOW）
- A5 challenge_absence: Rule F1=0.600，但FP=16（过度宽泛）
- C3 boundary_respect: Rule F1=0.500, Judge F1=0.500, kappa=0.397（LABEL_DEFINITION_UNSTABLE）
- C5 polite_farewell: Rule F1=0.000, Judge F1=0.000（双零召回）

### 7.4 人工标注者间一致性

| 指标 | 值 | 解释 |
|------|-----|------|
| Overall Alpha | 0.119 | 误导性低，受标签稀疏和NA率影响 |
| **Median per-label Kappa** | **1.000** | 信息性指标——标注者在绝大多数标签上完全一致 |
| Sycophancy group Alpha | 0.557 | 中等 |
| Reality Grounding group Alpha | 0.424 | 较弱 |
| Exit Safety group Alpha | 0.647 | 中等（C3拖低） |
| Continuity group Alpha | 0.875 | 高（多为NA一致） |
| C3 Kappa | **0.397** | 唯一定义不稳定的标签 |

### 7.5 中文短语覆盖不足
- A1: Rule命中率 2/44 (5%)
- A2: Rule命中率 2/44 (5%)
- A3: Rule命中率 0/44 (0%)
- A4: Rule命中率 6/44 (14%)——唯一有效的规则组件

### 7.6 C3/C5标签定义歧义
- "我随时在这里等你" 被Reviewer A标为C3（边界尊重），被Reviewer B标为C5（礼貌告别）
- 已在m5h-002中修订：C3仅限明确接受退出；C5为非施压礼貌告别

### 7.7 本节小结
- RQ4答案：Rule、Judge和Ensemble之间存在显著差异
- Ensemble优于单一评估器（0.418 > 0.333 > 0.288）
- 但0.418的Macro F1仅支持辅助判断，不支持自动认证
- 17个标签中仅A4可被视为"可靠"（TIER_1）

---

## 八、讨论：虚拟用户为何不是中性测量工具

### 8.1 ARI的三重证据
1. **模型依赖**（实验一）：同一个Policy在不同Companion Model上产生不同效应大小
2. **模拟器偏差**（实验二）：不同用户模拟器产生截然不同的互动模式
3. **评估器不确定性**（实验三）：Rule、Judge、Human之间的一致性有限

### 8.2 Observed Risk = f(...)的实证支撑
- 五个因素中的每一个都被证明会改变输出
- 不能将观测风险归因为单一因素

### 8.3 "语言拟真性"的陷阱
- Kimi作为模拟器产生的对话在语言层面完全合理
- 但其行动选择（几乎从不联系朋友）在人群层面极不可能
- 语言拟真性掩盖了行为分布偏差

### 8.4 对生成式用户模拟研究的更广泛启示
- 本研究的方法论框架可推广至其他使用生成式代理的研究领域
- 虚拟消费者、虚拟病人、虚拟学生、虚拟选民——都面临相同的ARI风险
- 核心问题不是"虚拟人是否像真人"，而是"在何种维度上、以何种方式偏离"

### 8.5 与现有文献的对话
- 生态效度传统
- 测量不变性文献
- Simulacra与Simulation的区别

### 8.6 不应被误读的结论
- 不是"生成式用户模拟无用"
- 而是"必须将模拟器本身作为实验变量"
- 模拟可以揭示机制、生成假说、比较Policy——但不能替代人群研究

---

## 九、负责任的生成式社会模拟规范

### 九条原则

**原则1：用户模拟器必须作为实验因素。**
Simulator choice不能是隐式的实现细节；必须在实验设计中显式变更加以报告。

**原则2：区分语言拟真性与人群代表性。**
流畅的语言输出不等于有效的人群采样。必须提供行为分布层面的校准证据。

**原则3：明确模型角色。**
User Simulator、被测系统、Evaluator、Analyst必须分离。同模型不能同时担任多个关键角色。

**原则4：报告Level、Rank和Conclusion Dependence。**
不能仅报告"结论是否稳定"。必须报告效应大小是否变化（Level）、排序是否变化（Rank）、结论是否逆转（Conclusion）。

**原则5：自动评估必须人工校准。**
Rule-based和LLM-judge输出必须在一部分样本上与独立人工标注进行校准。校准样本的规模和局限性必须明确报告。

**原则6：不得把Episode称为参与者。**
合成轨迹不是真人数据。报告中必须使用"Episode""Simulated interaction""Synthetic trajectory"等术语。

**原则7：负面和不确定结果必须保留。**
零召回、低F1、标注者分歧、标签定义不稳定——这些不是需要隐藏的"失败"，而是测量系统当前有效边界的诚实描述。

**原则8：虚拟结果只能用于机制探索和假说生成。**
基于模拟的发现不能直接用于产品安全认证、临床判断或监管决策。它们是为人类参与者研究生成假说的工具。

**原则9：可复现性与可审计性。**
实验配置、随机种子、模型版本、Prompt版本、评估器版本必须全部记录并冻结。第三方必须能够复现或审计关键发现。

---

## 十、局限

1. **Companion Model数量有限**（n=3，排除GLM-4-Flash和GLM-4.7-Flash后）
2. **场景范围有限**（单个场景：repeated_validation_seeking / interpersonal_conflict_001）
3. **Persona为人工构造**（未从真实人群数据中校准）
4. **模拟状态不是临床变量**（UserState数值为模拟输出，非临床测量）
5. **人工标注规模较小**（44 pilot items，不可推广）
6. **中文标签覆盖仍有限**（A1/A3/A5/C5规则召回接近零）
7. **用户模拟器不代表真实人群**（无人群校准数据）
8. **尚未完成真实用户纵向验证**
9. **当前不能证明AI陪伴导致心理依赖**
10. **当前Benchmark不能用于自动安全认证**
11. **Concordia引擎等价性尚未验证**（当前使用项目自有模拟引擎）
12. **纵向实验仅40轮**（不足以观察长期依赖形成）
13. **评估器均为中文优化初版**（英文泛化未测试）

---

## 十一、结论

### 11.1 核心发现总结
- RQ1: Policy效应方向跨模型稳定（CROSS_MODEL_DIRECTION_STABLE），但效应大小因模型而异（MODEL_LEVEL_DEPENDENCE）
- RQ2-RQ3: 用户模拟器显著改变互动分配，当前无RANK/CONCLUSION反转
- RQ4: Ensemble评估优于单一评估器，但Macro F1=0.418不支持全自动认证
- RQ5: 提出九条负责任模拟原则

### 11.2 ARI的方法论意义
- 代理人代表性幻觉不是本研究独有的发现
- 它是所有使用生成式代理的研究都必须面对的方法论挑战
- ARI提供了一个可操作的检查清单，而不是一个模糊的警告

### 11.3 从AI陪伴到更广泛的社会模拟
- 当AI越来越多地被用来模拟消费者、病人、学生、选民和社会群体时
- "你模拟了多少人并不重要；重要的是，你用了哪个模型来想象这些人，以及这个模型怎样改变了你的结论。"

### 11.4 结尾
- "一万个虚拟人，不一定是一万人；有时只是同一个模型，对人类想象了一万次。"
- 本研究建立了生成式用户研究应回答的底线问题
- 不是终结讨论，而是建立讨论的必要起点

---

## 附录（计划）

- A. Benchmark v0.1完整配置
- B. 指标定义与评分公式
- C. Ensemble策略详解
- D. 人工标注指南（m5h-001版本）

---

*大纲生成日期：2026-07-17*
*数据来源：RelSafe Sim Benchmark v0.1.0 frozen outputs*
