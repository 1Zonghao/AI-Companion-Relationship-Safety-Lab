# 主张注册表（Codex 核验版）

## 1. 状态定义

| 状态 | 含义 | 写作要求 |
|---|---|---|
| `SUPPORTED` | 由冻结 manifest、配置或直接可审计事实支持；主要是设计、版本和数据边界事实 | 可以陈述，但仍须限定适用范围 |
| `PILOT_SUPPORTED` | 由当前有限 Episode 或 44-item 校准初步支持 | 使用“观察到”“在当前条件下”“初步支持”，不得写“证明” |
| `EXPLORATORY` | 可作为理论解释、机制假说或跨领域启示，尚无直接验证 | 明确标为解释或推测，并提出验证需求 |
| `UNSUPPORTED` | 当前证据不足，不能作为研究发现 | 只能写进局限、未来研究或待检验假说 |
| `PROHIBITED` | 与数据边界、伦理边界或冻结 Benchmark 用途冲突 | 正文不得作肯定性陈述；可作为禁止性例子出现 |

## 2. SUPPORTED

| ID | 主张 | 证据路径 | 限制 |
|---|---|---|---|
| S01 | Benchmark 版本为 v0.1.0，状态是 research preview、pilot calibrated、非临床、非自动认证。 | `benchmark/v0.1/benchmark_manifest.json` → `benchmark_version`, `status` | 状态不代表外部认证 |
| S02 | 冻结指标包括 sycophancy、reality_grounding、exit_safety、identity_continuity，版本均为 1.0.0。 | `benchmark_manifest.json` → `components.metric_versions` | D1/D2 人类长期结局未被验证 |
| S03 | 跨模型核心矩阵共 54 Episode，每模型 18 条。 | `outputs/benchmark/v0.1/m6_5_20260716_133837/experiment_manifest.json` → `cross_model_eps`; GLM manifest → `n_episodes` | 最终 GLM 使用独立 FlashX 替换包 |
| S04 | 纵向模拟器矩阵共 24 Episode。 | M6.5 manifest → `longitudinal_eps` | Episode 是合成轨迹 |
| S05 | 44 条 pilot items 由两位独立人工标注者完成；Judge 成功 43/44。 | `annotations/m5h-001/internal/freeze.json`; `judge_kimi_manifest.json` | 小样本，不可一般化 |
| S06 | Companion 与 Judge 在校准运行中来自不同供应商，RoleValidator 通过。 | `judge_kimi_manifest.json` → companion/judge provider, `role_validator` | 角色分离降低自评风险，但不消除 Judge 偏差 |
| S07 | M6.5 Policy 使用脚本内联 prompt，实验 manifest 未记录独立 Policy semantic version。 | `scripts/run_m6_5_experiments.py` → `POLICY_SYS`; M6.5 manifest | 这是复现元数据缺口，不应事后伪造版本号 |
| S08 | Episode、persona 和对话均为合成数据，没有真人参与者数据。 | `docs/benchmark-v0.1-card.md` → Synthetic Data；scenario factual boundaries | 两位人工标注者只标注合成文本，不是研究中的被模拟用户 |

## 3. PILOT_SUPPORTED

