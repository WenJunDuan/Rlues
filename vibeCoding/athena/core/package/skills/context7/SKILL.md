---
name: context7
description: 查第三方库/框架的官方 API、用法、版本差异时用（context7 文档检索）；项目内代码用 augment 或 rg。
---

# context7 — 库文档检索

何时用：design 选型、impl 遇到不确定 API、review 质疑用法是否正确。不用于项目内代码。

## 步骤

1. `npx ctx7 resolve <库名>` → 得到 ID（如 `/vercel/next.js`）。
2. `npx ctx7 get-docs <ID> --topic "<主题>"` → 文档片段。
3. 有 MCP 接入时直接用 context7 MCP 工具（Codex：`~/.codex/config.toml [mcp_servers.context7]`）。
4. 结论写进 design.md 或 log.md，保留 ctx7 ID + topic 作出处；不重写成无出处的断言。

## 降级

| 情况 | 处理 |
|---|---|
| resolve 为空 | 库名拼错或未索引 → 官方文档网页（web fetch） |
| get-docs 超时 | 重试 1 次，再降级 web fetch |
| 都找不到 | design 标「无文档支撑，待验证」 |

优先级：ctx7 > 官方文档网页 > 通用搜索。未安装：`npx ctx7 setup --claude`（CC）；Codex 走 MCP。

完成条件：用到的每个外部 API 结论都带出处。
