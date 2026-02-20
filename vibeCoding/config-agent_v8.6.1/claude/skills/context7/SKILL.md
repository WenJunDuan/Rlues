---
name: context7
description: 库文档按需拉取 — brainstorm/R/D/E 阶段使用, 验证技术可行性
context: main
---
需要查询依赖库文档时:
1. 优先: `mcp-deepwiki` 查询 (MCP)
2. 备选: `npx ctx7 resolve {库名}` (CLI)
3. 降级: 使用 WebSearch 搜索官方文档

## 使用时机 (贯穿流程)
- **R₀b brainstorm**: 方案对比时拉取候选库文档, 验证 API 是否满足需求
- **R 研究**: 深入调研已选技术栈的具体用法和限制
- **D 设计**: 查 API 细节确认接口设计可行
- **E 开发**: 不确定 API 用法时即时查询

不预加载, 按需拉取, 仅取所需章节。
