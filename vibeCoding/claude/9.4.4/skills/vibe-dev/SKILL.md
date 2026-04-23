---
name: vibe-dev
effort: high
disable-model-invocation: true
argument-hint: "<需求描述>"
description: >
  VibeCoding 主入口。从需求到交付的完整工程化开发流程。
---

# /vibe-dev

.ai_state/ 不存在 → 提示 `/vibe-init`

## Get-bearings

1. 读 .ai_state/project.json → Path/Stage/Sprint
2. 读 .ai_state/progress.md → 上次做了什么
3. 读 .ai_state/lessons.md 最近 10 条 → 本任务是否命中 Pattern/Pitfall
4. `git log --oneline -10`
5. 读 .ai_state/tasks.md → 待办/完成/阻塞
6. impl/review 阶段 → `bash .ai_state/init.sh` → 基线测试

## Dispatch

有进行中的 stage → 从当前阶段继续 (触发 pace skill)
新需求 → 触发 pace skill 路由，需求: $ARGUMENTS

首次使用简短说明: "PACE 帮你路由: 小事直接做，大事加设计和审查。"
