---
name: tdd
description: Path 分级 TDD 策略
context: main
---

# TDD

| Path | 测试范围 | 提交频率 | 覆盖率 |
|:---|:---|:---|:---|
| A | 跳过 | 改完一次 | — |
| B | 核心逻辑 | 每功能 | 60%+ |
| C | 全覆盖 RED→GREEN | 每测试通过 | 80%+ |
| D | + 集成 + E2E | 原子 commit | 80%+ |

RED → GREEN → REFACTOR → commit → 循环。
SP `tdd` 提供方法论, VibeCoding 补充 Path 分级。
