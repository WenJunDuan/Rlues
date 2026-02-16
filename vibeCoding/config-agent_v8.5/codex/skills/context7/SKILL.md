---
name: context7
description: E 阶段按需拉取库文档 — 用 ctx7 获取准确 API 信息
context: main
---

# Context7 — 库文档按需拉取

## 使用时机

E 阶段遇到不确定的 API 用法时:
1. `npx ctx7 resolve <library>` → 获取最新文档
2. 如果 ctx7 不可用 → `mcp-deepwiki` 查询
3. 如果 deepwiki 也不可用 → Web search

## 示例

```bash
npx ctx7 resolve express    # Express 路由/中间件 API
npx ctx7 resolve prisma     # Prisma schema/query API
npx ctx7 resolve vitest     # Vitest 断言/mock API
```

## 原则

- 不猜 API, 查了再用
- 查到的关键信息记入 `.ai_state/tools.md`
