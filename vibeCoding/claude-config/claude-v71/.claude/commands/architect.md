---
description: 架构设计，第一性原理分析
---

# /architect - 架构设计

**触发词**: 架构、设计、技术选型、方案对比

## 核心理念

> **"Bad programmers worry about the code. Good programmers worry about data structures."** — Linus Torvalds

## 工作流

```
加载AR角色 → 第一性原理分析 → 数据结构设计 → 方案对比 → 寸止确认
```

## 执行步骤

### 1. 加载角色
```
promptx.switch("AR")
```

### 2. 第一性原理分析
```markdown
## 问题分析

### 用户需要什么？
[一句话描述本质需求]

### 核心约束
- [约束1]
- [约束2]

### 不可妥协的
- [...]
```

### 3. 数据结构设计（最重要）
```typescript
// 先设计数据，再考虑行为
interface User {
  id: string;
  email: string;
}
```

### 4. Linus审查
```markdown
- [ ] 数据结构是最简的吗？
- [ ] 每个字段都必要吗？
- [ ] 命名准确吗？
- [ ] 是否过度设计？
```

### 5. 方案对比
```markdown
| 维度 | 方案A | 方案B |
|:---|:---|:---|
| 复杂度 | 低 | 中 |
| 数据结构 | 简单 | 复杂 |
| YAGNI | ✅ | ❌ |
```

### 6. 寸止确认
```
多方案 → 寸止让用户选择
禁止自作主张
```

## 注意

此命令专注于设计，**不生成代码**。实现请用 /dev 或 /quick
