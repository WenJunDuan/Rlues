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

本 command 层自身承担编排职责（Orchestrator 角色），调度以下 Agent/Plugin：

1. `@file-parser`：解析 `payload` 中附件，产出结构化发票字段。
2. `@policy-researcher`：检索租户制度与限额/类目约束。
3. 数据采集阶段（Plugin 纯 I/O）：
   - `plugins/tax_api/main.py`：调用税务局 API，返回原始验真结果（预留对接）。
4. `@expense-auditor`：汇总步骤 1–3 结果，执行 skill rules 判定并输出最终结论。
   - 所有 skill rules 全部执行（不短路），聚合后产出 decision。

### 并行优化（可选）
- 当步骤 1 与步骤 2 输入互不依赖时，可并行执行。
- `@expense-auditor` 内部不做 Task fan-out，只允许串行补拉缺失插件结果。

## Validation Failure

- status: `failed`
- code: `VALIDATION_MISSING_FIELD | VALIDATION_TYPE_MISMATCH | VALIDATION_INVALID_VALUE`
- reserved generic code: `VALIDATION_FAILED`
- error payload: `code/message/recoverable/details?`（遵循 `.claude/skills/shared/output-format/result-envelope.md`）
