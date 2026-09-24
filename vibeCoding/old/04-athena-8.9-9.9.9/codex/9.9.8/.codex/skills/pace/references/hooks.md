# PACE References · Hooks & Compound (v9.9.6, Codex)

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart (startup\|resume\|clear) | session-start.py | 注入 _index.md + stage-specific 操作提示 |
| UserPromptSubmit | user-prompt-submit.py | 面包屑与提示预检；不启动 index-updater 扫描 (W40) |
| PreToolUse | pre-bash-guard.py + delivery-gate.py + subagent-worktree-audit.py | 灾难命令、spec/push 门禁，以及 `spawn_agent|Agent` 红区 worktree 前置阻断 |
| PostToolUse | evidence-collector.py + design-change-detector.py + index-updater.py (仅 Edit/Write) | validation 证据脱敏落盘；普通 Bash/MCP 不生成 raw telemetry (W35/W40) |
| SubagentStart / SubagentStop | subagent-tracker.py + SubagentStart 的 subagent-worktree-audit.py | 仅保留生命周期与已启动 agent 的 worktree 审计；不做 token 记账 (W40) |
| Stop | delivery-gate.py | 交付门禁；不续跑、不做 token 记账 (W35/W40) |
| PreCompact | 未注册 (compact-snapshot.py) | 默认不复制 _index 快照 (W35) |
| PostCompact | compact-restore.py | compact 后注回 _index.md 摘要 (v9.7.0 新) |

> CC 端另有 Notification hook (notification-router.cjs, agent_completed → 软提醒消费 next_action), CX hooks GA 事件集无 Notification — 已知不对称.

> Codex hooks 协议要点 (0.144.1):
> - Stop 事件要求 JSON 输出 (plain text 无效); `decision:"block"` + `reason` 生成续跑提示
> - additionalContext 放 `hookSpecificOutput` 并带 `hookEventName`
> - PostToolUse 支持 systemMessage / continue:false / stopReason; PreToolUse 返回这些会被标 hook 失败
> - **PreToolUse 阻断信道只有三条**: `hookSpecificOutput.permissionDecision:"deny"` + `permissionDecisionReason` / 旧式 `{"decision":"block","reason":…}` / **exit 2 且阻断原因写 stderr**。多 hook 时任一 deny 胜出; 无人决策走正常审批流; stdout 纯文本被忽略
> - **fail-open 陷阱**: `permissionDecision:"ask"` / `continue:false` / `stopReason` 会被解析但**不支持** — Codex 标记该 hook 运行失败、报错、然后**继续执行工具调用**
> - SubagentStart **无阻断语义** (`continue:false` 仅为兼容解析, 不阻止 subagent 启动), 只能注入 additionalContext 与留证据; 要拦 spawn 必须用 PreToolUse
> - 输入含 `permission_mode` (default/acceptEdits/plan/dontAsk/bypassPermissions); turn 级含 `turn_id`
> - SubagentStop 提供生命周期字段, 不提供可安全默认的命令退出码
> - hooks 可覆盖 shell、`apply_patch` 与部分 MCP, 但实际 handler/matcher 覆盖必须实测; evidence 走降级链 (见 stages.md)
> - 多 hook 并发执行无顺序保证
> - hook 是流程护栏, 不是完整安全边界; OS sandbox、权限与人工确认仍负责真正隔离
> - `subagent-retry.py` 是未注册的升级兼容清理 shim，不参与当前 PostToolUse 链，也不自动 retry
> - `pace-continuator.py`、`token-usage-collector.py`、`compact-snapshot.py` 均为未注册的历史/兼容资产，不参与默认 lifecycle (W35/W40)
> - 已启动的 worktree 违规会阻塞 ship；修复越界改动后须在对应 JSONL 行写 `resolved:true` 与非空 `resolution` 证据
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
