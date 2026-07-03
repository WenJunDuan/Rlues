---
name: thinking
description: 深度推理，第一性原理分析
mcp_tool: sequential-thinking
---

# Thinking Skill

深度推理引擎，用于复杂问题的第一性原理分析。

## 核心理念

**第一性原理**: 不接受"因为别人这么做"的答案，追问本质。

```
1. 这个问题的本质是什么？
2. 去掉所有假设后，还剩什么？
3. 从零开始，最简方案是什么？
```

## 使用场景

- 架构设计（Path C）
- 多方案对比
- 技术选型
- 复杂问题分析

## 调用方式

```javascript
sequential_thinking({
  thought: "分析用户认证方案...",
  thoughtNumber: 1,
  totalThoughts: 5,
  nextThoughtNeeded: true
})
```

## Linus审查清单

每次深度思考后检查：

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？能删掉什么？
- [ ] **Taste**: 方案有"品味"吗？

## 多方案决策

```javascript
// 禁止自作主张
寸止.ask({
  question: "发现两个可行方案",
  options: [
    "方案A: JWT + Redis",
    "方案B: Session + DB"
  ]
})
```

## 降级

sequential-thinking不可用 → Extended Thinking模式
