# Decision — _index 字段消费者审计 (9.9.2, design §5.3)

## 结论
`_index.md` 字段**无孤儿** — 每个字段有消费者, 无需删除。

## 依据
- hook 消费: stage/path/current_sprint_slug/next_action/skip_*/plan_critique_*/design_changed_after_impl/counts/fingerprint (delivery-gate/index-updater 读)。
- agent 消费 (读文档, hook 0 引用不等于无消费者): route_confidence/route_history/plan_model/platform_features/tools_available (主 agent 路由审议与工具选择读)。

## 取舍
- 删无消费者字段是 design §5.3 目标, 但审计发现**均有消费者**, 故本版只补两层记忆/检索路由框架文档, 不删字段。
- last_subagent/last_subagent_at 与 JSONL 重复, 属"仅记录"低价值位 → 保留 (删除收益<误伤风险), 标待后续单独评估。
