---
name: verification
description: V 阶段 Path 分级验证清单
context: main
---

# Verification

| 检查项 | A | B | C | D |
|:---|:---:|:---:|:---:|:---:|
| npm test | ✓ | ✓ | ✓ | ✓ |
| eslint clean | — | ✓ | ✓ | ✓ |
| tsc --noEmit | — | ✓ | ✓ | ✓ |
| 覆盖率 ≥ 80% | — | — | ✓ | ✓ |
| 无 TODO/FIXME | — | — | ✓ | ✓ |
| 集成测试 | — | — | — | ✓ |
| npm audit (high) | — | — | ✓ | ✓ |

失败 → 自动修复重试 (max 3) → SP debugging → cunzhi 人工介入。
结果写入 `.ai_state/verified.md`。
