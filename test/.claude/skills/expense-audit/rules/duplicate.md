# duplicate

## 规则目标
识别“同单内重复”和“历史重复报销”两类风险。

## 规则清单
1. `EXP-DUP-001` 同一报销单内 `invoice_code + invoice_number + date` 不可重复。
2. `EXP-DUP-002` 命中 `history_check.hits[]` 的发票，判定为历史重复。
3. `EXP-DUP-003` 若仅命中“相同金额+相近日期”但票据号不同，输出 `warning` 供人工复核。

## 输入字段
- `expense_report.invoices[]`
- `history_check.hits[]`
- `expense_report.employee_id`

## 输出示例
```json
{
  "rule_id": "EXP-DUP-002",
  "severity": "error",
  "category": "duplicate",
  "description": "invoice already reimbursed in historical records",
  "evidence_ref": "history://hit/record_id",
  "score_delta": -0.45
}
```

## 决策影响
- `EXP-DUP-001/002` 命中为强拒绝信号。
- `EXP-DUP-003` 仅触发复核，不直接拒绝。