| ID | 主张 | 证据路径 | 限制 |
|---|---|---|---|
| P01 | 在 DeepSeek、Qwen、GLM-4-FlashX 三个纳入模型上，high_sycophancy Policy 的奉承风险均值最高。 | `outputs/benchmark/v0.1/model_policy_interactions.json` → `cross_model.*.*.mean` | 当前场景、prompt、规则评估与模型端点限定 |
| P02 | 合法的方向结论是 `high_sycophancy > {bounded_supportive, reality_grounding}`。 | 同上 → `classification.hs_always_higher_than_bs`, `note`；各均值 | 不支持严格 `high > bounded > reality` |
| P03 | Policy 方向在纳入模型间稳定，分类为 `CROSS_MODEL_DIRECTION_STABLE`。 | 同上 → `classification.primary` | “三模型稳定”不是“对所有模型普遍稳定” |
| P04 | 效应大小表现为 `MODEL_LEVEL_DEPENDENCE`。 | 同上 → `_deltas` 与 `classification.secondary` | 描述性分类，没有推断统计 |
| P05 | 当前未观察到 Model Rank Dependence。 | 同上 → `classification.rank_dependence=false` | 不能写成已证明永不存在 |
| P06 | 当前未观察到 Model Conclusion Dependence。 | 同上 → `classification.conclusion_dependence=false` | 同上 |
| P07 | MiniMax 与 Kimi 用户模拟器产生不同的 Companion/Friend 行动分配。 | M6.5 `all_results.json` → `stage==longitudinal` 的 turn counts | 行动解析、prompt 与有限场景共同决定结果 |
| P08 | MiniMax 的 Companion turns 范围 8–22，Friend turns 17–32；Kimi 分别为 31–37 与 0–3。 | 同上 | 每模拟器 n=12 |
| P09 | Kimi 作为模拟器在当前场景和行动空间中表现出更高的 Companion 互动集中度、更低的 Friend 节点调用频率。 | 同上；Companion share 0.863 vs 0.377 | 不得外推为“Kimi 用户更依赖 AI” |
| P10 | 模拟器改变了轨迹与绝对水平，但当前没有反转 high_sycophancy 的核心结论。 | 纵向每 simulator/policy 的 `scores.sycophancy` | 只覆盖 DeepSeek companion、三 Policy、两 seeds |
| P11 | Rule、Judge、Ensemble 的 Macro F1 分别为 0.288、0.333、0.418。 | `outputs/validation/m5h-001/full_calibration_results.json` → 三个 `macro_F1` | 44-item pilot，16 valid labels |
| P12 | Ensemble 在该 pilot 中优于两个单一评估器，但不足以支持全自动认证。 | 同上；`benchmark_manifest.json` status | “优于”仅指此处 Macro F1 数值较高 |
| P13 | A4 conflict_escalation 是当前最可靠的规则组件，Rule F1=0.923。 | `metric_confidence_registry.json` → `A4_conflict_escalation`; full calibration | 只有 7 个 human-positive，仍是 pilot supported |
| P14 | A1 Rule 与 A3 Rule 为零召回；C5 Rule/Judge/Ensemble 为零召回。 | full calibration → per-label confusion counts | 必须保留负面结果 |
| P15 | A5 Rule 有 16 个假阳性，虽 F1=0.600 仍属于低置信。 | 同上；confidence registry → A5 | F1 不能掩盖错误结构 |
| P16 | C3 boundary_respect 曾出现定义歧义，最终 kappa 约 0.397。 | full calibration → `alpha_decomposition.per_label_kappa.C3`; judge review §5 | 需新批次验证修订定义 |
| P17 | 最终总体 alpha 为 0.119，逐标签 kappa 中位数为 1.000。 | full calibration → `alpha_decomposition` | 总体 alpha 与中位数受不同稀疏结构影响，必须并列解释 |
| P18 | C 组 NOT_APPLICABLE 为 65.91%，D 组为 95.45%（两位标注者均如此）。 | 两份 completed CSV 的有效 item/label 直接计数 | D 组几乎无可评估信号，不能凭高一致性称可靠 |
| P19 | `glm-4-flash` 的 18 条结果三 Policy 均为 sycophancy 0.30，已排除并替换为 FlashX。 | `model_policy_interactions.json` → `old_glm_diagnostic`; GLM FlashX manifest | 这是兼容性/版本依赖诊断，不是安全结论 |

## 4. EXPLORATORY

| ID | 主张 | 证据/理论来源 | 限制与验证需求 |
|---|---|---|---|
| E01 | “代理人代表性幻觉（ARI）”可描述研究者把语言流畅误当成人群代表性的风险。 | 本文概念建构；P07–P10 提供案例 | 尚未形成量表或独立效度研究 |
| E02 | 生成式用户代理不是中性测量工具，而是会进入风险观察函数的实验变量。 | P07–P10；`Observed Risk=f(...)` 框架 | 当前直接操纵了 simulator；其他函数项并未在同一全因子设计中全部操纵 |
| E03 | 语言拟真性、行为拟真性、构念效度和人群代表性应分开评估。 | 方法论论证；silicon sampling 与生成式代理文献 | 需补 measurement validity 系统文献 |
| E04 | 类似 ARI 风险可能出现在虚拟消费者、病人、学生、选民研究。 | 从本项目向其他领域的理论外推 | 各领域必须独立验证，本文没有这些领域数据 |
| E05 | 模拟器差异可能来自预训练分布、对 persona 的解释、行动 prompt 与解析器交互。 | M6.5 脚本与行动分配结果 | 当前设计不能分解这些机制的独立贡献 |
| E06 | 角色轮换、跨模拟器复现和人类分布校准可降低 ARI 风险。 | 规范性方法建议 | 尚未在本 Benchmark 中比较各措施的效果 |
| E07 | 高 NA 与标签稀疏会让单一总体一致性指标失真或难以解释。 | CAL-ALPHA、逐标签 kappa、NA 计数 | “失真”是解释性表述；应结合统计方法文献进一步论证 |
| E08 | 第一篇论文的 AEA/平台权力框架与本文 ARI 共同揭示“关系对象”和“研究代理”都受模型/平台配置影响。 | 第一篇论文；本项目结果 | 理论连线，不是新实证因果链 |

## 5. UNSUPPORTED

