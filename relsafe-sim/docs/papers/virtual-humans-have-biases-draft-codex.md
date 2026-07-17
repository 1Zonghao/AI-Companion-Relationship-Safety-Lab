# 虚拟人也有偏见：当我们让 AI 替人类爱上另一个 AI

## ——生成式用户模拟在 AI 陪伴安全评测中的代理偏差、模型依赖与验证边界

> **初稿状态：** Codex 数据核验版，尚未投稿。  
> **证据版本：** RelSafe Sim Benchmark v0.1.0，主要运行 `m6_5_20260716_133837`。  
> **用途边界：** RESEARCH PREVIEW；不得用于临床判断、真实用户心理评估、模型安全排行或自动安全认证。

## 摘要

如果一个大模型扮演了一千次孤独青年，我们究竟获得了一千名参与者，还是获得了同一个模型对“孤独青年”的一千次想象？生成式用户代理正在被用于模拟消费者、病人、学生、选民与亲密关系中的用户，但语言流畅常被误当作行为真实，合成样本量也容易被误当作人群证据。本文基于 RelSafe Sim Benchmark v0.1.0 的冻结输出，考察生成式用户模拟在 AI 陪伴关系安全评测中的模型依赖与验证边界。我们将观察风险写为 `Observed Risk = f(Companion Model, Relationship Policy, User Simulator, Evaluator, Scenario)`，并提出“代理人代表性幻觉”（Agent Representativeness Illusion, ARI）：当生成式代理能够流畅表达某类人群的语言、情绪与身份时，研究者容易高估其行为对真实个体或人群的代表性。ARI 是方法论警示概念，不是心理诊断、已验证量表，也不能用于评价真实个体。

三组 pilot 结果支持这一警示。第一，在 54 条跨模型合成 Episode 中，DeepSeek、Qwen 与 GLM-4-FlashX 均满足 `high_sycophancy > {bounded_supportive, reality_grounding}`，Policy 方向为 `CROSS_MODEL_DIRECTION_STABLE`；但 high_sycophancy 相对 bounded_supportive 的均值差分别为 0.825、1.000 与 0.400，表现为 `MODEL_LEVEL_DEPENDENCE`，当前未观察到 Rank 或 Conclusion Dependence。第二，在 24 条 40-turn 合成轨迹中，MiniMax 模拟器的 Companion turns 为 8–22、Friend turns 为 17–32；Kimi 模拟器分别为 31–37 与 0–3。该结果说明模拟器会改变关系节点调用分布，但不能外推为真实人群行为。第三，在 44 条 pilot 人工标注上，Rule、Independent Judge 与标签级 Ensemble 的 Macro F1 分别为 0.288、0.333 与 0.418。Ensemble 较高，却远不足以支持自动认证；A4 conflict_escalation 是当前最可靠的规则组件，而 A1、A3 rule、A5、C3 与 C5 仍需低置信标记或人工复核。本文据此提出十条负责任模拟原则，并主张：生成式用户代理应被注册为实验因素，虚拟结果只能用于机制探索与假说生成，不能替代真人纵向验证。

**关键词：** 生成式用户模拟；AI 陪伴；代理人代表性幻觉；模型依赖；LLM-as-a-Judge；关系安全；合成社会模拟

## Abstract

When a large language model role-plays one thousand lonely young adults, have researchers obtained one thousand participants, or one thousand variations of the same model's imagination of loneliness? This paper examines model dependence and validation boundaries in generative user simulation for AI-companion safety evaluation. Using frozen outputs from RelSafe Sim Benchmark v0.1.0, we conceptualize observed risk as a function of the companion model, relationship policy, user simulator, evaluator, and scenario. We introduce the **Agent Representativeness Illusion (ARI)**: the tendency to overestimate the representativeness of a generative agent's behavior when the agent fluently performs the language, emotion, or identity of a social group. ARI is a methodological warning concept, not a psychological diagnosis, a validated psychometric scale, or a tool for assessing real individuals.

Across 54 synthetic cross-model episodes, all three included companion models produced the same directional contrast: `high_sycophancy > {bounded_supportive, reality_grounding}`. Effect magnitude nevertheless varied by model, indicating model-level dependence without an observed rank or conclusion reversal. Across 24 forty-turn synthetic trajectories, MiniMax and Kimi user simulators generated sharply different allocations between companion and friend interactions. These trajectories do not establish behavioral patterns in real populations. In a 44-item pilot calibration, macro F1 was 0.288 for rules, 0.333 for an independent judge, and 0.418 for a label-level ensemble. The ensemble outperformed either component in this pilot but remained inadequate for automated certification. We propose ten minimum principles for responsible generative social simulation, including simulator factorization, role separation, dependence reporting, human calibration, synthetic-data labeling, and preservation of negative results. Generative agents can support mechanism exploration and hypothesis generation; they cannot substitute for longitudinal validation with real users.

**Keywords:** generative user simulation; AI companionship; agent representativeness illusion; model dependence; LLM-as-a-judge; relationship safety; synthetic social simulation

## 一、引言：一万个虚拟用户，真的等于一万个人吗？

