# PACE References · Hooks & Compound (v9.7.0, Codex)

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart (startup\|resume) | session-start.py | 注入 _index.md + stage-specific 操作提示 |
| UserPromptSubmit | user-prompt-submit.py + index-updater.py | 预检 + counts 同步 (mtime 比对) |
| PreToolUse(Bash) | pre-bash-guard.py | 灾难命令拦截 + 铁律[零写入] 红区 spawn_agent --cwd 强制 + worktree 命令跟踪 |
| PostToolUse(Bash) | subagent-retry.py + evidence-collector.py | spawn_agent 日志/roadmap 推进 + 过程证据收集 (v9.7.0 新) |
| SubagentStop | subagent-tracker.py | subagent 完成记录 (v9.7.1: 读取官方 agent_type / agent_id, 兼容旧字段) |
| Stop | delivery-gate.py | 交付门禁 (exit 0 + JSON decision) |
| PreCompact | compact-snapshot.py | compact 前快照 _index.md (v9.7.0 新, CX 0.129+) |
| PostCompact | compact-restore.py | compact 后注回 _index.md 摘要 (v9.7.0 新) |

> v9.7.0 协议要点 [官方 developers.openai.com/codex/hooks]:
> - Stop 事件要求 JSON 输出 (plain text 无效); `decision:"block"` + `reason` 生成续跑提示
> - additionalContext 放 `hookSpecificOutput` 并带 `hookEventName`
> - PostToolUse 支持 systemMessage / continue:false / stopReason; PreToolUse 返回这些会被标 hook 失败
> - 输入含 `permission_mode` (default/acceptEdits/plan/dontAsk/bypassPermissions); turn 级含 `turn_id`
> - SubagentStop 输入含 `agent_type` / `agent_id`; 不再依赖早期实验字段名
> - **拦截不完整**: 非 shell、非 MCP 工具调用 (含文件写) 不触发 hook → evidence 走降级链 (见 stages.md)
> - 多 hook 并发执行无顺序保证

## compound 联动 (铁律[复利])

- plan stage 开始: 主 agent 读 `_index.pointers.latest_decisions` 列出的 5 个 `decision-*.md`
- design stage: grep 关键词读相关 `learning-*.md` + `trick-*.md`
- polish stage 完成: 触发 `/compound add learning` 提示
- review 发现 P0: reviewer 触发 `/compound add learning`

详: `~/.codex/skills/compound/SKILL.md`

## 项目级例外 (用户可调)

- `_index.skip_polish = true`: 跳过 polish (用户自负责)
- `_index.skip_architecture_check = true`: 跳过 architecture mtime 检查
- `_index.plan_critique_disabled = true`: 关闭多轮 critique
- `_index.plan_critique_max_rounds = N`: 调整最大轮数 (2-6)
