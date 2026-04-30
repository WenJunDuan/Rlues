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

## Get-bearings (R₀, v9.5 升级)

1. **全局**: 扫 `~/.claude/lessons/INDEX.md` → 找命中本任务主题, 读对应 lesson 文件
2. 读 `.ai_state/project.json` → Path / **Scenario** / Stage / Sprint
3. 读 `.ai_state/progress.md` → 上次做了什么
4. 读 `.ai_state/lessons.md` 最近 10 条 → 本任务是否命中 Pattern/Pitfall
5. **读 `.ai_state/sprint-{N-1}-summary.md` 和 `sprint-{N-2}-summary.md`** (如存在) → 最近 2 个 sprint 故事 (v9.5 新)
6. `git log --oneline -10`
7. 读 `.ai_state/tasks.md` → 待办/完成/阻塞
8. impl/review 阶段 → `bash .ai_state/init.sh` → 基线测试
9. **4 元素口诀自检** (CLAUDE.md 顶部): 上下文 + 目标 + 约束 + 验证 都齐了吗?

## Dispatch

有进行中的 stage → 从当前阶段继续 (触发 pace skill)。

新需求 → 触发 pace skill 路由, 需求: $ARGUMENTS

### v9.5 场景分支

新需求且即将进 stage=plan, **根据 project.json `scenario` 字段**, PACE skill 内部 include 对应模板:

| scenario | 模板 | 重点 |
|----------|------|------|
| `from-zero` | `~/.claude/skills/pace/prompts/from-zero.md` | 图 04: Idea→Spec→Architecture→Tasks→Code |
| `modify-existing` | `~/.claude/skills/pace/prompts/change-existing.md` | 图 06: Read→Locate→Plan→Patch→Verify, 强制 change-plan.md |

scenario 字段空 → 提示用户运行 `/vibe-init` (会自动判定写入)。

首次使用简短说明: "PACE 帮你路由: 小事直接做, 大事加设计和审查。改已有项目会先勘察再动手。"
