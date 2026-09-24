# PACE References · Hooks & Compound (v9.9.3, Codex)

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart (startup\|resume\|clear) | session-start.py | 注入 _index.md + stage-specific 操作提示 |
| UserPromptSubmit | user-prompt-submit.py + index-updater.py | 预检 + counts 同步 (mtime 比对); v9.9.0 index-updater 加 re-route 机械触发 (文件数超路径上限 → next_action=re-route) |
| PreToolUse | pre-bash-guard.py | 灾难命令与 ship 前 push 门禁; 对可观察调用做软防护, 不声称能校验原生工具不存在的 cwd 参数 |
| PostToolUse | subagent-retry.py + evidence-collector.py + index-updater.py | 使用 `tool_response` 记录可观察过程证据; 无法确认状态时记 unknown, 不默认成功 |
| SubagentStart / SubagentStop | subagent-tracker.py | 仅记录生命周期; 不从 Start 推断完成, 不从 Stop 猜 exit code, 不自动推进 next_action |
| Stop | delivery-gate.py | 交付门禁; Feature+ 要求 generator 的 Stop 完成记录 + checklist/review 产物, Start 记录不能解锁 |
| PreCompact | compact-snapshot.py | compact 前快照 _index.md (v9.7.0 新, CX 0.129+) |
| PostCompact | compact-restore.py | compact 后注回 _index.md 摘要 (v9.7.0 新) |

> CC 端另有 Notification hook (notification-router.cjs, agent_completed → 软提醒消费 next_action), CX hooks GA 事件集无 Notification — 已知不对称.

> Codex hooks 协议要点 (0.144.1):
> - Stop 事件要求 JSON 输出 (plain text 无效); `decision:"block"` + `reason` 生成续跑提示
> - additionalContext 放 `hookSpecificOutput` 并带 `hookEventName`
> - PostToolUse 支持 systemMessage / continue:false / stopReason; PreToolUse 返回这些会被标 hook 失败
> - 输入含 `permission_mode` (default/acceptEdits/plan/dontAsk/bypassPermissions); turn 级含 `turn_id`
> - SubagentStop 提供生命周期字段, 不提供可安全默认的命令退出码
> - hooks 可覆盖 shell、`apply_patch` 与部分 MCP, 但实际 handler/matcher 覆盖必须实测; evidence 走降级链 (见 stages.md)
> - 多 hook 并发执行无顺序保证
> - hook 是流程护栏, 不是完整安全边界; OS sandbox、权限与人工确认仍负责真正隔离
>
> 官方说明: https://learn.chatgpt.com/docs/hooks

## compound 联动 (铁律[复利])

- plan stage 开始: 主 agent 读 `_index.pointers.latest_decisions` 列出的 5 个 `decision-*.md`
- design stage: grep 关键词读相关 `learning-*.md` + `trick-*.md`
- polish stage 完成: 触发 `/compound add learning` 提示
- review 发现 P0: reviewer 触发 `/compound add learning`

详: `~/.agents/skills/compound/SKILL.md`

## 项目级例外 (用户可调)

v9.9.1 保留旗标: `plan_critique_min_rounds` (0=auto: Refactor/System=2 其余=1) · `skip_impl_subagent_check` (纯绿区微改才设) · `skip_runtime_verify` / `skip_architecture_check`. 全部在 `_index.md` frontmatter, delivery-gate 读取.

- `_index.skip_polish = true`: 跳过 polish (用户自负责)
- `_index.skip_architecture_check = true`: 跳过 architecture mtime 检查
- `_index.plan_critique_disabled = true`: 关闭多轮 critique
- `_index.plan_critique_max_rounds = N`: 调整最大轮数 (2-6)
