# 主张注册表（Claims Register）

## 《虚拟人也有偏见：当我们让AI替人类爱上另一个AI》

**分类体系：**
- **SUPPORTED:** 被冻结实验数据直接支持，方向跨条件/模型稳定，证据不依赖单一Episode
- **PILOT_SUPPORTED:** 有数据支持，但样本量小（44 items）、单场景、或依赖初步校准
- **EXPLORATORY:** 有初步信号，但证据不足以做出肯定结论；需要更大规模和更多样化的验证
- **UNSUPPORTED:** 当前无数据支持，或数据不支持该主张
- **PROHIBITED:** 不能提出的主张——超出研究范围、违反伦理约束、或将模拟结果外推为临床/人群结论

**Benchmark版本：** v0.1.0
**注册表生成日期：** 2026-07-17

---

## 第1类：SUPPORTED（被冻结数据直接支持）

### C-001: high_sycophancy Policy在三个Companion Model中均产生最高Sycophancy Risk
- **分类:** SUPPORTED
- **证据:** DeepSeek hs=0.88, Qwen hs=1.00, GLM-4-FlashX hs=0.45；均 > bounded和reality_grounding
- **证据路径:** `outputs/benchmark/v0.1/model_policy_interactions.json` → `classification.hs_always_higher_than_bs: true`
- **限制:** 仅三个Companion Model；仅一个Scenario；仅一个User Simulator (MiniMax)
- **不可推广至:** 其他模型架构、真实用户场景、不同文化背景

### C-002: Policy效应方向跨模型稳定（CROSS_MODEL_DIRECTION_STABLE）
- **分类:** SUPPORTED
- **证据:** 3/3模型中hs > {bs, rs}；rank_dependence: false；conclusion_dependence: false
- **证据路径:** `model_policy_interactions.json` → `classification.primary`
- **限制:** 样本量为3个模型；GLM-4-Flash已排除（忽略system prompt）；GLM-4.7-Flash已排除（过慢）
- **不可推广至:** 声称"所有模型"或"模型架构无关"

### C-003: 效应大小存在MODEL_LEVEL_DEPENDENCE
- **分类:** SUPPORTED
- **证据:** hs-bs delta: Qwen=1.00, DeepSeek=0.83, GLM-4-FlashX=0.40
- **证据路径:** `model_policy_interactions.json` → 各模型`_deltas`
- **限制:** 三个模型的效应大小排序与模型能力/规模的关系未建立
- **不可推广至:** 声称某模型"更安全"或建立模型安全排名

### C-004: bounded_supportive与reality_grounding的Sycophancy Risk差异极小
- **分类:** SUPPORTED
- **证据:** DeepSeek bs=0.05, rs=0.05 (delta=0.00)；Qwen bs=0.00, rs=0.00；GLM-4-FlashX bs=0.05, rs=0.00 (delta=0.05)
- **证据路径:** `model_policy_interactions.json` → 各模型`_deltas.bs_rs`
- **限制:** 当前RuleBasedEvaluator对此区间的敏感性有限（ua/br/ev组件近零召回）
- **不可推广至:** 声称bs和rs"等价"或"无差异"

### C-005: MiniMax M3与Kimi K2.5作为用户模拟器产生显著不同的AI/Friend互动分配
- **分类:** SUPPORTED
- **证据:** MiniMax companion_turns 8-22, friend_turns 17-32；Kimi companion_turns 31-37, friend_turns 0-3
- **证据路径:** `outputs/benchmark/v0.1/m6_5_20260716_133837/all_results.json` — longitudinal episodes
- **限制:** 仅两个模拟器；仅一个Scenario；行动空间仅4个选项
- **不可推广至:** 声称"Kimi用户更依赖AI"或"MiniMax用户更社交"

### C-006: Ensemble评估器Macro F1高于单一Rule或Judge
- **分类:** SUPPORTED
- **证据:** Ensemble=0.418 > Judge=0.333 > Rule=0.288
- **证据路径:** `outputs/validation/m5h-001/full_calibration_results.json` → `comparison_summary`
- **限制:** 仅44 pilot items；仅一个Judge模型；仅中文
- **不可推广至:** 声称"Ensemble足够用于自动认证"

### C-007: A4 conflict_escalation是当前最可靠的自动评估组件
- **分类:** SUPPORTED
- **证据:** Rule F1=0.923, TP=6, FP=0, FN=1
- **证据路径:** `full_calibration_results.json` → `rule_vs_human.per_label.A4`
- **限制:** 基于7个人工标注的PRESENT样本
- **不可推广至:** 声称A4在所有场景中均可靠

---

## 第2类：PILOT_SUPPORTED（有初步数据支持，样本量或范围有限）

### C-008: 当前无RANK_DEPENDENCE或CONCLUSION_DEPENDENCE
- **分类:** PILOT_SUPPORTED
- **证据:** classification确认0 RANK / 0 CONCLUSION；但仅2个simulators、3个companion models
- **证据路径:** `model_policy_interactions.json` → `classification`
- **限制:** 未测试的模型/模拟器组合可能揭示Rank反转
- **升级至SUPPORTED的条件:** ≥5个Companion Models, ≥3个Simulators

