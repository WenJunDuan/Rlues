# PACE References · Hooks & Compound (v9.7.0)

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart | session-start.cjs | 注入 _index.md + stage-specific 操作提示 |
| PreToolUse(Bash) | pre-bash-guard.cjs | 灾难命令拦截 |
| PreToolUse(Task) | subagent-worktree-check.cjs | 铁律[零写入] 红区/并行强制 worktree |
| PostToolUse(Edit/Write/MultiEdit) | index-updater + evidence-collector + design-change-detector | 状态同步 / 证据收集 / design 变更标记 |
| PostToolUse(Bash) | evidence-collector | 命令证据 |
| PostToolUse(Task) | subagent-retry | 失败记录 |
| SubagentStop | subagent-tracker.cjs | 写 subagent-log + roadmap 自动推进 |
| WorktreeCreate / WorktreeRemove | worktree-tracker.cjs | worktrees.yaml + active_worktrees |
| Stop | delivery-gate.cjs + pace-continuator.cjs | 交付门禁 (确定性 command) + 历史/软提醒 |
| PermissionDenied | permission-retry.cjs | deny 反馈 |
| PreCompact / PostCompact | compact-snapshot/restore.cjs | 跨 compact 状态恢复 |

> v9.7.0 协议要点 [官方 code.claude.com/docs/en/hooks]:
> - JSON 输出仅在 exit 0 时解析; exit 2 时 JSON 被忽略 → 所有 Stop hook 统一 exit 0 + 纯 JSON stdout
> - additionalContext 放 `hookSpecificOutput` 并带 `hookEventName`; 输出上限 10,000 字符
> - Stop 输入含 `stop_hook_active` (前一个 Stop hook 已续命) 与 `background_tasks` (2.1.145+, 后台任务状态)
> - Stop hook 连续 block 有上限 (默认 8, env `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`); block reason 必须含明确解锁动作

## compound 联动 (铁律[复利])

- plan stage 开始: 主 agent 读 `_index.pointers.latest_decisions` 列出的 5 个 `decision-*.md`
- design stage: grep 关键词读相关 `learning-*.md` + `trick-*.md`
- polish stage 完成: 触发 `/compound add learning` 提示
- review 发现 P0: reviewer 触发 `/compound add learning`

详: `~/.claude/skills/compound/SKILL.md`

## 项目级例外 (用户可调)

- `_index.skip_polish = true`: 跳过 polish (用户自负责)
- `_index.skip_architecture_check = true`: 跳过 architecture mtime 检查
- `_index.plan_critique_disabled = true`: 关闭多轮 critique
- `_index.plan_critique_max_rounds = N`: 调整最大轮数 (2-6)
