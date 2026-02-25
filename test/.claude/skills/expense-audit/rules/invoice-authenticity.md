# invoice-authenticity

## 规则目标
基于税务验真与内部复用检查结果判断票据真实性与可用性。

## 规则清单
1. `EXP-INV-001` `tax_verify.status != verified` 时，标记 `error`（税务验真未通过）。
2. `EXP-INV-002` `invoice_verify.used_before=true` 时，标记 `error`（疑似重复报销）。
3. `EXP-INV-003` 税务验真接口未接通或回退策略命中时，记录 `info`，不直接拒绝。

## 输入字段
- `tax_verify.status`
- `tax_verify.issues[]`
- `invoice_verify.used_before`
- `invoice_verify.status`
- `invoice_verify.verify_id`

## 输出示例
```json
{
  "rule_id": "EXP-INV-003",
  "severity": "info",
  "category": "invoice_authenticity",
  "description": "tax verification API unavailable; downgraded to first-gate mode",
  "evidence_ref": "tax_verify://verified_at",
  "score_delta": -0.05
}
```

## 决策影响
- 发票真实性风险优先级高，命中 `error` 时直接进入拒绝路径。
- 第一关模式下，接口不可用不作为拒绝的直接触发条件。
