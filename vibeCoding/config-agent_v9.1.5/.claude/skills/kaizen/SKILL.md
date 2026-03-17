---
name: kaizen
description: 持续改进 — 交付后复盘经验沉淀 (NeoLabHQ kaizen 模式)
context: main
---
## 用途
从每次交付中提炼可复用经验, 避免重复踩坑。

## 流程

### 1. 回顾变更
```bash
git diff --stat HEAD~{commits}..HEAD
git log --oneline HEAD~{commits}..HEAD
```

### 2. 反思 (三个必答问题)
- 哪些决策正确? **为什么**正确? (记录根因, 不是结果)
- 哪里浪费了时间? 根因是什么? (工具不熟? 设计返工? 需求不清?)
- 什么模式可以复用? (代码模式、流程模式、工具用法)

### 3. 写入
- **knowledge.md**: `[日期] 领域: 可复用模式`
- **lessons.md**: `[日期] 领域: 陷阱描述 → 正确做法`
- **conventions.md**: 如发现新规范 → 追加

### 4. 归档
核心决策和变更摘要 → archive.md

## 原则
每条 ≤2 行, 只记有价值的, 不记 AI 已知常识。
