# PACE References · Hooks & Compound (v9.9.3)

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart | session-start.cjs | 注入 _index.md + stage-specific 操作提示 |
| PreToolUse(Bash) | pre-bash-guard.cjs | 灾难命令拦截; v9.9.0 加 git push 门禁 (stage != ship 拦, 防 CC 2.1.198 worktree 自动 PR 绕过 review; 逃生 ATHENA_ALLOW_PUSH=1) |
| PreToolUse(Agent) | subagent-worktree-check.cjs | 铁律[零写入] 红区/并行强制原生 worktree |
| PostToolUse(Edit/Write/MultiEdit) | index-updater + evidence-collector + design-change-detector | 状态同步 / 证据收集 / design 变更标记; v9.9.0: index-updater 加 re-route 机械触发; design-change-detector 挂 if 过滤 (2.1.178+, 只在 design.md 被 Edit 时起进程, 失效有 delivery-gate mtime 兜底) |
| Notification | notification-router.cjs | v9.9.0: agent_completed → 软提醒消费 next_action (fail-open, CC 2.1.198+; CX 无此事件, 不对称) |
| PostToolUse(Bash) | evidence-collector | 官方成功事件 → pass; 不读 legacy tool_output/exit_code |
| PostToolUseFailure(Bash/Agent) | evidence-collector + subagent-retry | 官方失败事件 → fail/error/interrupt/duration |
| SubagentStart / SubagentStop | subagent-tracker.cjs | exact raw JSONL; Start 冻结 sprint, Stop 按 agent_id 回写; assignment 由主 agent握手 |
| WorktreeCreate / WorktreeRemove | 默认不注册 | 使用 Claude Code 原生 Git worktree; 自定义 hook 仅非 Git VCS 专用 profile |
| InstructionsLoaded / ConfigChange | config-change-audit.cjs | 只记来源/文件名, 不复制配置值 |
| StopFailure | stop-failure-recorder.cjs | 模型/API 停止失败元数据, secret redaction |
| Stop | delivery-gate.cjs + pace-continuator.cjs | 交付门禁 (确定性 command) + 历史/软提醒 |
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
- review 发现 P0: 主 agent 根据 reviewer 返回结果触发 `/compound add learning`

详: `~/.claude/skills/compound/SKILL.md`

## 项目级例外 (用户可调)

v9.9.0 新增旗标: `plan_critique_min_rounds` (0=auto: Refactor/System=2 其余=1) · `skip_impl_subagent_check` (U1 逃生, 纯绿区微改才设) · `skip_runtime_verify` / `skip_architecture_check` (原有)。全部在 `_index.md` frontmatter, delivery-gate 读取。

- `_index.skip_polish = true`: 跳过 polish (用户自负责)
- `_index.skip_architecture_check = true`: 跳过 architecture mtime 检查
- `_index.plan_critique_disabled = true`: 关闭多轮 critique
- `_index.plan_critique_max_rounds = N`: 调整最大轮数 (2-6)
