# Athena {{athena:ATHENA_VERSION}} — Codex 插件形态

门禁核（H1–H5）+ PACE skills，一个目录，不依赖 `~/.athena/current`。

## 装载

按 Codex 的插件安装流程装入本目录（具体命令待本机验证）。装后在 `/hooks` 里审阅并信任本插件的 hooks —— 未受信前门禁不生效。

需要 node ≥ 22 在 PATH。

## 内容

| 路径 | 作用 |
|---|---|
| `plugin.json` | 清单；`extensions["com.openai"].hooks = ./hooks/hooks.json` |
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

- 清单字段、`extensions["com.openai"].hooks`、`${PLUGIN_ROOT}` 展开：待本机 Codex 验证。
- skills 正文里的 `${PLUGIN_ROOT}/skills/...` 是否展开：未验证。
- 已知缺口：skills 正文仍写安装器路径（`~/.athena/current/templates/`）；纯插件形态下模板在 `gate/templates/`。
