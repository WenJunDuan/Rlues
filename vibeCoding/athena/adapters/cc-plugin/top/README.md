# Athena {{athena:ATHENA_VERSION}} — Claude Code 插件形态

门禁核（H1–H5）+ `athena` CLI + PACE skills + agents，一个目录，不依赖 `~/.athena/current`。

## 装载

```bash
claude --plugin-dir <本目录>
```

需要 node ≥ 22 在 PATH。

## 内容

| 路径 | 作用 |
|---|---|
| `.claude-plugin/plugin.json` | 清单（name / version / description） |
| `hooks/hooks.json` | 9 个事件 → `gate/hook.cjs --platform cc` |
| `gate/` | 门禁核，与 `dist/athena` 同字节 |
| `bin/athena` | CLI 入口（插件 `bin/` 进 PATH） |
| `skills/` `agents/` | 与安装器形态同源 |
| `constitution.md` | 宪法正文；SessionStart hook 经 `ATHENA_CONSTITUTION` 注入 |

## 插件带不走

- `CLAUDE.md`：改由 SessionStart 注入 `constitution.md`（≤ 4 KB）。
- path-scoped rules（`~/.claude/rules/`）：仍需 `athena install --platform cc`。
- `settings.json` 的 permissions / env、`workflows/athena-review.js`：同上。

## 不要双装

安装器形态已写入 `~/.claude/settings.json` 的 hooks 时再启用本插件 → 每道门跑两遍。`athena doctor` 会报 WARN。二选一：只为 rules 而装时，装后删 settings.json 里的 Athena hooks，或停用插件。

## 待验证

- Claude Code 2.1.289：`plugin validate` 通过（仅 author 提示）；`plugin details` 识别 22 skills、4 agents、9 hooks。
- 官方文档支持 Markdown 中的 `${CLAUDE_PLUGIN_ROOT}` 展开；真实模型会话、子 agent PATH 与 Stop 仍待验证。
- 模板指向插件内 `gate/templates/`；agents 优先插件 `bin/`。path-scoped rules 仍由安装器提供。
