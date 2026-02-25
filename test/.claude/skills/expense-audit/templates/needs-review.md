# needs-review template

## 适用条件
- 无 `error`，但存在关键 `warning`。
- 或关键信息缺失导致自动判定不可靠。

## 输出模板
```text
【审核结论】人工复核
【摘要】报销单 {report_id} 需要人工确认。
【触发原因】{warning_descriptions}
【待补充材料】{required_materials}
【当前证据】{evidence_refs}
```

## 附加要求
- `decision` 固定为 `needs_review`。
- `issues` 至少包含 1 条 `warning` 或 1 条“缺失字段”说明。