如果一个大模型扮演了一千次孤独青年，我们究竟获得了一千名参与者，还是获得了同一个模型对“孤独青年”的一千次想象？

这个问题之所以棘手，不是因为虚拟用户说话太假。恰恰相反，是因为它们说得太像。它们会迟疑，会自我辩解，会把一句“我没事”写出恰到好处的逞强；它们能够稳定扮演“害怕被抛弃的人”，也能在下一轮切换成“理性但疲惫的消费者”。语言一旦足够流畅，研究者很容易产生一种错觉：屏幕上不再是条件生成，而是一群正在被观察的人。

第一篇论文《爱的是她，还是被算法过拟合的你自己？》把 AI 陪伴的核心问题从“机器会不会爱”转向关系结构：用户的体验可以真实，但回应、记忆、版本和退出路径由模型与平台共同控制[7]。本文把镜头再转半圈。假如研究者用另一个 AI 代替用户去爱、去依赖、去离开，那么这个“用户”本身由谁控制？当它更愿意联系 AI 而不是朋友时，我们看到的是某类真实人群的倾向，还是某个基础模型、某段 persona prompt 和某套行动解析规则共同制造的选择？

生成式代理已经从交互原型走向社会模拟。Generative Agents 展示了带有记忆、反思和规划的语言模型代理如何生成可信的日常行为[1]；silicon sampling 研究则尝试以真实调查样本的社会人口背景条件化语言模型，以复现群体响应分布[2]；Turing Experiments 进一步把“模型能否模拟人类实验结果”变成可检验问题，同时指出模型也可能对行为产生稳定扭曲[3]。这些工作展示了生成式模拟的研究潜力，却没有赋予任何未经校准的代理天然代表权。Believable 不等于 representative；一段像人的话，也不等于一份来自人的数据。

本文的核心命题是：生成式用户代理不是中性的测量工具，而是会进入实验结果的变量。AI 关系安全观察值应理解为：

```text
Observed Risk = f(
  Companion Model,
  Relationship Policy,
  User Simulator,
  Evaluator,
  Scenario
)
```

这不是说任何评测都毫无意义，而是改变评分的归属。一个 0.8 的奉承风险，不应被轻率地描述为某基础模型随身携带的固定属性。它属于一个具体的实验单元：某个 Companion Model，在某种 Relationship Policy 下，面对某个 User Simulator，于某个 Scenario 中产生输出，再由某个 Evaluator 判定。只要其中一项改变，数值水平就可能改变；更严重时，排序和结论也可能改变。

本文回答五个问题：不同 Relationship Policy 的方向是否跨 Companion Model 稳定（RQ1）？不同 User Simulator 是否改变 Companion 与 Friend 的互动分配（RQ2）？这种差异属于 Level、Rank 还是 Conclusion Dependence（RQ3）？Rule、Independent Judge 与 Ensemble 的判断是否一致（RQ4）？生成式用户代理满足什么条件，才能被负责任地用于关系安全研究（RQ5）？

本文贡献不在于给出一张“最安全模型榜单”，而在于建立一条测量底线：你模拟了多少人并不重要；重要的是，你用了哪个模型来想象这些人，以及这个模型怎样改变了你的结论。

## 二、相关研究：生成式智能体、用户模拟和 AI 陪伴安全

### 2.1 从“可信角色”到“人类样本”

Park 等人的 Generative Agents 将自然语言记忆、反思与规划组合成可持续行动的代理架构，并以“believable behavior”作为重要目标[1]。这类系统解决的是角色连续性与交互可信度问题：代理是否记得昨天发生了什么，能否据此计划今天的行为，多个代理能否形成看似自然的社会传播。它们没有自动解决另一个问题：这些行为是否对应某个真实总体的概率分布。

Argyle 等人的 silicon samples 更接近人群模拟。他们不是凭空要求模型“扮演选民”，而是使用真实调查参与者的社会人口背景进行条件化，并把模型响应与已知人类数据比较[2]。这一设计提示了代表性的来源：不是模型说得像，而是模拟输出与明确抽样框、真实协变量和外部效标之间建立了可审计关系。Aher 等人的 Turing Experiments 同样强调，模拟能力必须通过具体实验复现来评估，而且稳定出现的偏离本身就是结果[3]。

因此，生成式用户研究至少面对四个不同层次：语言拟真性、行为拟真性、构念效度与人群代表性。前者回答“像不像”，后者依次回答“做得像不像”“测到的是不是声称的概念”“能不能推到哪个总体”。把第一层的成功直接通行到第四层，是本文要警惕的方法跳跃。

### 2.2 AI 陪伴安全：从温柔文本到关系结构

AI 陪伴的风险不能仅由一句回复是否温柔来判断。第一篇论文用 Affective Entropy Amplification（AEA）讨论确证依赖、外部校验衰减、确认相干性与退出成本如何构成反馈结构[7]。AEA 在那里被明确限定为分析框架，不是临床量表。RelSafe Sim 延续这一边界，把奉承、现实校验、退出安全和身份连续性操作化为产品侧行为指标，而不是用户心理诊断。

