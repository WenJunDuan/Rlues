---
name: thinking
description: 深度推理，第一性原理分析
mcp_tool: sequential-thinking
---

# Thinking Skill (Sequential Thinking)

深度推理引擎，用于第一性原理分析和复杂决策。

## 核心理念

> **"I think the biggest mistake people make is not questioning the basic assumptions."** — Elon Musk

立足于第一性原理剖析问题，不被表象迷惑，追溯问题本质。

## 使用场景

| 场景 | 触发 |
|:---|:---|
| 架构设计 | Path B/C I阶段 |
| 方案对比 | 多个可行方案 |
| 技术选型 | 框架/库选择 |
| 问题诊断 | 难以直接解决的问题 |

## 第一性原理分析框架

```markdown
### 1. 问题本质
- 用户真正需要什么？（不是用户说的）
- 核心约束是什么？
- 什么是不可妥协的？

### 2. 分解问题
- 问题可以拆分为哪些子问题？
- 每个子问题的本质是什么？
- 哪些是核心，哪些是衍生？

### 3. 最简方案
- 解决核心问题的最简方案是什么？
- 是否有更简单的数据结构？
- 能否删除某些部分而不影响核心功能？

### 4. 验证假设
- 方案基于哪些假设？
- 这些假设成立吗？
- 如何验证？
```

## Linus 审查清单

```markdown
- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？能删除什么？
- [ ] **Compatibility**: 向后兼容？
- [ ] **Taste**: 这段代码有"味道"吗？
```

## 调用方式

```javascript
sequential_thinking({
  thought: "分析用户认证方案的本质需求...",
  thoughtNumber: 1,
  totalThoughts: 5,
  nextThoughtNeeded: true
})
```

## 多方案决策

```javascript
// 发现多个方案时
寸止.ask({
  question: "基于第一性原理分析，有两个可行方案",
  options: [
    "方案A: JWT + Redis — 本质：无状态+缓存",
    "方案B: Session + DB — 本质：有状态+持久化"
  ],
  analysis: "方案A更简单，但需要额外Redis；方案B更传统，数据库已有"
})
// 等待用户选择，禁止自行决定
```

## 思考模板

```markdown
## 第一性原理分析

### 问题
[一句话描述问题本质]

### 约束
1. [约束1]
2. [约束2]

### 分解
1. 子问题1 → 本质是...
2. 子问题2 → 本质是...

### 方案
最简方案: [描述]
理由: [为什么这是最简的]

### Linus检查
- [x] 数据结构最简
- [x] 无过度设计
- [ ] 需要用户确认...
```

## 降级方案

sequential-thinking不可用时 → 使用结构化Markdown分析
