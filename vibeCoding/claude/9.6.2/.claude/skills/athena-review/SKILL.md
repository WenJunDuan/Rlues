---
name: athena-review
description: |
  用户主动触发 review (例如 "review 一下我刚写的代码"). 调用 reviewer + evaluator subagent.
effort: medium
---

# /athena-review — 用户主动 review

## 工作流

1. Read `.ai_state/_index.md` 确认 stage
2. 若 stage != review, 提示用户 "建议先完成 impl 再 review"
3. Task `subagent_type: reviewer` → 写 findings 到 `details/reviews/sprint-{N}.md`
4. Task `subagent_type: evaluator` → 追加 VERDICT
5. 根据 VERDICT 决定下一步:
   - PASS / CONCERNS (Refactor/System) → 提示进 polish stage
   - PASS / CONCERNS (其他路径) → 提示进 ship
   - REWORK / FAIL → 提示回 impl

详见 `~/.claude/agents/reviewer.md` 和 `~/.claude/agents/evaluator.md`.
