---
name: context7
description: E 阶段按需拉取第三方库文档 — 使用 context7 CLI 获取最新 API 文档
context: main
---

# Context7 — 库文档按需拉取

## 用途

写代码时需要第三方库 API 文档, 按需拉取到 context window, 不预加载。

## 调用方式

```bash
# 搜索可用库
npx ctx7 resolve <library-name>

# 示例
npx ctx7 resolve next.js
npx ctx7 resolve prisma
npx ctx7 resolve tailwindcss
```

## 集成点

- **E 阶段**: 开始用某个库的 API 前, 先 ctx7 拉文档
- **R 阶段**: 评估技术方案时, 查库的最新版本特性
- 与 `mcp-deepwiki` 分工: deepwiki 查开源项目源码文档, ctx7 查库的使用文档

## 原则

不预加载所有依赖的文档 — 太浪费 context。
用到什么查什么, 查完继续写。
