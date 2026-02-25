# invoice-authenticity

## 规则目标
基于发票验真结果判断票据真实性与可用性。

## 规则清单
1. `EXP-INV-001` 验真结果 `verified=false` 时，标记 `error`（不合规）。
2. `EXP-INV-002` 验真结果 `used_before=true` 时，标记 `error`（疑似重复报销）。
3. `EXP-INV-003` 验真接口未接通时，按第一关策略默认有效并记录 `info`，不直接降级。

## 输入字段
- `invoice_verify.verified`
- `invoice_verify.status`
- `invoice_verify.risk_tags[]`
- `invoice_verify.verify_id`

## 输出示例
```json
{
  "rule_id": "EXP-INV-003",
  "severity": "info",
  "category": "invoice_authenticity",
  "description": "invoice verification API unavailable; assumed valid in first-gate mode",
  "evidence_ref": "invoice_verify://verify_id",
  "score_delta": -0.05
}
```

## 决策影响
- 发票真实性风险优先级高，命中 `error` 时直接进入拒绝路径。
- 第一关模式下，接口不可用不作为拒绝或复核的直接触发条件。