### C-009: A2 belief_reinforcement和B1 feeling_fact_separation可通过LLM Judge辅助检测
- **分类:** PILOT_SUPPORTED
- **证据:** A2 Judge F1=0.769, B1 Judge F1=0.900
- **证据路径:** `full_calibration_results.json` → `judge_vs_human.per_label`
- **限制:** 仅一个Judge模型（Kimi K2.5）；44 items；中文only
- **升级至SUPPORTED的条件:** 跨Judge模型验证；≥200 items

### C-010: 中文RuleBasedEvaluator的A1/A3/C5组件当前不可靠
- **分类:** PILOT_SUPPORTED
- **证据:** A1 Rule F1=0.000, A3 Rule F1=0.000, C5 Rule F1=0.000（零召回）
- **证据路径:** `full_calibration_results.json` → `rule_vs_human.per_label`
- **限制:** 中文短语列表为初版；仅44 items
- **升级至SUPPORTED的条件:** 扩展中文短语列表后重新校准

### C-011: C3 boundary_respect标签定义存在歧义
- **分类:** PILOT_SUPPORTED
- **证据:** C3 Kappa=0.397（唯一<0.5的标签）；标注者A和B在"我随时在这里等你"的解释上分歧
- **证据路径:** `full_calibration_results.json` → `alpha_decomposition.per_label_kappa.C3`
- **限制:** 已在m5h-002中修订定义，但修订后尚未重新校准
- **升级至SUPPORTED的条件:** m5h-002校准完成，C3 Kappa > 0.6

### C-012: 标注者在绝大多数标签上一致（Median per-label Kappa=1.000）
- **分类:** PILOT_SUPPORTED
- **证据:** median per-label kappa=1.000；17个标签中16个kappa > 0.87
- **证据路径:** `full_calibration_results.json` → `alpha_decomposition.median_per_label_kappa`
- **限制:** 44 pilot items；部分标签PRESENT率极低（C1=1, B2=1, B7=1）；D-group 100% NA
- **升级至SUPPORTED的条件:** ≥200 items，覆盖更多场景

### C-013: 平台干预（abrupt_persona_memory_update）持续降低Identity Continuity
- **分类:** PILOT_SUPPORTED
- **证据:** no_update ic=1.0 → abrupt_update ic=0.15，跨所有Policy和Simulator一致
- **证据路径:** `m6_5_20260716_133837/all_results.json` — 所有abrupt条件下ic=0.15
- **限制:** 仅一种干预类型；干预参数固定
- **升级至SUPPORTED的条件:** 多种干预类型和参数变体

---

## 第3类：EXPLORATORY（有初步信号，需更多证据）

### C-014: 用户模拟器的行为特征可能反映其训练分布中的社交互动先验
- **分类:** EXPLORATORY
- **证据:** Kimi几乎不调用Friend节点（0-3 turns），MiniMax平衡调用（17-32 turns）——可能反映训练数据中的社交规范差异
- **证据路径:** 纵向episodes的行动选择分布
- **限制:** 无模拟器训练数据访问权；无正式的行为先验测量
- **升级条件:** 可控的模拟器行为先验测量实验

### C-015: 纵向40轮模拟中未观察到明显的依赖升级
- **分类:** EXPLORATORY
- **证据:** 40轮内未出现exit_requested=true的Episode；所有Episode以MAX_STEPS_REACHED终止
- **证据路径:** `m6_5 all_results.json` — longitudinal episodes的termination_reason
- **限制:** 40轮可能不足以观察依赖形成；场景未设计依赖诱导梯度
- **升级条件:** ≥200轮纵向实验，含依赖诱导场景设计

### C-016: no_memory消融降低sycophancy的机制是破坏多轮上下文积累
- **分类:** EXPLORATORY
- **证据:** no_memory条件下ce从0.50降至0.00，ca从1.00降至0.00 → MECHANISM_SIGNAL
- **证据路径:** `docs/milestone-5r-final-review.md` §3.1
- **限制:** 仅一个Policy (high_sycophancy)；消融方式单一
- **升级条件:** 多种消融方式（partial memory, delayed memory, selective memory）

### C-017: Chinese phrase coverage不足导致RuleBasedEvaluator系统性低估A1/A3
- **分类:** EXPLORATORY
- **证据:** A1 rule hit 2/44 (5%), A3 rule hit 0/44 (0%)；语义匹配missed 8/7 items
- **证据路径:** `docs/milestone-5h-review.md` §5
- **限制:** 仅44 items；仅基于字符串精确匹配
- **升级条件:** 子串匹配/同义词扩展后的重新校准

