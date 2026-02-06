---
name: context7
description: |
  Library documentation fetcher using Context7 CLI (npx ctx7).
  Provides up-to-date, version-specific docs for external libraries.
  CLI version replaces Context7 MCP for lower context overhead.
context: fork
allowed-tools:
  - Bash(npx ctx7*)
  - Bash(npm *)
---

# Context7 Documentation Skill (CLI)

## 自动触发

检测到以下情况时自动激活：
- 使用外部库/框架 (React, Next.js, Vue, Express...)
- 查看 package.json / go.mod / requirements.txt 中的依赖
- 报错涉及第三方 API

## 使用方式

```bash
# 搜索库
npx ctx7 search "react hooks"

# 获取文档
npx ctx7 docs react --topic="useState"

# 指定版本
npx ctx7 docs next@14 --topic="app router"
```

## 与 mcp-deepwiki 分工

| 工具 | 负责 | 示例 |
|:---|:---|:---|
| context7 | 库/框架级 API 文档 | React hooks 用法 |
| mcp-deepwiki | 架构/Wiki 级知识 | 系统设计模式 |

## 降级

context7 CLI 不可用 → mcp-deepwiki 搜索 → Web 搜索。
