# 平台差异（CC / CX / Pi）

语义一致，不伪造对称工具名。门禁核、CLI、stages 三端相同。

| 项 | Claude Code | Codex | Pi |
|---|---|---|---|
| 宪法 | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | 插件每轮追加 `plugin/core/IRON.md` |
| rules | `~/.claude/rules/` | `~/.codex/standards/`（避开 Codex `.rules` 权限文件） | `config/rules/` |
| 门禁挂载 | settings.json hooks → `node ~/.athena/current/hook.cjs <事件> --platform cc` | hooks.json，同一命令 `--platform cx` | 扩展 athena-gates.ts 进程内调用 |
| 子 agent | Agent 工具 + `~/.claude/agents/*.md`（`omitClaudeMd: true`） | `spawn_agent` + `~/.codex/agents/*.toml` | `/generator` 等 prompt 或 pi-subagents |
| 红区隔离 | `isolation: worktree` | 自建 git worktree，任务写 `worktree: /abs/path` | 自建 worktree + 新 session |
| 续派 | SendMessage 给同一 agent | 同一 thread 继续 | 同一 session 继续 |
| 独立 review | reviewer agent；可选 `athena-review` workflow（flag `cc_workflows`） | reviewer agent | `/reviewer` prompt |
| Stop 硬停 | 支持 | 支持 | 无硬停（0.87）：ship 用 followUp 提示 |

模型、effort、provider、权限由用户原生配置决定；不设覆盖子 agent 模型的全局环境变量（如 `CLAUDE_CODE_SUBAGENT_MODEL`，会让角色配置静默失效）。能调用某工具不等于该副作用已获授权。

安装与检查：`athena install --platform cc,cx[,pi]`、`athena doctor`、`athena rollback`（见 athena-setup）。

官方文档（滚动更新，承重行为需本机实测）：[CC subagents](https://code.claude.com/docs/en/sub-agents) · [CC hooks](https://code.claude.com/docs/en/hooks) · [CC settings](https://code.claude.com/docs/en/settings) · [Codex config](https://developers.openai.com/codex/config-reference)。
