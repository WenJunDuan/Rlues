# amount-check

## 规则目标
校验报销金额的结构正确性和制度阈值一致性。

## 规则清单
1. `EXP-AMT-001` 发票金额必须大于 0。
2. `EXP-AMT-002` 报销单汇总金额必须等于发票金额求和（允许误差 `<= 0.01`）。
3. `EXP-AMT-003` 报销总额不得超过 `standard_query.limit`；若缺少 limit，降级为 `warning`。
4. `EXP-AMT-004` 币种不是 `CNY` 时标记 `warning`，要求人工确认汇率换算依据。

## 输入字段
- `expense_report.total_amount`
- `expense_report.invoices[].amount`
- `expense_report.invoices[].currency`
- `standard_query.limit`（可选）

## 输出示例
```json
{
  "rule_id": "EXP-AMT-003",
  "severity": "error",
  "category": "amount",
  "description": "report total exceeds policy limit",
  "evidence_ref": "policy://expense/limit",
  "score_delta": -0.35
}
```

## 决策影响
- 出现 `error`：进入拒绝路径。
- 仅 `warning`：进入人工复核路径。
