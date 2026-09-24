# vibeCoding 历史版本归档

只读归档，不再维护。当前版本在 `vibeCoding/athena/`（文档：`INSTALL.md` / `MIGRATION.md` / `RELEASE.md`）。按时间顺序：

| 目录 | 版本 | 形态 | 说明 |
|---|---|---|---|
| `01-riper-protocols/` | RIPER v4.9 – v5.6 | 单文件提示词 | RIPER-5/6/10 + P.A.C.E. 协作协议，最早的纯提示词形态 |
| `02-config-agent-v7/` | v7.0 – v8.0 | `claude/v7.x`、`codex/v7.8+` 分端目录 | config-agent 第一代（CLAUDE.md + agents/commands/skills）；`kernel-v8.0-*-README.md` 为 VibeCoding Kernel v8.0 说明 |
| `03-config-agent-v8-v9/` | v8.2 – v9.3 | 每个版本一个目录，内含 `.claude` / `.codex` 双端 | config-agent 第二代，双平台同版本发布 |
| `04-athena-8.9-9.9.9/` | 8.9 – 9.9.9 | `claude/<ver>`、`codex/<ver>`、`pi-agent/`、`scripts/` | Athena / PACE 9.x：hook 门禁 + `.ai_state` v1。10.1 起被单源构建取代 |
| `05-other-tools/` | — | — | Cursor 规则与 hooks、通用 MCP 配置片段 |

## `04-athena-8.9-9.9.9` 仍被引用的部分

| 路径 | 用途 |
|---|---|
| `claude/9.9.9`、`codex/9.9.9`、`pi-agent` | 10.1 构建测试的冻结基线（`athena/evals/fixtures/test_build.py` 等），**不要改** |
| `scripts/tests/athena999/` | 9.9.9 回归套件：`cd vibeCoding/old/04-athena-8.9-9.9.9/scripts/tests && python3 -m unittest discover -s athena999 -t athena999`（需 Python ≥ 3.11） |
| `scripts/*.py` 其余 | 9.9.2 / 9.9.3 / 9.9.8 时期脚本，路径按原仓库布局写死，归档后不保证可运行 |
