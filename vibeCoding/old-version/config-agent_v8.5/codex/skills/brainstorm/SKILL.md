---
name: brainstorm
description: R/D 阶段工具编排 — augment 搜索 + ADR 输出格式
context: main
---

# Brainstorm

> R/D 阶段的工具组合和输出格式。具体步骤见 `workflows/riper-7.md`。

## 工具优先级

1. `augment-context-engine` — 搜现有代码 (关键词: 功能名/模块名)
2. `mcp-deepwiki` — 查外部文档 (新库/新 API)
3. `.ai_state/pitfalls.md` — 历史踩坑
4. `.ai_state/requirements/` + `assets/` — 需求文档和设计图

## ADR 输出格式

```markdown
## ADR-{N}: {标题}
- 状态: proposed → accepted
- 背景: {搜索结果摘要}
- 决策: {选定方案}
- 后果: {预期影响}
```

写入 `.ai_state/design.md`, 重大决策同步到 `decisions.md`。