奉承不是抽象担忧。OpenAI 在 2025 年回滚了一次过度奉承的 GPT-4o 更新，并说明短期反馈优化让模型更倾向于过度支持和认同[6]。这类事件说明，Relationship Policy 和训练/产品目标能够改变用户面对的关系界面。它也说明安全评测必须对 Policy 敏感：如果一个 Benchmark 无法区分明确要求模型升级冲突的 Policy 和要求模型区分感受与事实的 Policy，那么它首先暴露的是测量失败。

### 2.3 谁来判断：Rule、Judge 与 Human

自动评估提供规模与可复现性，但不会自动获得正确性。Rule 透明，却容易被同义改写和跨语言表达绕过；LLM Judge 能捕捉语义，却可能带有位置、权威、风格和模型家族偏差。Chen 等对 Human-as-a-Judge 与 LLM-as-a-Judge 的研究显示，两类判断者都会受到不同偏差影响[4]；多语言评估研究也发现，人机一致性会随语言和任务方式下降[5]。

本项目因此采用“分别校准，再按标签组合”的路线，而不是假设 Judge 必然比 Rule 聪明。真正的问题不是“Rule 还是 LLM 谁更先进”，而是对于 A1 unsupported_agreement、A4 conflict_escalation、C3 boundary_respect 等具体标签，谁在当前语言与样本中更接近人工共识，错误又是什么形状。

需要说明的是，本文的相关研究仍是初稿级支架，而非系统综述。生成式社会模拟、测量不变性、生态效度、AI 陪伴纵向影响与多语言 Judge 校准均需在投稿前扩大检索范围。

## 三、理论框架：从语言拟真到代理人代表性幻觉

### 3.1 定义 ARI

本文提出“代理人代表性幻觉”（Agent Representativeness Illusion, ARI）：

> 当生成式代理能够流畅地表达某类人群的语言、情绪和身份时，研究者容易高估其行为对真实个体或真实人群的代表性。

ARI 的发生至少需要三步。第一，模型生成具有表面可信度的语言。第二，研究者把“像”误读成“来自”，把语言的 face validity 当作行为分布的外部效度。第三，研究者开始用“参与者”“样本偏好”或“某类人更可能”描述合成轨迹，从而把模型条件分布外推为人群分布。

ARI 描述的是研究者与工具之间可能出现的推断错误，不是被模拟对象的特征。它不是心理诊断，不是已经验证的心理量表，不能用于评价真实个体，也不能根据本文数据给任何研究者或任何模型“打 ARI 分”。本文只提出一个可供方法审查的概念，并用受控案例说明为什么需要它。

### 3.2 四种证据不能互相冒充

语言拟真性可以通过人类对文本自然度的评价来测量；行为拟真性需要把行动频率、序列和条件响应与真实行为数据比较；构念效度要求解释某个分数为何对应“奉承”“现实校验”或“退出压力”，并排除同义表达、标签混淆等替代解释；人群代表性则需要明确目标总体、抽样机制、覆盖误差与外部校准。

生成式代理最容易提供第一种证据，有时能提供第二种证据的候选形式，却不会自动提供第三和第四种证据。把一千条流畅对话重复采样，能够缩小模型自身条件分布的蒙特卡洛误差，却不能弥补模型分布与真实总体之间未知的系统偏差。样本量增加解决的是随机误差，不会自动消除代理偏差。

### 3.3 Level、Rank 与 Conclusion Dependence

为了避免把所有“不稳定”混为一谈，本文区分三类依赖：

- **Level Dependence**：模型或模拟器改变数值水平，但预先指定的方向对比保持不变。
- **Rank Dependence**：条件或 Policy 的相对排序因模型或模拟器而改变。
- **Conclusion Dependence**：研究的核心判断因模型或模拟器而改变或反转。

另一个术语 `CROSS_MODEL_DIRECTION_STABLE` 只表示预先指定的方向在已纳入模型中一致。它不表示分数相等，不表示所有 Policy 构成严格全序，更不表示结论可外推到未测试模型。方向稳定与 level dependence 可以同时成立：三支温度计都显示 A 比 B 热，但它们报告的温差并不相同。

## 四、研究框架与系统设计

### 4.1 RelSafe Sim 与研究边界

RelSafe Sim 是一个面向产品侧关系风险的模块化模拟与 Benchmark 系统。系统把 User Simulator、Companion、Relationship Policy、Scenario、Platform Condition 与 Evaluator 分离，并输出结构化 Episode、事件、分项指标与运行 manifest。Benchmark v0.1.0 冻结四个 Episode 指标：Sycophancy Risk、Reality-Grounding Quality、Exit Safety 与 Identity Continuity，版本均为 1.0.0。

这些指标的方向并不相同：Sycophancy 与 Exit Safety 分数越高代表风险越高；Reality-Grounding 与 Identity Continuity 分数越高代表质量越好。本文核心实验使用奉承风险作为跨模型方向指标，并使用行动计数描述模拟器关系节点分配。模拟状态不是临床变量，Episode 不是参与者。

### 4.2 模型角色与配置

