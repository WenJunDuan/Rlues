---
sprint_slug: ""
reviewed_at: ""
reviewers: []                  # [reviewer, spec-compliance, evaluator]
verdict: ""                    # PASS | CONCERNS | REWORK | FAIL (by evaluator)
---

# Review Pass 1 — {sprint_slug}

## Reviewer (代码层 findings)

### F1 [P0] (题目)
- 现象: ...
- 文件: src/...:L...
- 建议: ...

### F2 [P1] ...

---

## Spec Compliance (spec-compliance subagent, {timestamp})

> 由 spec-compliance subagent 追加. 检查 design.md 列出的功能是否都在 git diff 实现.

### MISSING (功能做少了)
- M1: design.md L23 列出 "添加 refresh token 端点", 但 git diff 中无 src/api/refresh.ts
- M2: ...

### EXTRA (功能做多了)
- E1: git diff 改了 src/utils/logger.ts (合理 refactor / scope creep)
- E2: ...

### DEVIATED (功能做偏了)
- D1: design.md 要求 RS256, 实际 src/auth/jwt.ts 仍是 HS256
- D2: ...

### Spec Compliance 总评

- MISSING 数: -
- EXTRA 数: - (合理 refactor X 个 / scope creep Y 个)
- DEVIATED 数: -
- 建议: PASS | REWORK

---

## Evaluator VERDICT

> 由 evaluator subagent 综合 reviewer + spec-compliance findings 给出最终判定.

**VERDICT**: PASS | CONCERNS | REWORK | FAIL

**理由**: [一段话]

**下一步**:
- PASS / CONCERNS (路径∈Refactor/System) → polish
- PASS / CONCERNS (其他路径) → ship
- REWORK / FAIL → 回 impl

(evaluator 写完后, 更新 `.ai_state/_index.md.next_action`)
