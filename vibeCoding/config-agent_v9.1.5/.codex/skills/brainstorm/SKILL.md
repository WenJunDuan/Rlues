---
name: brainstorm
description: Spec 生成与方案探索 — 发散-收敛结构化流程 (SDD spec-first 模式)
context: main
---

## 流程

### 1. 定义问题

用一句话提炼需求本质。不复述用户的话。

### 2. 发散搜索

- **动手**: `augment-context-engine` 搜项目代码 — 类似功能?
- **动手**: `mcp-deepwiki` 查候选库文档 — 成熟库?
- **动手**: `cat .ai_state/knowledge.md | grep 关键词` — 历史经验
- **动手**: `cat .ai_state/lessons.md` — 上次踩坑?
- **动手**: `web search` — 社区方案?

### 3. 追问筛选

为什么选这个库? 数据量大 100 倍还能工作吗? 最简方案是什么?

### 4. 收敛输出 → .ai_state/design.md

Spec (MUST/SHOULD/COULD + 非功能需求 + 约束 + 验收标准) + 2-3 候选方案

### 5. cunzhi [DESIGN_DIRECTION]
