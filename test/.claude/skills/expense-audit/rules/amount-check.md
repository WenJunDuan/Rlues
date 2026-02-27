# amount-check

## 规则目标
校验报销金额的结构正确性和制度阈值一致性。
该规则不写死具体制度阈值，阈值必须来自 `payload.policy_pack`（由制度文档提炼而来）。

## 规则清单
1. `EXP-AMT-001` 发票金额必须大于 0。
2. `EXP-AMT-002` 报销单汇总金额必须等于发票金额求和（允许误差 `<= 0.01`）。
3. `EXP-AMT-003` 报销总额不得超过制度限额（优先使用 `payload.policy_pack.standard_file` 中的职级限额）；若无匹配职级，降级为 `warning`。
4. `EXP-AMT-004` 币种不是 `CNY` 时标记 `warning`，要求人工确认汇率换算依据。

## 输入字段
- `expense_report.total_amount`
- `expense_report.invoices[].amount`
- `expense_report.invoices[].currency`
- `expense_report.level`（用于匹配职级限额）
- `payload.policy_pack.standard_file`（推荐）
- `payload.policy_pack`（结构化制度字段，作为兜底）

## 制度参考
参见 `payload.policy_pack` 对应标准文件中的「职级报销限额」数据。
`rules/policy-standards.md` 仅定义标准文件结构，不提供默认业务值。

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
