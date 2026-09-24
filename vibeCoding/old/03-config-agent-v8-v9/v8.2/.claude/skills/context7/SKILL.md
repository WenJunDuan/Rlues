---
name: context7
description: "Library documentation query via ctx7 CLI with deepwiki fallback"
context: fork
allowed-tools:
  - Bash(npx ctx7*)
  - Bash(npm *)
---

# Context7 (库文档查询)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| ctx7 CLI | NPX | 搜索和查询库文档 | `npx ctx7 search/docs` |
| deepwiki | MCP | 架构/设计模式 | `deepwiki.query("主题")` |

## 触发条件

E 阶段检测到外部库/框架使用时按需激活。

## 用法

```bash
npx ctx7 search "react hooks"
npx ctx7 docs react --topic="useState"
npx ctx7 docs next@14 --topic="app router"
npx ctx7 docs prisma --topic="relations"
```

## 与 deepwiki 分工

| 场景 | ctx7 | deepwiki |
|:---|:---|:---|
| 库 API 用法 | ✓ | — |
| 框架版本差异 | ✓ | — |
| 架构设计模式 | — | ✓ |
| 技术选型调研 | — | ✓ |

## 降级链

ctx7 → deepwiki → Web 搜索。