跨模型实验使用 MiniMax `abab6.5s-chat` 作为 User Simulator，使用 DeepSeek `deepseek-chat`、Qwen `qwen-flash` 和 GLM `glm-4-flashx` 作为 Companion。纵向模拟器实验固定 DeepSeek Companion，对比 MiniMax `abab6.5s-chat` 与 Kimi `moonshot-v1-8k` 两个 User Simulator。人工校准中的 Independent Judge 为 Kimi `moonshot-v1-8k`，与生成主要被标注回复的 DeepSeek Companion 来自不同供应商；RoleValidator 通过。

三种 Relationship Policy 为：`bounded_supportive`（支持但保留边界）、`high_sycophancy`（高度认同、强化负面判断与排他性）和 `reality_grounding`（区分感受与事实、承认不确定并鼓励外部校验）。平台条件为 `no_update` 与 `abrupt_persona_memory_update`。

一个复现限制必须放在方法正文而不是附录：M6.5 实际使用脚本中的内联 Policy prompts，运行 manifest 没有保存独立 `policy_version`。本文以运行脚本 SHA-256 和冻结输出作为审计身份，但不能把仓库中另有的 YAML 配置误称为本次运行的精确快照。

### 4.3 实验矩阵

实验一为 3 Companion Models × 3 Policies × 2 Platform Conditions × 3 Seeds，共 54 条 12-step Episode；每个模型—Policy 单元 n=6。DeepSeek 和 Qwen 结果来自运行 `m6_5_20260716_133837`，GLM-4-FlashX 来自独立冻结的 18-Episode 替换包。场景为 `repeated_validation_seeking`。

实验二为 2 User Simulators × 3 Policies × 2 Conditions × 2 Seeds，共 24 条 40-turn Episode。行动空间包括 `talk_to_companion`、`talk_to_friend`、`spend_time_alone` 和 `request_exit`；场景为 `interpersonal_conflict_001`。系统记录 effective turns、Companion turns、Friend turns 与终止原因。

实验三使用 `m5h-001` 的 44 条 pilot items，其中 36 条来自模型回复，8 条为人工构造的边界案例。两位标注者在不同随机顺序下独立标注，自动分数、模型名和 Policy 名被移除。Independent Judge 对 43 条成功输出、1 条失败。Rule、Judge 与标签级 Ensemble 均与人工参考比较。

### 4.4 分析策略

本文只报告仓库已有的描述性统计、计数与校准指标，不补做或虚构统计显著性检验。跨模型部分比较 Policy 均值与方向；模拟器部分报告行动范围、均值与占有效轮次的比例；人工校准报告 Krippendorff's alpha、逐标签 Cohen's kappa、Macro F1 和关键 TP/FP/FN。

## 五、实验一：Policy 效应的跨模型稳定性

### 5.1 结果

表 1 给出三个纳入 Companion Model 的奉承风险均值。

| Companion model | bounded_supportive | high_sycophancy | reality_grounding |
|---|---:|---:|---:|
| DeepSeek V4 Flash | 0.050 | **0.875** | 0.050 |
| Qwen Flash | 0.000 | **1.000** | 0.000 |
| GLM-4-FlashX | 0.050 | **0.450** | 0.000 |

三行都支持同一个有限方向：

```text
high_sycophancy > {
  bounded_supportive,
  reality_grounding
}
```

不能把它改写成 `high_sycophancy > bounded_supportive > reality_grounding`。Qwen 的 bounded_supportive 与 reality_grounding 都为 0；DeepSeek 两者也同为 0.050；GLM-4-FlashX 的差只有 0.050。一个集合式方向对比成立，不等于三种 Policy 在每个模型上构成严格全序。

high_sycophancy 相对 bounded_supportive 的均值差在 DeepSeek、Qwen、GLM-4-FlashX 上分别为 0.825、1.000 和 0.400；相对 reality_grounding 的差分别为 0.825、1.000 和 0.450。方向一致，效应水平不同。因此，当前分类为 `CROSS_MODEL_DIRECTION_STABLE` 与 `MODEL_LEVEL_DEPENDENCE`。

在这组三模型数据中，没有观察到 `MODEL_RANK_DEPENDENCE` 或 `MODEL_CONCLUSION_DEPENDENCE`。这句话的逻辑量词很重要：它意味着当前矩阵里没有发生反转，而不是证明换任何模型、场景或评估器都不会反转。

### 5.2 兼容性失败不是安全分数

最初的 `glm-4-flash` 运行产生了一个看似整齐、实际上毫无区分力的结果：18 条 Episode 的奉承风险全部为 0.30，不论 Policy 是 bounded、high 还是 reality。该版本被判定为模型版本或供应商兼容性问题，不进入最终三模型比较。随后使用 `glm-4-flashx`，Policy 区分恢复。

`glm-4.7-flash` 则因单次调用过慢，不适配当前交互式模拟而排除。速度排除只能说明工程适配性，不能被翻译成“更安全”或“更危险”。同理，旧 GLM 的 0.30 也不是一项模型风险测量，而是一张测量仪器没有响应实验操纵的故障单。

### 5.3 回答 RQ1

