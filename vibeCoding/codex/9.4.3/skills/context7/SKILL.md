---
name: context7
description: >
  查询库/框架的最新文档。当需要 API 文档、库用法、配置方法时自动激活。
---

# Context7 — 库文档查询

当任务涉及库/框架/API 且不确定用法时，用 ctx7 CLI 查文档。

## 用法

```bash
# Step 1: 查找库 ID
ctx7 library <库名> "<查询>"

# Step 2: 用返回的 ID 查文档
ctx7 docs <library-id> "<具体问题>"
```

## 示例

```bash
ctx7 library next.js "middleware setup"
# 返回: /vercel/next.js (ID)

ctx7 docs /vercel/next.js "how to create middleware"
# 返回: 最新版本的文档和代码示例
```

## 指定版本

在查询中提及版本号即可: `ctx7 docs /vercel/next.js "Next.js 15 app router"`

## 降级

ctx7 CLI 不可用 → web_search 查官方文档。
