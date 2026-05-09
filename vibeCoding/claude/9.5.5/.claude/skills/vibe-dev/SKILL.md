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

## Get-bearings (R₀, just-in-time)

1. **必读**: `.ai_state/project.json` → Path/Stage/Sprint/gotchas
2. **按需**: 阶段=impl/review → read progress.md + tasks.md
3. **按需**: 任务命中 lessons 主题 → read .ai_state/lessons.md
4. **按需**: `git log --oneline -10`
5. **按需**: impl/review 阶段 → `bash .ai_state/init.sh`

文件大就用 head/tail/grep，不要 cat 全文。跨项目记忆请装 claude-mem 或 superpowers (Hermes 不再做)。

## Dispatch

有进行中的 stage → 从当前阶段继续 (触发 pace skill)
新需求 → 触发 pace skill 路由，需求: $ARGUMENTS

首次使用简短说明: "PACE 帮你路由: 小事直接做，大事加设计和审查。"
