---
name: context7
description: 按需拉取库文档到上下文
context: main
---

## 管道位置: 任何阶段 → 查文档时使用

## 用法

1. 优先用 context7 CLI: `context7 resolve <library>` 获取文档
2. 备选: mcp-deepwiki MCP 查询
3. 拉取后提取关键 API 签名, 不要把整个文档塞进上下文

## 使用时机

- R₀b brainstorm: 候选库文档对比
- R 研究: 深入调研技术栈
- D 设计: 确认 API 接口可行
- E 开发: 不确定用法时即时查询

不预加载, 按需拉取, 仅取所需章节。

---

name: context7
description: 按需查询库文档

---
