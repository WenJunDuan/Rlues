# approve template

## 适用条件
- 无 `error`。
- 无高风险 `warning`。

## 输出模板
```text
【审核结论】通过
【摘要】报销单 {report_id} 通过自动审核。
【关键信息】员工 {employee_id}，总金额 {total_amount} {currency}。
【证据】已完成金额校验、重复检索、类目匹配，未发现拒绝项。
```

## 附加要求
- `issues` 可为空数组。
- `evidence` 至少包含 1 条规则执行摘要。
