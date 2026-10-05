# Athena {{athena:ATHENA_VERSION}} — Codex 插件形态

门禁核（H1–H5）+ PACE skills，一个目录，不依赖 `~/.athena/current`。

## 装载

按 Codex 的插件安装流程装入本目录（本地 marketplace 后执行 `codex plugin add athena@<marketplace>`）。装后在 `/hooks` 里审阅并信任本插件的 hooks —— 未受信前门禁不生效。

需要 node ≥ 22 在 PATH。

## 内容

| 路径 | 作用 |
|---|---|
| `plugin.json` | 根清单；故意不带 Agent Plugins `$schema`（见待验证），hooks 走默认 `hooks/hooks.json` 发现 |
| `hooks/hooks.json` | 8 个事件 → `${PLUGIN_ROOT}/gate/hook.cjs --platform cx` |
| `gate/` | 门禁核，与 `dist/athena` 同字节 |
| `skills/` | 与安装器形态同源 |

## 插件带不走

- `config.toml`、`AGENTS.md`、`standards/`：仍需 `athena install --platform cx`。
- agents（`.codex/agents/*.toml`）：能否随插件分发未验证，本包不带，由安装器提供。
- `athena` 命令：本包不带 `bin/`；用 `node <插件目录>/gate/cli.cjs`，或安装器的 `~/.athena/bin/athena`。

## 不要双装

`~/.codex/hooks.json` 已有 Athena hooks 时再启用本插件 → 每道门跑两遍。`athena doctor` 会报 WARN。

## 待验证

- Codex 0.160.0 临时环境安装与原生加载通过：22 skills、8 hooks；仍需 `/hooks` 受信与真实工具触发验证。
- `$schema`：加上后 Codex 按 AgentPlugin 格式加载并跳过 hooks（openai/codex#47925，≤0.160.0 实测 0 hooks）；不加则 description 不被读取但 hooks 正常发现。上游修复后再加。
- 模板指向插件内 `gate/templates/`；Markdown 的 `${PLUGIN_ROOT}` 展开仍待真实会话验证。
