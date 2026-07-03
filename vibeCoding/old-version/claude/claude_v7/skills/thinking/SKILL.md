---
name: thinking
description: 深度推理，复杂决策和架构设计
mcp_tool: sequential-thinking
---

# Thinking Skill (Sequential Thinking)

深度推理引擎，用于复杂问题分析和架构决策。

## 使用场景

| 场景 | 触发 |
|:---|:---|
| 架构设计 | Path C |
| 方案对比 | 多个可行方案 |
| 技术选型 | 框架/库选择 |
| 复杂问题分析 | 难以直接解决的问题 |

## 调用方式

```javascript
sequential_thinking({
  thought: "分析用户认证方案...",
  thoughtNumber: 1,
  totalThoughts: 5,
  nextThoughtNeeded: true
})
```

## Linus 审查清单 (Torvalds' Test)

每次深度思考后必须检查：

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？
- [ ] **Compatibility**: 向后兼容？

## I阶段（创新）标准流程

```
1. 使用 sequential-thinking 深度推演
2. 应用 Linus 审查清单
3. 若存在 >= 2 个可行方案:
   → 调用 寸止 展示选项
   → 等待用户选择
   → 禁止自作主张
```

## 多方案决策模板

```javascript
// 发现多个方案时
寸止.ask({
  question: "发现两个可行方案",
  options: [
    "方案A: JWT + Redis 缓存，性能高，复杂度中",
    "方案B: Session + DB，简单，性能一般"
  ]
})
// 等待用户选择，禁止自行决定
```

## 降级方案

sequential-thinking不可用时 → 使用 Extended Thinking 模式
