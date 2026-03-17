---
name: context7
description: 库文档按需拉取 — 任何阶段可用
context: main
---
## 工具
1. `mcp-deepwiki`: 查询指定库文档 (首选)
2. `web search`: 搜官方文档 (降级)

## 使用时机
- R₀: 候选库对比 → 辅助选方案
- R/D: API 接口确认 → 补充 design.md
- E: 不确定用法时即时查 → 避免猜测
- T: 确认 lint/test 配置

## 原则: 不预加载, 按需拉取, 仅取所需章节
