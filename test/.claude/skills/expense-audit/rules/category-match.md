# category-match

## 规则目标
确保报销项类目与公司制度和票据内容一致。

## 规则清单
1. `EXP-CAT-001` 发票类目必须落在 `standard_query.allowed_categories[]`。
2. `EXP-CAT-002` 报销单行项目类目与发票类目不一致时记为 `warning`。
3. `EXP-CAT-003` 类目属于敏感项（如礼品、招待）时，要求备注业务场景；缺失则 `warning`。
4. `EXP-CAT-004` 税务校验结果为异常时，类目结论降级为 `needs_review`，避免误拒。

## 输入字段
- `expense_report.invoices[].category`
- `expense_report.items[].category`（可选）
- `standard_query.allowed_categories[]`
- `tax_verify.status`

## 输出示例
```json
{
  "rule_id": "EXP-CAT-001",
  "severity": "error",
  "category": "category",
  "description": "invoice category not allowed by policy",
  "evidence_ref": "policy://expense/category",
  "score_delta": -0.3
}
```

## 决策影响
- 类目越权（`EXP-CAT-001`）优先级高于普通金额异常。
- 类目冲突但证据不足时，应偏向 `needs_review`。
