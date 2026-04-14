---
name: riper-pace
effort: high
description: >
  工作流引擎。收到开发任务、不确定该做什么时触发。PACE 路由 + RIPER 阶段编排。
---

# RIPER-PACE

首先读 .ai_state/project.json。有进行中的 stage → 从该 stage 继续。
.ai_state/ 不存在 → 提示用户 `/vibe-init`。

## PACE 路由

| 维度 | A | B | C | D |
|------|---|---|---|---|
| 文件数 | 1-3 | 4-10 | 10+ | 跨服务 |
| 时间 | <30min | 30min-4h | 4h-2d | >2d |
| 架构影响 | 无 | 局部 | 跨模块 | 系统级 |

| 配置 | A | B | C | D |
|------|---|---|---|---|
| 阶段 | E→T | R₀→R→D→P→E→T→V | 同B | 同B |
| 规划 | 无 | superpowers | /ultraplan | /ultraplan+对抗 |
| 执行 | 手动TDD | codex:rescue→@generator→手动 | +/batch | +Agent Teams |
| 审查 | /review | codex:review→@evaluator | +adversarial+ECC | +playwright |

路由完成 → 写 project.json {path, stage, sprint} → 进入首阶段。

## RIPER 阶段门控

| 阶段 | 进入条件 | 产出 | 退出门控 |
|------|---------|------|---------|
| R₀ | path≠A | .ai_state/design.md | 用户确认 |
| R | design.md 有需求 | design.md 追加技术方案 | 技术方案非空 |
| D | 技术方案就绪 | tasks.md 填充 | 用户确认 |
| P | tasks.md 非空 | tasks.md 补充依赖顺序 | tasks 有序 |
| E | tasks.md 有待办 | 代码 + 测试通过 | tasks.md 全部 [x] |
| T | 全部完成 | reviews/sprint-N.md | VERDICT=PASS |
| V | PASS | lessons.md + conventions | sprint+1 |

阶段后退: T-REWORK→E, T-FAIL→D
Path A 跳过: 直接 E→T
