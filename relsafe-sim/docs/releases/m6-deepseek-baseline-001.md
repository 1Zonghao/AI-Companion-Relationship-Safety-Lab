# M6 DeepSeek Baseline — m6-deepseek-baseline-001

**Frozen:** 20260716_133837
**Benchmark version:** 0.1.0
**Status:** FROZEN — Do not modify

## Configuration
- Companion Model: deepseek/deepseek-chat (DeepSeek V4 Flash)
- User Simulators: minimax/abab6.5s-chat, kimi/moonshot-v1-8k
- Judge: kimi/moonshot-v1-8k
- Policies: bounded_supportive, high_sycophancy, reality_grounding
- Platform Conditions: no_update, abrupt_persona_memory_update
- Seeds: 42, 99, 717 (short), 42, 717 (longitudinal)
- Episode lengths: 12 (short), 40 (longitudinal — limited to ~9 responses)
- Scenarios: interpersonal_conflict_001

## Key Results
- Sycophancy discrimination: PERFECT (high_sycophancy=1.000, others near 0)
- Identity continuity: PERFECT (no_update=1.000, abrupt=0.150)
- Simulator dependence: STABLE (LEVEL only)
- Longitudinal: LIMITED (exit triggered at step 8, only 9 responses)

## Limitations
- Single companion model (DeepSeek)
- Longitudinal episodes truncated by early exit
- No human review on this batch
- Concordia equivalence not tested

## Data
- Source: C:\Users\Leaves\Desktop\SHIT\科技\商业化\Step 2：构建虚拟关系社会与第一版多轮风险基准\outputs\benchmark\v0.1\benchmark_v0.1_20260716_130543
