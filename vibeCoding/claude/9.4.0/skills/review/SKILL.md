---
name: review
effort: high
context: fork
description: >
  质量审查和评分。多模型 review + 安全扫描 + 归档。当进入 T 阶段时触发。
allowed-tools: Bash, Read, Grep, Glob
---

# Review Skill: 质量审查 + 归档

核心原则: **写代码的模型不独自审查自己的代码。**

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`

## 已完成的 Task
!`grep -c "\[x\]" .ai_state/tasks.md 2>/dev/null`

## 审查进度 (如有, 说明部分审查已完成, 从断点继续)
!`ls .ai_state/reviews/ 2>/dev/null`
!`head -20 .ai_state/reviews/sprint-*.md 2>/dev/null`

## 可用审查工具
!`which codex 2>/dev/null`
!`npx ecc-agentshield --version 2>/dev/null`

---

## 前置检查

- **Path A:** 确认修复完成即可
- **Path B+:** tasks.md 有完成的 Task
- project.json stage → "T"
- `mkdir -p .ai_state/reviews`

---

## 审查链 (Path B 完整流程)

按以下顺序执行, 每一步结果追加到 `.ai_state/reviews/sprint-N.md`:

### Step 1: 冒烟测试

运行项目核心测试命令 (npm test / pytest / 项目特定命令)。
记录结果到 review 报告: 通过/失败/覆盖率。

### Step 2: /codex:review (外部标准审查)

```
/codex:review --background
/codex:status       → 等待完成
/codex:result       → 取回结果
```

将 codex:result 输出写入 review 报告。
**必须等拿到结果再进行下一步。**

### Step 3: /codex:adversarial-review (Path C+ 对抗审查)

```
/codex:adversarial-review challenge the [关键设计决策]
```

结果追加到 review 报告。

### Step 4: ECC 安全扫描 (Path C+)

```
npx ecc-agentshield scan
```

结果追加到 review 报告。

### Step 5: Claude 最终审查

Claude 自己做最终审查:
1. 对照 .ai_state/design.md 验收标准逐条确认
2. 检查 codex:result 反馈中的问题是否已修复
3. 确认测试通过
4. 检查是否有遗漏的 TODO / 占位符

### Step 6: @evaluator 综合评分

委托 @evaluator, 附带:
- design.md (验收标准)
- 代码变更 (git diff)
- codex:result + ECC 输出 (如有)
- 测试结果

@evaluator 4 维评分 → VERDICT 写入 review 报告。

---

## 审查链 (按 Path 精简)

| Path | 执行步骤 |
|------|---------|
| A | 冒烟测试 + `/codex:review` 或 `/review` (无需 @evaluator) |
| B | Step 1→2→5→6 |
| C | Step 1→2→3→4→5→6 |
| D | Step 1→2→3→4→5→6 + playwright E2E |

---

## VERDICT 和后续

| VERDICT | 均分 | 动作 |
|---------|------|------|
| PASS | ≥4.0 | → V 归档 |
| CONCERNS | 3.0-3.9 | → 修复 → 重新评分 |
| REWORK | 2.0-2.9 | → 回 E |
| FAIL | <2.0 | → 回 D |

---

## V 归档 (PASS 后)

1. project.json: conventions + gotchas 更新
2. lessons.md: 追加本 Sprint 教训
3. project.json: stage="", sprint+1
4. 告知用户: "Sprint N 完成, 交付了 X 个 Feature。"

## Gotchas

- ❌ 只用 /review 自审就交付 → ✅ Path B+ 必须 /codex:review 外部审查
- ❌ 不等 codex:result 就调 evaluator → ✅ 必须等结果
- ❌ CONCERNS 放过 → ✅ 修复后重新评分
- ❌ 不写审查报告 → ✅ 每步结果追加到 reviews/sprint-N.md
- ❌ 不做冒烟测试 → ✅ Step 1 必须运行测试
