# VibeCoding Kernel v9.1.7

## 铁律 (违反即阻断交付)
1. **先搜后写** — 写代码前用 augment-context-engine 搜项目代码 + context7/mcp-deepwiki 查库文档。不搜就写 = 盲人摸象
2. **先测后码** — 源码文件必须有对应测试。delivery-gate 会用 git diff 检查。无测试 = 不交付
3. **寸止确认** — 设计方向、计划、交付前必须人工确认。用 cunzhi MCP 发起确认。跳过确认 = 不交付

## 入口
收到任务 → 读 .claude/workflows/pace.md 路由复杂度 → 按 riper-7.md 执行阶段

## 行为校准
- 不确定时说出来, 不要猜
- compact 前先存 .ai_state/status.md
- 两次 compact = 任务太大, 考虑拆分或用子代理
- 避免过度工程 — 最简方案优先
