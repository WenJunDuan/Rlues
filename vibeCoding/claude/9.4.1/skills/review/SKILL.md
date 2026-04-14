---
name: review
effort: high
context: fork
description: >
  质量审查。project.json stage 为 T 时触发。审查链 + 评分 + 归档。
allowed-tools: Bash, Read, Grep, Glob
---

# Review: T + V 阶段

`bash .ai_state/init.sh` → 基线测试确认无回归。
`mkdir -p .ai_state/reviews`

## 审查链 (每步结果追加到 reviews/sprint-N.md，参照 templates/review-report.md)

<important>
codex:review 和 codex:adversarial-review 必须产生真实 tool_use 响应。
调用后用 /codex:status 确认任务存在。如果没有 → 调用未实际执行 → 跳过该步。
</important>

| Step | 动作 | Path |
|------|------|------|
| 1 | 运行测试 (project.json test_cmd) | 所有 |
| 2 | `/codex:review --background` → `/codex:status` 确认任务存在 → `/codex:result` | B+ |
| 2.5 | 验证 codex 输出: 引用的文件路径是否存在，不存在的结论作废 | B+ |
| 3 | `/codex:adversarial-review` → `/codex:status` 确认 | C+ |
| 3.5 | 同上验证 | C+ |
| 4 | `npx ecc-agentshield scan` | C+ |
| 5 | Claude 对照 design.md 验收标准逐条确认 | 所有 |
| 6 | @evaluator 综合评分 (附 design.md + git diff + 审查结果) | B+ |

Path A: Step 1 + `/review` 即可。

## VERDICT 处理

- PASS → V 归档
- CONCERNS → 修复 → 重新评分 (不阻断但必须修)
- REWORK → stage="E"
- FAIL → stage="D"

## V 归档 (PASS 后)

1. project.json: conventions + gotchas 更新
2. lessons.md: 追加 Sprint 教训
3. progress.md: Sprint 完成摘要
4. project.json: stage="", sprint+1
