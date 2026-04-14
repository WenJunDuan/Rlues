---
name: plan
effort: high
description: >
  需求分析和设计规划。project.json stage 为 R₀/R/D/P 时触发。
---

# Plan: R₀ → R → D → P

读 .ai_state/project.json 确认当前子阶段。

## R₀ 需求精炼

brainstorming 自动激活 → 结果整理到 .ai_state/design.md (参照 templates/design.md)
如果 brainstorming 写到了别处 → 合并回 design.md，唯一真相源。
用户确认 → stage="R"

## R 技术调研

Grep 搜项目 → augment-context-engine 语义搜索 → ctx7 查关键库 → 读 lessons.md
design.md 追加: 技术方案 + 接口 + 依赖 + 风险
→ stage="D"

## D 方案定稿

@evaluator 评审方案合理性 (或 /review 快速审查)
从 design.md 验收标准生成 .ai_state/tasks.md (参照 templates/tasks.md)
用户确认 → stage="P"

注意: 此阶段无代码，不用 /codex:adversarial-review

## P 计划排期

Path B: superpowers writing-plans
Path C/D: /ultraplan
tasks.md 补充依赖和执行顺序
→ stage="E"