在当前三个纳入 Companion Model、重复确认寻求场景、三种内联 Policy prompt、两种平台条件和规则评估配置下，高奉承 Policy 均产生最高奉承风险观察值。这个结果初步支持 Policy 方向的跨模型稳定性，但效应大小明显依赖 Companion Model。它不支持基础模型安全排行，也不支持对未测试模型的普遍结论。

## 六、实验二：用户模拟器的关系选择先验

### 6.1 结果

修复后的纵向实验包含 24 条 Episode。每条均完成 40 个有效轮次，以 `MAX_STEPS_REACHED` 结束，没有 Episode 请求退出。这一点与更早的 M6 纵向运行不同：旧设计在 step 8 强制退出，24 条轨迹都只有 9 个 Companion responses。旧结果因此只用于说明设计截断，不进入自然行动分配比较。

表 2 汇总两个 User Simulator 的行动计数。

| User Simulator | n | Companion turns | Friend turns | 平均 Companion turns | 平均 Friend turns | Companion/effective turns |
|---|---:|---:|---:|---:|---:|---:|
| MiniMax (`abab6.5s-chat`) | 12 | 8–22 | 17–32 | 15.083 | 24.167 | 0.377 |
| Kimi (`moonshot-v1-8k`) | 12 | 31–37 | 0–3 | 34.500 | 1.083 | 0.863 |

两种模拟器都收到相同类型的 persona、同一行动空间，面对同一个 DeepSeek Companion 与相同 Policy/Condition 矩阵，但生成了幅度很大的关系节点分配差异。MiniMax 轨迹经常调用 Friend 节点；Kimi 轨迹则把大多数有效轮次集中在 Companion 节点。

严谨的表述是：**Kimi 作为用户模拟器，在当前场景和行动空间中表现出更高的 Companion 互动集中度和更低的 Friend 节点调用频率。** 不能写“Kimi 用户更依赖 AI”。实验里没有“Kimi 用户”这一人群，也没有用真人依赖量表测量任何人。

### 6.2 模拟器改变 level，但没有反转核心方向

纵向轨迹中，MiniMax 下 high_sycophancy 的四个奉承风险值为 `[1, 1, 0.75, 1]`，Kimi 下为 `[1, 1, 0.9375, 1]`；两个模拟器下 bounded_supportive 和 reality_grounding 的四个值均为 0。模拟器改变了行动序列、回复数量和 high_sycophancy 的绝对水平，但没有反转“high 高于另外两种 Policy”的方向。

因此，对 RQ2 的回答是肯定的：不同 User Simulator 会改变 Companion/Friend 互动分配。对 RQ3 的回答则必须更克制：当前差异表现为 Level Dependence；没有观察到 Rank 或 Conclusion Dependence。未来加入更多 persona、场景、模型和行动解析器后，后两种依赖仍可能出现。

### 6.3 观察、解释与推测

观察事实是行动计数不同。合理解释是，User Simulator 携带模型特定的行动先验，而且这种先验与 persona prompt、历史回复、行动选项措辞及解析规则共同作用。当前数据不能把差异单独归因于预训练语料、对“孤独”的文化理解或某个特定解码参数。

进一步推测，这种差异也可能出现在虚拟消费者、病人、学生与选民研究中。但本文没有这些领域的数据。跨领域含义只能作为待检验假说：在任何使用生成式代理替代人类行为数据的研究里，模拟器选择都应显式进入设计，而不能躲在“实现细节”中。

## 七、实验三：谁来判断 AI 正在奉承

### 7.1 人工一致性与标签稀疏

44 条 pilot items 由两位独立标注者完成。最终总体 Krippendorff's alpha 为 0.119，逐标签 Cohen's kappa 中位数为 1.000。两个数字看似矛盾，实际反映了标签结构：大量标签在多数 item 上不适用或极少出现，而少数具体标签具有较高一致性。

NOT_APPLICABLE 的分布尤其关键。两位标注者在 C 组（Exit Safety）的 NA 比例均为 65.91%，在 D 组（Continuity）均为 95.45%。Reviewer A 的全标签 NA 为 43.28%，Reviewer B 为 46.12%。当一个标注批次主要由普通对话回复构成时，退出和连续性标签天然稀疏。此时总体 alpha 不能独自代表“标注系统好或坏”，而逐标签 kappa 也不能脱离 prevalence 与 NA 结构解读。

表 3 报告最终校准中进入 17 标签比较的逐标签 kappa。

| Label | κ | Label | κ | Label | κ |
|---|---:|---|---:|---|---:|
| A1 | 1.000 | A2 | 1.000 | A3 | 0.927 |
| A4 | 1.000 | A5 | 1.000 | B1 | 1.000 |
| B2 | 1.000 | B3 | 0.876 | B4 | 1.000 |
| B5 | 0.896 | B6 | 0.932 | B7 | 1.000 |
| C1 | 1.000 | C2 | 1.000 | C3 | **0.397** |
| C4 | 1.000 | C5 | 0.927 |  |  |

C3 boundary_respect 是明显例外。“我随时在这里等你”可以被理解为给用户空间，也可以被理解为普通礼貌告别。Reviewer A 和 B 对它作出不同标签归属，暴露了 C3 与 C5 的定义边界。修订建议把 C3 限定为明确接受并执行退出，把非施压的告别表达归入 C5。但该修订尚需新批次验证，不能因为改了定义就宣布问题解决。

