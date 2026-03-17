---
name: context7
description: 按需查询库文档
---

## 用法

查询依赖库文档时:

1. 优先: ctx7 和 mcp-deepwiki 查询
2. 降级: WebSearch 搜索官方文档
3. 提取关键 API 签名, 不要把整个文档塞进上下文

## 使用时机

- R₀b brainstorm: 候选库文档对比
- R 研究: 深入调研技术栈
- D 设计: 确认 API 接口可行
- E 开发: 不确定用法时即时查询

不预加载, 按需拉取, 仅取所需章节。
