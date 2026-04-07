---
name: review
effort: high
context: fork
description: >
  质量审查和评分。多模型 review + 安全扫描 + 归档。当进入 T 阶段时触发。
allowed-tools: Bash, Read, Grep, Glob
---

# Review Skill: 质量审查 + 归档

核心原则: **写代码的模型不应该独自审查自己的代码。**

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`

## 已完成的 Task
!`grep -c "\[x\]" .ai_state/tasks.md 2>/dev/null`

## 可用审查工具
!`which codex 2>/dev/null`
!`npx ecc-agentshield --version 2>/dev/null`

---

## 前置检查

- **Path A:** 确认修复代码已完成即可
- **Path B+:** tasks.md 中有 "完成" 的 Task
- project.json stage 更新为 "T"
- 确保 `mkdir -p .ai_state/reviews` (写入报告前)

---

## 审查调度 (按 Path 深度)

### Path A — 选一即可
- `/codex:review` 或 `/review` (CC 内置)
- 通过就可交付, 不需要 @evaluator 评分

### Path B — 按顺序

1. `/codex:review --background` → `/codex:status` → `/codex:result`
2. 运行项目测试: `npm test` / `pytest` 等
3. @evaluator 综合评分 (附带 codex:result + 测试结果)
4. 结果写入 `.ai_state/reviews/sprint-N.md`

**重要:** 必须等 /codex:result 拿到结果后再调 @evaluator。

### Path C — 全部

1. `/codex:review --background`
2. `/codex:adversarial-review --background` (可与 1 并行)
3. `/codex:status` → `/codex:result` (等 1+2 完成)
4. `npx ecc-agentshield scan`
5. 运行项目测试
6. @evaluator 综合评分 (附带所有审查结果 + 测试结果)
7. 结果写入 `.ai_state/reviews/sprint-N.md`

### Path D — 全部 + E2E
- 同 Path C
- 如有前端: playwright-skill E2E 测试

### 未来扩展
当其他模型 CLI 可用时 (如 Gemini CLI), 加入审查链。当前只有 codex-plugin-cc。

---

## @evaluator 评审

委托 @evaluator 时提供:
1. .ai_state/design.md — 验收标准
2. 代码变更 (git diff 或文件列表)
3. 前置审查结果 (codex:result + ECC)
4. 测试结果

4 维评分:
| 维度 | 说明 |
|------|------|
| Functionality | 验收标准逐条检查 |
| Spec Compliance | 对照 design.md |
| Craft | 命名、结构、可维护性 |
| Robustness | 异常处理、边界、安全 |

---

## VERDICT 和后续动作

| VERDICT | 均分 | 动作 |
|---------|------|------|
| PASS | ≥4.0 | → V 归档 |
| CONCERNS | 3.0-3.9 | → 修复问题 → 重新评分 |
| REWORK | 2.0-2.9 | → 回 E 阶段重做 |
| FAIL | <2.0 | → 回 D 阶段重新设计 |

---

## V 归档 (PASS 后)

1. project.json: 追加新发现的 conventions 和 gotchas
2. lessons.md: 追加本 Sprint 教训
3. project.json: `stage=""`, `sprint+1`
4. 告知用户: "Sprint N 完成, 交付了 X 个 Feature。"

## Gotchas

- ❌ 只用 /review 自审就交付 → ✅ Path B+ 必须有跨模型审查
- ❌ adversarial-review 不指定方向 → ✅ 给方向: "challenge the caching design"
- ❌ @evaluator CONCERNS 就放过 → ✅ 必须修复后重新评分
- ❌ 忘记写审查报告 → ✅ 结果必须写入 .ai_state/reviews/
