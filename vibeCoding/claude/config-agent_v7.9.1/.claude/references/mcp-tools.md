# MCP Tools Reference (v7.9.1)

## Required MCP

| Tool | Purpose | Notes |
|:---|:---|:---|
| **cunzhi** | 寸止确认 | 关键节点暂停等待 |

## Recommended MCP

| Tool | Purpose | Priority |
|:---|:---|:---|
| sequential-thinking | 深度推理 | 高 |
| memory | 跨会话记忆 | 中 |
| playwright | E2E测试 | 中 |

## Replaced by CLI/Skill

| Old MCP | New Method |
|:---|:---|
| context7-mcp | `npx ctx7` CLI + context7 skill |
| mcp-feedback-enhanced | cunzhi MCP |
| promptx | 已移除 |

## Tool Selection Guide

| 场景 | 使用 |
|:---|:---|
| 库/框架文档 | context7 skill (`npx ctx7`) |
| 寸止确认 | cunzhi MCP |
| 复杂推理 | sequential-thinking MCP |
| 持久记忆 | memory MCP |
| E2E 测试 | playwright MCP |

## Configuration Example

```json
{
  "mcpServers": {
    "cunzhi": {
      "command": "your-cunzhi-command"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/sequential-thinking-mcp"]
    }
  }
}
```

## Context Window Warning

- 不要同时启用太多 MCP
- 建议: < 10 个活动 MCP
- 建议: < 80 个总工具数
