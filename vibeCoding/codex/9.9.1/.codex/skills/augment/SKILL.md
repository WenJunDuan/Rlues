---
name: augment-context-engine
description: |
  augment-context-engine MCP 工具的调度说明.
  PACE plan / design 阶段做项目代码语义检索, 找"是否已经实现过"或"相关代码在哪里".
  避免重复造轮子.
---

# /augment — 项目代码语义检索 (v9.6.2)

## 何时用

| stage | 用例 |
|---|---|
| plan | "我们项目里有没有类似的实现?" / "这个 utility 是否已经存在?" |
| design | "改这个模块会影响哪些 caller?" |
| review | reviewer 找"删除的 export 是否还有引用" / "新接口是否与已有约定冲突" |

## 调用方式

### MCP 形式 (CX 端推荐)
配置在 `~/.codex/config.toml`:
```toml
[mcp_servers.augment-context-engine]
command = "npx"
args = ["ace-tool-rs", "--base-url", "https://acemcp.heroman.wtf/relay/", "--token", "<YOUR_ACE_TOKEN>"]

[mcp_servers.augment-context-engine.tools.search_context]
approval_mode = "approve"  # 用户确认后再执行 (因为远程调用)
```

调用: 主 agent 用 `spawn_agent` 创建 docs_researcher 任务, 在 `message` 中写明具体问题与允许使用的 MCP 工具; 不把 agent 名或配置路径当 shell 命令.

### CC 端
通过 MCP server 接入 (用户在 ~/.claude/mcp.json 或类似配置). 主 agent 用 `Use the augment-context-engine search_context tool` 调用.

### GX 端 (v9.6.2 新)
`~/.gemini/settings.json` 加 mcpServers:
```json
{
  "mcpServers": {
    "augment-context-engine": {
      "command": "npx",
      "args": ["ace-tool-rs", "--base-url", "...", "--token", "..."]
    }
  }
}
```

## 工具能力

主要工具: `search_context`
- 输入: 自然语言查询 (例如 "用户认证相关的代码")
- 输出: 相关代码片段 + 路径 + 上下文 (语义相似而非 grep 字符串匹配)

辅助工具: `find_definition`, `find_references`, `get_symbol_info` (按 augment 实际暴露而定)

## 与 grep / context7 的区别

| 工具 | 用什么搜 | 输出 |
|---|---|---|
| **augment-context-engine** | 自然语言 (语义) | 项目内代码片段 |
| **grep / rg** | 字符串 / 正则 | 文件 + 行号 |
| **context7** | 库名 + topic | 第三方库官方文档 |

**优先级**: 找项目内已有实现 → augment > rg. 找"是否有这个字符串" → rg > augment.

## 关键约束

- approval_mode = "approve" → 用户必须明确同意 (因为远程, 可能上传项目代码片段做检索)
- token 严禁硬编码在 config 模板里, 用 placeholder
- 若用户机器无 token → 降级到 rg / grep, 不阻塞 PACE 流程

## 工作流示例

```
plan stage, 主 agent 接到任务 "加 JWT refresh"
↓
主 agent 调用 augment search_context "JWT verify 已有实现"
↓
返回: src/auth/jwt.ts 已有 verifyToken 函数
↓
主 agent 写 design.md: "复用 src/auth/jwt.ts, 新增 refreshToken 函数邻接"
```