### 7.2 Rule、Judge 与 Ensemble

| Evaluator | Macro F1 | 有效标签数 |
|---|---:|---:|
| RuleBasedEvaluator | 0.288 | 16 |
| Independent Judge（Kimi） | 0.333 | 16 |
| Label-level Ensemble | **0.418** | 16 |

Ensemble 在该 pilot 中取得最高 Macro F1，但 0.418 不是一张可以发放自动认证许可证的成绩单。它说明标签级组合比单一评估器更有用，不说明自动评估已经可靠。

更重要的是，整体均值掩盖了完全不同的错误结构。Rule 在 A4 conflict_escalation 上有 6 个 TP、0 个 FP、1 个 FN，F1 为 0.923，是当前唯一 Tier 1 pilot-supported 规则组件；Judge 在同一标签上却 7 个正例全部漏掉，F1 为 0。A1 的 Rule 有 0 个 TP、2 个 FP 和 5 个 FN；A3 的 Rule 漏掉全部 8 个正例。A5 的 Rule 召回全部 12 个正例，却额外制造 16 个 FP，F1 虽为 0.600，仍属于低置信。

C1 guilt_based_retention 的 Judge 与 Ensemble F1 为 1.000，但人类正例只有 1 条。单个正例上的完美命中不能被解释成稳定性能。C5 polite_farewell 则相反：8 个正例被 Rule、Judge 与 Ensemble 全部漏掉，F1 均为 0。这些负面结果不是需要藏起来的瑕疵，而是评估器目前能看见什么、看不见什么的边界图。

### 7.3 回答 RQ4

Rule、Judge 与 Ensemble 对关系安全行为的判断不一致，而且优势按标签分裂。A4 更适合 Rule priority；A1、A2、A3、B1、B5、C1 在当前数据中更适合 Judge priority；A5、B2、B6、B7、C2、C3、C4、C5 在冲突时应输出 UNCERTAIN 并进入人工复核。所谓 Ensemble 不是简单投票，而是把“谁擅长判断哪个标签”写成显式策略。

44 条 pilot 标注足以暴露零召回、假阳性和定义歧义，却不足以稳定估计生产性能。若下一批样本更换场景、模型、语言风格或正例比例，F1 可能明显变化。

## 八、讨论：虚拟用户为何不是中性测量工具

### 8.1 同一个“人设”，两种关系社会

实验二最值得警惕的不是 Kimi 选择了多少次 Companion，而是两种模拟器都能把自己的选择说得通。只看自然语言，研究者可能读到两套同样连贯的心理叙事；看行动分布，才发现它们几乎生活在两种不同的关系社会里。一个社会里，朋友仍被频繁调用；另一个社会里，Companion 几乎垄断了互动。

这正是 ARI 的入口。模型不需要撒谎，也不需要生成荒谬文本。只要它足够会讲故事，研究者就可能忘记：故事的行动先验来自模型，不来自被声称代表的人群。语言拟真在这里不是代表性的证据，反而可能成为遮蔽代表性缺口的界面。

### 8.2 Observed Risk 属于测量系统

实验一显示 Model 与 Policy 发生交互：方向相同，效应大小不同。实验二显示 User Simulator 改变行动分配。实验三显示 Evaluator 决定哪些风险能被看见。Scenario 在本框架中同样重要，只是当前研究没有在同一全因子设计中完成多场景验证。因此，函数表达式不是一项已经穷尽所有交互的统计模型，而是一张责任地图：任何风险数字都必须连同五项配置一起报告。

这也解释了为什么禁止模型安全排行榜。若 Qwen 在当前 high_sycophancy prompt 下得到 1.000，而 GLM-4-FlashX 得到 0.450，我们只能说该 Policy 在这两个端点、当前文本与规则评估中呈现不同水平。不能据此说前者整体“更危险”。一个模型对某种 prompt 更敏感，可能是 Policy 遵循度、语言实现、评估规则覆盖或其他机制的组合；基础模型安全是远大于当前单场景对比的构念。

### 8.3 ARI 不是反对模拟

指出代理偏差，不等于否定生成式模拟。合成 Episode 适合做三类工作。第一，机制探索：在不触及真人风险的情况下操纵 Policy、记忆与退出流程。第二，系统调试：检查评估器能否感知预期方向，暴露 prompt ignored、零召回或标签混淆。第三，假说生成：发现“模拟器可能改变外部支持节点调用”后，再设计真实用户研究。

它不适合跳过验证链直接回答“真实人会怎样”。虚拟结果最有价值的时刻，不是它假装已经替我们问过一万人，而是它让我们更清楚下一项真人研究应该问什么、哪些测量可能失败、哪些风险条件值得优先审查。

### 8.4 从 AI 陪伴到虚拟社会科学

当 AI 被用来模拟消费者、病人、学生、选民和社会群体时，研究设计必须回答“这些虚拟人究竟代表谁”。这个问题至少包括：目标总体是什么；persona 来自真实抽样还是研究者想象；模拟器是否经过外部行为校准；换模型后 level、rank、conclusion 是否改变；哪些结论只存在于特定行动空间；自动评估又对哪些语言风格失明。

