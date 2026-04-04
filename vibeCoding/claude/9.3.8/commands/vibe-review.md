# /vibe-review — 质量审查

只走审查流程。前提: 代码已实现。

## 流程

1. 读 .ai_state/state.json 确认当前 Path
2. 触发 review skill (T + V 阶段)
3. 按 Path 深度编排审查工具
4. @evaluator 评分 → quality.json → VERDICT
5. PASS → 归档; CONCERNS → 提示修复; REWORK/FAIL → 提示回退

## 用法

```
/vibe-review                                      # 标准审查
/vibe-review --adversarial challenge the auth design  # 对抗审查并聚焦
/vibe-review --security                            # 含安全扫描
```

$ARGUMENTS 传递给 adversarial-review 作为聚焦方向。
