---
name: vibe-dev
effort: xhigh
disable-model-invocation: true
argument-hint: "<需求描述>"
description: >
  VibeCoding 主入口。从需求到交付的完整工程化开发流程。
---

# /vibe-dev

.ai_state/ 不存在 → 提示 `/vibe-init`

## Get-bearings (R₀)

1. **全局**: 扫 `~/.claude/lessons/INDEX.md` → 找命中本任务主题, 读对应 lesson 文件
2. 读 `.ai_state/project.json` → Path/Stage/Sprint
3. 读 `.ai_state/progress.md` → 上次做了什么
4. 读 `.ai_state/lessons.md` 最近 10 条 → 本任务是否命中 Pattern/Pitfall
5. `git log --oneline -10`
6. 读 `.ai_state/tasks.md` → 待办/完成/阻塞
7. impl/review 阶段 → `bash .ai_state/init.sh` → 基线测试

## Dispatch

有进行中的 stage → 从当前阶段继续 (触发 pace skill)
新需求 → 触发 pace skill 路由，需求: $ARGUMENTS

首次使用简短说明: "PACE 帮你路由: 小事直接做，大事加设计和审查。"
