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
3. `@expense-auditor`：汇总步骤 1 + 2 结果，执行规则并输出最终结论。

### 并行优化（可选）
- 当步骤 1 与步骤 2 输入互不依赖时，可由 Orchestrator 使用 Task 工具并行执行。
- 并行子任务结果必须在 `@expense-auditor` 前完成聚合；Subagent 内不做 Task fan-out。

## Validation Failure

- status: `failed`
- code: `VALIDATION_MISSING_FIELD | VALIDATION_TYPE_MISMATCH | VALIDATION_INVALID_VALUE`
- reserved generic code: `VALIDATION_FAILED`
- error payload: `code/message/recoverable/details?`（遵循 `.claude/skills/shared/output-format/result-envelope.md`）