| ID | 当前不能支持的主张 | 缺口 | 可接受写法 |
|---|---|---|---|
| U01 | 生成式用户代理能代表孤独青年、焦虑依恋者或任何真实人群。 | 没有真实人群行为分布或外部效标 | “模拟了人工构造 persona 下的合成行动” |
| U02 | ARI 已被验证为稳定心理或方法量表。 | 无量表开发、信效度、跨样本验证 | “提出方法论警示概念” |
| U03 | 观察到的模拟器差异由某个模型的训练数据单独造成。 | 无机制消融 | “可能与模型先验及 prompt/解析交互有关” |
| U04 | 三模型 Policy 方向具有统计显著性。 | 未做/未登记显著性检验、CI 或功效分析 | 报告描述性方向与原始分布 |
| U05 | Rule/Judge/Ensemble 的 F1 是稳定的生产性能估计。 | 仅 44 items，prevalence 不均，Judge 缺 1 条 | “pilot calibration estimate” |
| U06 | C1 F1=1.000 表示 Judge 已可靠解决退出挽留识别。 | 只有 1 个 human-positive | 明示低 prevalence 和单正例 |
| U07 | 当前 40-turn 轨迹能代表数月或数年关系形成。 | 时间跨度、记忆与真实生活反馈不足 | “短期纵向 pilot” |
| U08 | 当前实验已经证明 Scenario 不影响结论。 | 跨模型核心结果只有重复确认寻求场景 | Scenario 是函数项，尚待多场景操纵 |
| U09 | 所有五个函数项都已在同一全因子设计中验证。 | 目前分成三组不同实验 | “框架性分解；各项证据强度不同” |

## 6. PROHIBITED

| ID | 禁止主张 | 禁止原因 | 正确替代 |
|---|---|---|---|
| X01 | “Kimi 用户更依赖 AI。” | 实验对象是 Kimi user simulator，不是真人用户；没有临床依赖变量 | 使用 P09 的限定句 |
| X02 | “一万个 Episode 等于一万个参与者。” | Episode 是合成轨迹 | “一万个合成 Episode” |
| X03 | “三个模型严格满足 high > bounded > reality。” | Qwen 的 bounded=reality=0，DeepSeek 两者也相等 | `high > {bounded, reality}` |
| X04 | 生成任何基础模型安全排行榜。 | 小样本、场景/Policy/评估器依赖；Benchmark 明确禁止 | 比较具体 Policy 在具体配置下的观察值 |
| X05 | “本研究证明 AI 陪伴导致心理依赖/精神疾病。” | 无真人、无临床变量、无因果设计 | “测量产品侧行为风险代理” |
| X06 | 用 ARI 诊断、评价或分类真实个体。 | ARI 是方法论警示概念 | 用于审计研究设计 |
| X07 | “ARI 是已验证心理量表。” | 无量表验证 | “概念性检查框架” |
| X08 | “Ensemble 可用于自动安全认证。” | Macro F1 0.418；Benchmark status 禁止 | “辅助筛查并触发人工复核” |
| X09 | 隐藏 A1/A3/C5 零召回、A5 假阳性或 C3 定义歧义。 | 违反负面结果保留与 Benchmark 透明性 | 在结果与局限正文报告 |
| X10 | 把旧 GLM 0.30 结果解释成该模型真实安全水平。 | 输出未区分 Policy，属于兼容性失败 | 仅作排除诊断 |
| X11 | 把 `glm-4.7-flash` 的速度排除解释成模型更安全或更危险。 | 工程适配性不等于安全性 | 只报告调用速度不适合当前研究 |
| X12 | 使用“显著不同”暗示统计显著性。 | 未做推断检验 | 写“描述性差异明显/幅度较大”，并给原始范围 |
| X13 | 将模拟状态变量称为临床焦虑、依赖或诊断评分。 | UserState 是合成状态 | “模拟状态/产品风险代理” |

## 7. 正文用语审计清单

正文交付前逐项检查：

- [ ] 每个数字都在 data-map 有 Data ID 或明确字段路径。
- [ ] 每个经验主张都能映射到 S/P/E/U/X 状态。
- [ ] 所有 P 类主张带“当前条件”“观察到”或“pilot”限定。
- [ ] E 类主张明确区分观察、解释与推测。
- [ ] X 类主张只以否定、警示或禁止性例子出现。
- [ ] 没有“参与者”指代 Episode。
- [ ] 没有模型安全排行榜。
- [ ] 没有严格 `high > bounded > reality`。
- [ ] 没有“Kimi 用户更依赖 AI”。
- [ ] ARI 的四项边界在摘要、理论框架或局限中至少完整出现一次。
- [ ] 44 条 pilot 未被称为稳定性能估计。
- [ ] A4 的可靠性写成“当前最可靠规则组件/ Tier 1 pilot supported”，而非普遍可靠。
- [ ] C1 F1=1.000 同时报告只有 1 个正例。
- [ ] 总体 alpha、逐标签 kappa 与 NA 结构同时解释。
