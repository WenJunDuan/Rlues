---
name: audit
description: 报销审核入口
---

# /audit

## Input Contract

- required: `payload.expense_report`
- required: `payload.expense_report.invoices[]`
- required: `payload.applicant`
- required: `payload.trip_application | payload.outing_application`
- required: `payload.policy_pack`

## Route

### 调度路径（默认串行流水线）
1. `@file-parser`：解析 `payload` 中附件，产出结构化发票字段。
2. `@policy-researcher`：检索租户制度与限额/类目约束。
3. `@orchestrator`：调度外部校验插件并聚合结果（`tax_verify/history_check/standard_query`）。
4. `@expense-auditor`：汇总步骤 1 + 2 + 3 结果，执行规则并输出最终结论。
   - 优先消费上游注入的插件结果。
   - 若上游缺失，允许在 Subagent 内按 `tax_verify -> history_check -> standard_query` 串行补拉。

### 并行优化（可选）
- 当步骤 1 与步骤 2 输入互不依赖时，可由 Orchestrator 使用 Task 工具并行执行。
- 步骤 3 的插件调用可并行 fan-out；所有子结果必须在 `@expense-auditor` 前完成聚合。
- `@expense-auditor` 内部不做 Task fan-out，只允许串行补拉缺失插件结果。

## Validation Failure

- status: `failed`
- code: `VALIDATION_MISSING_FIELD | VALIDATION_TYPE_MISMATCH | VALIDATION_INVALID_VALUE`
- reserved generic code: `VALIDATION_FAILED`
- error payload: `code/message/recoverable/details?`（遵循 `.claude/skills/shared/output-format/result-envelope.md`）
