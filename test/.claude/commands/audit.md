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

- target agent: `expense-auditor`

## Validation Failure

- status: `failed`
- code: `VALIDATION_MISSING_FIELD | VALIDATION_TYPE_MISMATCH | VALIDATION_INVALID_VALUE`
- reserved generic code: `VALIDATION_FAILED`
- error payload: `code/message/recoverable/details?`（遵循 `.claude/skills/shared/output-format/result-envelope.md`）
