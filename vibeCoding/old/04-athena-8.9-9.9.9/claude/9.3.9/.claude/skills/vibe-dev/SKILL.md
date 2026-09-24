---
name: vibe-dev
effort: high
disable-model-invocation: true
argument-hint: "<需求描述>"
description: >
  VibeCoding 主入口。从需求到交付的完整工程化开发流程。
---

# /vibe-dev — 完整开发流程

## 项目状态
!`cat .ai_state/project.json 2>/dev/null`

## 流程

1. .ai_state/ 不存在? → 先初始化 (从 riper-pace/templates/ 复制模板)
2. 触发 riper-pace skill → PACE 路由 → RIPER 全流程执行
3. 需求: $ARGUMENTS

如果用户不熟悉, 简短说明:
"我会按流程帮你: 分析需求 → 设计方案 → 你确认 → 写代码+测试 → 质量审查 → 交付。关键节点需要你确认。"
