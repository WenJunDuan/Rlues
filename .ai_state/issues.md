# Issues

| id | 类型 | 级别 | 一句话 | 发现于 | 去向 | 状态 |
|---|---|---|---|---|---|---|
| D-014 | debt | P2 | 10.1.0 发布门豁免行为评测（S8 dropped），无 9.9.9 对比基线 | decisions/2026-09-24-decision-athena-10-1-release-gate.md | 10.2 发布门恢复；先在 quantum 真实 sprint 中收集 | open |
| U-001 | upstream | P2 | Codex（≤0.160.0 实测）根 plugin.json 带 Agent Plugins `$schema` 时按 AgentPlugin 格式加载并整段跳过 hooks（openai/codex#47925，loader.rs 格式判断提前返回，未修）；不带 `$schema` 时默认发现 `hooks/hooks.json`，hooks 不缺，仅根清单 description 不读。现保持不带 `$schema` | docs/reports/2026-10-04-athena-10-1-5-review.md | 上游修复后给 cx-plugin 根清单加 `$schema` 并复跑 P6；不阻塞 10.1.5 | open |
