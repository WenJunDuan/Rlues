# MCP Tools Reference

## Claude Code 平台

| 工具 | 名称 | 用途 |
|:---|:---|:---|
| augment-context-engine | sou | 语义代码搜索 |
| cunzhi | 寸止 | 确认点 (真暂停) |
| mcp-deepwiki | deepwiki | 技术文档/Wiki 查询 |

## Codex CLI 平台 (额外)

| 工具 | 名称 | 用途 |
|:---|:---|:---|
| chrome-devtools | devtools | 前端实时调试 |
| desktop-commander | commander | 系统级 GUI 操作 |

## 已移除 (v8.0)

| 工具 | 移除原因 | 替代方案 |
|:---|:---|:---|
| sequential-thinking | Adaptive Thinking 替代 | effort=max |
| memory | .ai_state 文件系统替代 | .ai_state/*.md |
| mcp-feedback-enhanced | cunzhi 完全替代 | cunzhi |
| context7-mcp | CLI 版本替代 | npx ctx7 |
| promptx | skills 系统替代 | .claude/skills/ |

## 使用优先级

```
1. sou (augment-context-engine) — 语义搜索，首选
2. grep/find — 精确文本匹配
3. read_file — 最后手段
```

## 降级策略

| 工具不可用 | 降级方案 |
|:---|:---|
| sou | grep + find |
| cunzhi | 文字 [CUNZHI] 标记请求确认 |
| mcp-deepwiki | Web 搜索 |
| context7 CLI | mcp-deepwiki → Web 搜索 |
| chrome-devtools | 手动测试指导 |
| desktop-commander | CLI 命令替代 |

## 注意

**寸止无降级到跳过** — 必须通过某种方式与用户交互确认。
