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
| Stop 硬停 | 支持 | 支持 | 支持（≥0.87，`agent_before_settle` 续跑；更旧版本退回 followUp 提示）· 待本机验证 |
| 插件形态 | `dist/claude-plugin`：hooks + 门禁核 + skills + agents + `bin/athena`；带不走 CLAUDE.md 与 rules（宪法由 SessionStart 注入，rules 仍靠 `athena install`） | `dist/codex-plugin`：hooks + 门禁核 + skills；带不走 `config.toml` 与 AGENTS.md；hook 装后须在 `/hooks` 受信 | `dist/pi/…/plugin` 即 Pi 包 |
| code mode | — | 默认关；嵌套调用是否触发 PreToolUse 官方文档与开放 issue 说法相反 · 待验证（探针 P1），未定前不要开 | 嵌套调用照发 `tool_call`（源码确认，待实跑）；外层 `codemode` 调用放行 |

模型、effort、provider、权限由用户原生配置决定；不设覆盖子 agent 模型的全局环境变量（如 `CLAUDE_CODE_SUBAGENT_MODEL`，会让角色配置静默失效）。能调用某工具不等于该副作用已获授权。

同一端不要同时启用安装器形态与插件形态：每个门禁会跑两遍，`athena doctor` 会告警。

安装与检查：`athena install --platform cc,cx[,pi]`、`athena doctor`、`athena rollback`（见 athena-setup）。

官方文档（滚动更新，承重行为需本机实测）：[CC subagents](https://code.claude.com/docs/en/sub-agents) · [CC hooks](https://code.claude.com/docs/en/hooks) · [CC settings](https://code.claude.com/docs/en/settings) · [Codex config](https://developers.openai.com/codex/config-reference)。

## 2026-10-04 本机验证（候选 10.1.5）

- CC 2.1.289：清单 validate 通过（author 提示）；原生 details 识别 22 skills / 4 agents / 9 hooks。真实模型、子 agent PATH 和完整 Stop 流程待验证。
- Codex 0.160.0：隔离 HOME 的本地 marketplace 安装成功，app-server plugin/read 识别 22 skills / 8 hooks；仍未验证 `/hooks` 受信后的工具触发。原 portable 根清单描述被忽略；添加官方 `$schema` 后，显式/default hooks 的三次加载均为 0 hooks，无 stderr/error，停止尝试。此项为发布阻塞，不改本机信任配置。
- Pi 本机无 CLI，P3/P7 待验证；适配器 fixture 不能替代真实 Pi。
- P1/P2 原生 code mode / spawn_agent 与行为质量评测未跑；未发起收费模型请求。
- 协议依据：[CC plugin manifest](https://code.claude.com/docs/en/plugins-reference)、[OpenAI package plugin](https://developers.openai.com/plugins/build/plugins)。本机结果与文档有差异时以探针结果限定声明。
