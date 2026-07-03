---
name: thinking
description: 深度推理，逐步思考，第一性原理
mcp_tool: sequential-thinking
---

# Thinking Skill

深度推理引擎，支持**逐步思考**和**第一性原理**分析。

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

## 逐步思考协议 (Path C必须)

对于复杂模块化开发(Path C)，必须启用逐步思考：

### 🧠 Step-by-Step Thinking

```markdown
## 1. 问题分解
将大问题拆解为小问题：
- 子问题1: [描述]
- 子问题2: [描述]
- 依赖关系: 1 → 2

## 2. 逐步推理
一步一步思考：

### Step 1: [子问题1]
思考过程: ...
结论: ...
验证: ✅/❌

### Step 2: [子问题2]
思考过程: ...
结论: ...
验证: ✅/❌

## 3. 综合结论
基于以上步骤，结论是...

## 4. 决策记录
记录到 project_document/.ai_state/decisions.md
```

## 调用方式

### MCP工具调用
```javascript
sequential_thinking({
  thought: "分析用户认证方案...",
  thoughtNumber: 1,
  totalThoughts: 5,
  nextThoughtNeeded: true
})
```

### Path C自动触发
```bash
/vibe-code --path=C "重构认证系统"
# 自动启用逐步思考
```

## Linus审查清单

每次深度思考后检查：

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？
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

## 决策记录

重要决策写入 `project_document/.ai_state/decisions.md`：

```markdown
### ADR-001: 认证方案选择

**日期**: 2025-01-01
**状态**: 已采纳

**背景**: 需要实现用户认证

**逐步分析**:
1. Step 1: 分析需求 → 需要支持无状态
2. Step 2: 对比方案 → JWT更简单
3. Step 3: 验证可行性 → 满足需求

**决策**: 选择JWT方案

**理由**: 简单，无状态，满足需求
```

## 降级

sequential-thinking不可用 → Extended Thinking模式
