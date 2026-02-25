# reject template

## 适用条件
- 命中至少 1 条 `error` 级规则。

## 输出模板
```text
【审核结论】拒绝
【摘要】报销单 {report_id} 未通过自动审核。
【拒绝原因】{top_error_description}
【关键规则】{top_rule_id}
【证据链】{evidence_refs}
【处理建议】申请人修正后重新提交，或转人工复核。
```

## 附加要求
- `issues` 必须包含至少 1 条 `severity=error`。
- `evidence` 必须包含可追溯引用（历史命中/制度条款/税务结果其一）。