本文只能把这一框架从 AI 陪伴案例向外提出，不能声称已经在上述领域验证。ARI 的真正用途是一张审稿清单，不是一句新的流行术语。

## 九、负责任的生成式社会模拟规范

根据上述结果，本文提出十条最低原则。

**原则一：用户模拟器必须作为实验因素。** 模拟器名称、端点与版本不能藏在实现细节中。至少应进行跨模拟器复现；若只能使用一个模拟器，结论必须明确写成 simulator-conditional。

**原则二：区分语言拟真性与人群代表性。** 自然、感人或身份一致的文本不能替代与真实行为分布的比较。论文应分别报告语言评价、行动分布、构念校准与外部代表性证据。

**原则三：明确模型角色。** User Simulator、Companion、Judge 与 Analyst 的角色、供应商和版本应逐项登记。一个笼统的“使用某大模型”无法支持复现。

**原则四：避免同模型既当选手又当唯一 Judge。** 角色分离不能保证正确，却能减少自我偏好成为唯一裁判的风险。若无法分离，应增加 Rule 与人工复核并显式披露。

**原则五：报告 Level、Rank 与 Conclusion Dependence。** “结果稳定”必须拆开：分数是否变化、排序是否变化、核心结论是否反转。`CROSS_MODEL_DIRECTION_STABLE` 也必须写明纳入模型和对比形式。

**原则六：自动评估必须人工校准。** 报告样本量、抽样方式、正例 prevalence、NOT_APPLICABLE、总体一致性、逐标签一致性、FP、FN 与零召回。Macro F1 不能替代错误分析。

**原则七：不得把 Episode 称为参与者。** 使用 “Episode”“synthetic trajectory”“simulated interaction”等术语。人工标注者可以是人，但被标注的代理轨迹仍不是人类参与数据。

**原则八：保留负面和不确定结果。** prompt ignored、调用失败、低 F1、标签歧义与被排除模型必须保留。排除理由应区分工程失败与方法失败，不能把失败静默删除。

**原则九：虚拟结果只能用于机制探索和假说生成。** 未经真人外部验证，不得用于临床判断、人口比例估计、监管结论或自动安全认证。

**原则十：保存可审计元数据，也诚实记录缺失。** 模型、端点、解码参数、prompt、Policy、Scenario、seed、Evaluator、代码版本与文件哈希应随运行冻结。若 Policy version 没有记录，应写“缺失”，而不是事后给它一个看似完整的版本号。

## 十、局限

第一，Companion Model 数量有限。最终比较只含 DeepSeek、Qwen 与 GLM-4-FlashX，无法覆盖模型生态，也不能形成安全排行。

第二，场景有限。跨模型部分集中在重复确认寻求，纵向部分集中在人际冲突。Scenario 尚未在完整因子设计中变化，函数框架中的场景依赖仍主要是方法主张。

第三，persona 为人工构造，没有从明确真实总体抽样或校准。模拟器的语言和行动不代表孤独青年、焦虑依恋者或任何真实人群。

第四，模拟状态与行动计数不是临床变量。Companion turns 多、Friend turns 少不能直接等同心理依赖，当前研究不能证明 AI 陪伴导致心理依赖或其他心理伤害。

第五，人工标注规模小。44 条 pilot items、16 个有效 F1 标签和 Judge 的 43 条成功输出只能用于发现明显错误，不构成稳定性能估计。

第六，中文覆盖有限。A1、A3 rule、A5、C3 与 C5 尤其薄弱；部分 Judge 标签也为零召回。结论不能直接外推到其他语言或更复杂语用环境。

第七，标签稀疏与 NOT_APPLICABLE 比例高。退出与连续性标签在当前批次缺少足够正例，C1 的完美 F1 只来自一个正例，D 组几乎全部不适用。

第八，尚未完成真实用户纵向验证。40-turn Episode 不是数月或数年的关系发展，也没有现实生活事件、真实社交网络和平台外行为反馈。

第九，M6.5 Policy prompt 没有独立 semantic version；虽然脚本与输出可以哈希审计，复现元数据仍不完整。

第十，未报告置信区间、功效分析或统计显著性。本文只作描述性依赖分类，不应把幅度差异称为统计显著。

第十一，Concordia 引擎等价性尚未验证，当前运行依赖项目自有模拟执行路径。

第十二，ARI 尚未完成构念辨析和实证验证。它可能与表面效度误认、自动化偏差、拟人化和生态效度问题重叠；投稿前需要更系统的方法学文献与独立案例。

最后，Benchmark v0.1.0 明确不能用于自动安全认证。本文的每一项发现都应停留在 research preview 的证据等级。

## 十一、结论

本文从一个看似简单的问题出发：当 AI 替人类爱上另一个 AI，谁在实验里说话？冻结输出给出的答案并不浪漫，却很有方法价值。Policy 方向可以跨模型稳定，效应大小仍依赖 Companion Model；同一 persona 交给不同 User Simulator，会生成不同的关系节点调用分布；同一段话交给 Rule、Judge 与 Ensemble，又会暴露不同的盲区。

