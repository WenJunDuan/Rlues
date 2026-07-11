---
name: context7
description: |
  调用 context7 (npx ctx7) 库文档解析工具.
  PACE plan / design / impl stage 在需要查第三方库 API / 用法 / 最佳实践时使用.
  避免凭记忆瞎写库 API.
---

# /context7 — 库文档解析 (v9.6.2)

## 何时用

| 场景 | 触发 |
|---|---|
| plan stage | "我想用 X 库实现 Y, 它的 API 怎么样?" |
| design stage | "Z 库的最佳实践是什么?" |
| impl stage | 写代码时遇到 API 不确定 → 先查 ctx7 |
| review stage | reviewer 不确定某用法是否 idiomatic → 让 docs_researcher 用 ctx7 |

## 关键命令

```bash
# 解析库 (得到 ctx7 ID)
npx ctx7 resolve react           # → /facebook/react
npx ctx7 resolve "next.js"       # → /vercel/next.js

# 获取文档片段 (按 topic)
npx ctx7 get-docs /facebook/react --topic "hooks useEffect"
npx ctx7 get-docs /vercel/next.js --topic "app router"

# 列出已索引的库
npx ctx7 list

# Setup (一次性, 用户初装 Athena 后跑)
npx ctx7 setup --claude          # CC 端
npx ctx7 setup --gemini          # Gemini 端 (v9.6.2 新)
# Codex 通过 MCP 接入, 配置在 ~/.codex/config.toml [mcp_servers.context7]
```

## 工作流

### 在 PACE 中调用

```
plan stage:
  主 agent 识别需要查库 X
  → Bash `npx ctx7 resolve <X>` (拿到 ID)
  → Bash `npx ctx7 get-docs <ID> --topic <T>` (拿到片段)
  → 把结果写入 `.ai_state/sprints/{current_sprint_slug}/research.md`
  → 继续 plan
```

### 在 review passN 中

```
reviewer 提出疑虑 "这个用法对吗?"
  → 主 agent 不直接回答
  → 调用 docs_researcher subagent (cx) 或 Task subagent_type 调研
  → docs_researcher 用 ctx7 查官方文档
  → docs_researcher 返回证据链, 主 agent 写入 `sprints/{current_sprint_slug}/reviews/passN.md`
```

## 与其他工具的关系

| 工具 | 用途 | 何时用 |
|---|---|---|
| **context7** (本) | 第三方库文档 (npm/pypi/cargo/...) | 已知库, 要查 API / 用法 |
| **augment-context-engine** | 项目代码语义检索 | 不知道项目里是否已实现某功能, 找现有代码 |
| **web_search** | 通用网络搜索 | 库的 issue / 上游讨论 / 博客案例 |
| **web_fetch** | 抓取指定 URL | 已知文档 URL, 全文加载 |

**优先级**: ctx7 > web_fetch > web_search (越靠前越精准, 越少 token).

## 输出约束

- 引用 ctx7 结果时必须保留 ctx7 ID + topic, 不要重写后失去溯源
- 若 ctx7 没找到库 → 降级到 web_search
- 若 web_search 也找不到 → 在 design.md 标注"无文档支撑, 走探索路径"

## 错误处理

| 错误 | 处理 |
|---|---|
| `ctx7 resolve` 返回空 | 库名拼错或 ctx7 索引未覆盖, 用 web_search |
| `ctx7 get-docs` 超时 | 重试 1 次, 失败则降级 web_fetch |
| ctx7 未安装 | `npm i -g @upstash/context7-mcp` (或对应平台安装命令) |

## 安装与配置

### CC 端 (skill 模式, 推荐)
```bash
npx ctx7 setup --claude
# 这会在 ~/.claude/skills/ 下安装 ctx7 skill, 主 agent 用 Bash 调用 npx ctx7
```

### CX 端 (MCP 模式)
```toml
# ~/.codex/config.toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
```

### GX 端 (v9.6.2 新, skill 模式)
```bash
npx ctx7 setup --gemini
# 或 MCP 模式: ~/.gemini/settings.json -> mcpServers.context7
```
