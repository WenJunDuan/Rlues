---
name: plan-first
description: 强制先规划后执行 — Path B+ 任务必须在 Plan 模式完成设计后再写代码
context: main
---

# Plan-First

> 最常见的 AI 编程失败不是 bad code, 而是 solving the wrong problem。

## 协议

Path B+ 启动时自动触发:

1. **不写代码, 先出计划** — 交付物: `.ai_state/plan.md`
2. 计划包含: 有序任务列表, 每个标注目标+涉及文件+验收标准
3. 参考 `.ai_state/pitfalls.md` 标注风险
4. **cunzhi PLAN_APPROVED** 确认后才进入 E 阶段
5. 执行中计划变更 > 30% → 重新 cunzhi 确认

SP `writing-plans` 可用时让 SP 生成初稿, VibeCoding 补充 Path 分级参数。