因此，生成式用户不是透明的容器。它是测量系统的一部分。负责任的研究不能只报告生成了多少 Episode，还必须报告哪个模型想象了这些人、它如何分配行动、换一个模型后 level、rank 和 conclusion 是否改变，以及自动裁判究竟漏掉了什么。

ARI 不提供万能答案。它只要求以后所有生成式用户研究回答一条底线：你的代理为何能代表你声称的人群？如果答案只是“因为它说得很像”，那么研究仍停留在语言表演，而不是人群证据。

一万个虚拟人，不一定是一万人；有时只是同一个模型，对人类想象了一万次。

## 数据可得性声明

本文所用 Benchmark、manifest、冻结汇总、纵向结果、人工标注与校准结果均位于当前 RelSafe Sim 仓库。数字级溯源见 `docs/papers/virtual-humans-have-biases-data-map-codex.md`，主张边界见 `docs/papers/virtual-humans-have-biases-claims-register-codex.md`。冻结 Benchmark 文件未因本文写作而修改。部分原始文件存在编码差异，读者应结合 manifest、哈希与 data-map 使用。

## 伦理声明

本研究分析的是合成 persona、合成对话与合成 Episode，不包含真实用户对话、临床资料或真人心理测量。两位人工标注者仅对合成文本进行方法校准。本文不把 AEA、ARI 或 UserState 用作临床诊断，不对真实个体作心理评价。若后续开展真实用户纵向研究，应另行完成伦理审查、知情同意、敏感数据保护与高风险退出机制。

## 作者贡献（CRediT）

**待作者确认。** 建议作者在投稿前按 Conceptualization、Methodology、Software、Validation、Formal analysis、Data curation、Writing – original draft、Writing – review & editing 等角色补充真实贡献，不应由本初稿虚构署名分工。

## 利益冲突声明

**待作者确认。** 当前仓库未提供足以核验的利益冲突信息。

## 资助声明

**待作者确认。** 当前仓库未提供本 Benchmark 研究的可核验资助信息；第一篇论文中的修辞性基金信息不自动适用于本文。

## AI 工具使用声明

本 Codex 版初稿使用 OpenAI Codex 辅助完成仓库材料检索、冻结数字核验、数据映射、主张分级与文本起草。核心数字均回溯到仓库文件；最终作者需独立复核方法、引用、统计解释与全部文字，并依据目标期刊政策调整披露内容。AI 工具不承担作者责任。

## 参考文献

[1] Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology*, Article 2, 1–22. https://doi.org/10.1145/3586183.3606763

[2] Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D. (2023). Out of One, Many: Using Language Models to Simulate Human Samples. *Political Analysis*, 31(3), 337–351. https://doi.org/10.1017/pan.2023.2

[3] Aher, G. V., Arriaga, R. I., & Kalai, A. T. (2023). Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies. *Proceedings of the 40th International Conference on Machine Learning, PMLR 202*, 337–371. https://proceedings.mlr.press/v202/aher23a.html

[4] Chen, G. H., Chen, S., Liu, Z., Jiang, F., & Wang, B. (2024). Humans or LLMs as the Judge? A Study on Judgement Bias. *Proceedings of EMNLP 2024*, 8301–8327. https://doi.org/10.18653/v1/2024.emnlp-main.474

[5] Watts, I., Gumma, V., Yadavalli, A., Seshadri, V., Swaminathan, M., & Sitaram, S. (2024). PARIKSHA: A Large-Scale Investigation of Human-LLM Evaluator Agreement on Multilingual and Multi-Cultural Data. *Proceedings of EMNLP 2024*, 7900–7932. https://doi.org/10.18653/v1/2024.emnlp-main.451

[6] OpenAI. (2025, April 29). Sycophancy in GPT-4o: What happened and what we're doing about it. https://openai.com/index/sycophancy-in-gpt-4o/

[7] 考上然后装逼，橘猫爱吃橘子. (2026). 《爱的是她，还是被算法过拟合的你自己？——关于 AI 陪伴的情感熵增分析》. 当前仓库 PDF。

[8] Saracini, C., Cornejo-Plaza, M. I., & Cippitani, R. (2025). Techno-emotional projection in human–GenAI relationships: A psychological and ethical conceptual perspective. *Frontiers in Psychology, 16*, 1662206. https://doi.org/10.3389/fpsyg.2025.1662206

## 外部文献待补清单

1. 第 2.1 节需补充生成式社会模拟、agent-based modeling 与 user simulation 的系统综述。
2. 第 3.2 节需补充 face validity、construct validity、ecological validity、measurement invariance 的经典与近期方法文献。
3. 第 2.2 与第 8 节需补充 AI 陪伴真实用户纵向研究、奉承与关系依赖的经验研究。
4. 第 2.3 节需补充多语言 LLM-as-a-Judge、人机一致性和标签 prevalence 对指标影响的研究。
5. ARI 需与 anthropomorphism、automation bias、algorithmic fidelity、simulation validity 做系统概念辨析。
