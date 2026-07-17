# Benchmark v0.1 Evidence Update (M6.5)

**Date:** 2026-07-17
**Status:** CROSS_MODEL_DIRECTION_STABLE — MODEL_LEVEL_DEPENDENCE

## Results

| Model | bounded | high_sycophancy | reality_grounding | hs-bs | hs-rs |
|-------|---------|-----------------|-------------------|-------|-------|
| DeepSeek V4 Flash | 0.05 | **0.88** | 0.03 | +0.83 | +0.85 |
| Qwen Flash | 0.00 | **1.00** | 0.00 | +1.00 | +1.00 |
| GLM-4-FlashX | 0.05 | **0.45** | 0.00 | +0.40 | +0.45 |

## Classification

- Primary: CROSS_MODEL_DIRECTION_STABLE
- Secondary: MODEL_LEVEL_DEPENDENCE
- Rank dependence: None
- Conclusion dependence: None

## GLM-4-Flash Diagnostic

glm-4-flash excluded: all 18 eps sy=0.30. Ignored system prompts. Archived.
glm-4.7-flash excluded: reasoning model, 5min+/call, too slow for interactive simulation.

## Conclusion

> 在三个被测Companion Model中，高奉承Policy均产生更高的奉承性风险观察值，Policy效应方向保持一致；但效应强度因模型而异（MODEL_LEVEL_DEPENDENCE）。该结果仅适用于当前受控场景、Policy实现、模型版本和评估配置。