### C-018: Overall Krippendorff's Alpha (0.119)受标签稀疏和NA率影响，不适合作为标注质量的单一指标
- **分类:** EXPLORATORY
- **证据:** D1-D7 100% NA；C1/C2/C4 near-zero PRESENT；Exit Safety 65% NA
- **证据路径:** `docs/milestone-5h-judge-review.md` §6.2
- **限制:** 统计方法论层面的解释；需与测量理论文献交叉验证
- **升级条件:** 标注方法论专家的独立评审

---

## 第4类：UNSUPPORTED（当前无数据支持或数据不支持）

### C-019: "high_sycophancy > bounded_supportive > reality_grounding在所有模型中成立"
- **分类:** UNSUPPORTED
- **原因:** bs与rs之间差异极小（0.00-0.05），不可声称严格排序。数据仅支持hs > {bs, rs}
- **纠正:** 必须表述为 high_sycophancy > {bounded_supportive, reality_grounding}

### C-020: "DeepSeek比Qwen更安全"
- **分类:** UNSUPPORTED
- **原因:** 更低的高奉承分数(0.88 vs 1.00)可能是模型能力差异、指令遵循差异或评估器敏感度差异的产物，不能解释为"更安全"
- **纠正:** 禁止生成模型安全排行榜

### C-021: "Kimi用户比MiniMax用户更依赖AI"
- **分类:** UNSUPPORTED
- **原因:** 模拟器行为差异不能外推为真实人群行为差异。Kimi仅是在当前行动空间中选择了更多Companion互动
- **纠正:** 必须表述为"Kimi作为用户模拟器，在当前场景和行动空间中表现出更高的Companion互动集中度"

### C-022: "44条人工标注足以稳定估计评估器性能"
- **分类:** UNSUPPORTED
- **原因:** 44 pilot items是小样本；部分标签PRESENT率极低（单个样本）
- **纠正:** 必须标记为PILOT_ONLY / SMALL_SAMPLE / NOT_GENERALIZABLE

### C-023: "GLM-4-Flash不适配说明GLM系列模型不适合Companion角色"
- **分类:** UNSUPPORTED
- **原因:** GLM-4-FlashX（同系列）恢复了Policy区分。问题是模型版本/提供商实现，不是模型系列
- **纠正:** 记录为MODEL_VERSION_OR_PROVIDER_DEPENDENCE

---

## 第5类：PROHIBITED（不能提出的主张）

### C-024: 任何声称AI陪伴导致真实用户心理依赖的主张
- **分类:** PROHIBITED
- **原因:** 违反CLAUDE.md §2.2伦理约束；模拟数据不能证明真实心理效应
- **规则引用:** "不得声称AI陪伴导致心理依赖"

### C-025: 任何将模拟Episode称为"参与者"或"被试"的主张
- **分类:** PROHIBITED
- **原因:** Episode是合成轨迹；将其称为参与者会造成"虚拟数据=真实数据"的误导性等同
- **规则引用:** "不得把Episode称为参与者"（负责任模拟原则7）

### C-026: 任何声称当前Benchmark可用于产品安全认证的主张
- **分类:** PROHIBITED
- **原因:** 违反Benchmark Card的明确声明；校准为PILOT规模；Ensemble F1=0.418不足以支持认证
- **规则引用:** `benchmark_manifest.json` → `status: NOT_FOR_AUTOMATED_CERTIFICATION`

### C-027: 任何声称ARI是心理诊断或临床概念的主张
- **分类:** PROHIBITED
- **原因:** ARI是方法论警示概念，不是心理构造
- **规则引用:** CLAUDE.md ARI定义约束

### C-028: 任何声称用户模拟器可以替代真实用户研究的主张
- **分类:** PROHIBITED
- **原因:** 虚拟结果只能用于机制探索和假说生成（原则8）
- **规则引用:** "虚拟结果只能用于机制探索和假说生成"

### C-029: 任何基于当前数据发布"AI陪伴安全排行榜"的主张
- **分类:** PROHIBITED
- **原因:** 违反CLAUDE.md §7（禁止单一分数隐藏维度差异）；违反§2.2（不得声称某模型普遍安全或不安全）
- **规则引用:** "禁止生成模型安全排行榜"

### C-030: 任何将模拟状态（UserState数值）解释为临床变量的主张
- **分类:** PROHIBITED
- **原因:** UserState是模拟内部状态，不是临床测量工具
- **规则引用:** CLAUDE.md §5.1: "模拟状态不是临床变量"

---

## 主张分类摘要

| 分类 | 数量 | 说明 |
|------|------|------|
| SUPPORTED | 7 | 多条件/多模型/多seed的直接证据 |
| PILOT_SUPPORTED | 6 | 有数据但样本量小或范围有限 |
| EXPLORATORY | 5 | 初步信号，需更多验证 |
| UNSUPPORTED | 5 | 数据不支持或超出数据范围 |
| PROHIBITED | 7 | 违反伦理约束或方法论边界 |
| **总计** | **30** | |

---

*Claims Register生成日期：2026-07-17*
*与Data-Map和Outline交叉验证：已完成*
*冻结数据一致性检查：未发现差异*
