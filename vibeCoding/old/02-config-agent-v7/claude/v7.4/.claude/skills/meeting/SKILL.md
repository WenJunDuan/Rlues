---
name: meeting
description: 本地模拟会议，多角色协作
---

# Meeting Skill

通过模拟多角色会议进行任务分析、方案讨论和计划制定。

## 核心理念

**渐进式开发**: 在着手任何设计或编码前，必须完成前期调研并厘清所有疑点。

## 会议类型

### 1. 需求澄清会议

**参与者**: PM + PDM + 用户(via 寸止)

```markdown
## 需求澄清会议

### 1. 问题本质 (第一性原理)
- 用户要解决什么问题?
- 问题的根本原因是什么?

### 2. 功能边界
- Must Have: [必须]
- Nice to Have: [可选]
- Out of Scope: [不做]

### 3. 验收标准
- [ ] 标准1
- [ ] 标准2

### 📋 [PLAN_READY]
等待用户确认
```

### 2. 技术方案会议

**参与者**: AR + LD + SA

```markdown
## 技术方案会议

### 1. 问题分析 (第一性原理)
[分析]

### 2. 数据结构设计 (Data First)
[Interface定义]

### 3. 方案对比
| 维度 | 方案A | 方案B |
|------|-------|-------|
| Linus评分 | /5 | /5 |

### 📋 [DESIGN_FREEZE]
等待用户选择
```

### 3. 任务分解会议

**参与者**: PM + AR + LD

```markdown
## 任务分解会议

### 任务清单
| ID | 任务 | 依赖 | Owner | 预估 |
|----|------|------|-------|------|

### 📋 [PLAN_READY]
等待用户确认
```

### 4. 代码评审会议

**参与者**: AR + LD + QE + SA

```markdown
## 代码评审会议

### Linus审查
- [ ] Data First
- [ ] Simplicity
- [ ] Taste

### 问题清单
| 级别 | 位置 | 问题 |
|------|------|------|

### 📋 [REVIEW_DONE]
```

## 使用时机

| Path | 会议 |
|:---|:---|
| Path A | 不需要 |
| Path B | 技术方案 + 任务分解 |
| Path C | 全部会议 |

## 输出位置

所有会议结论写入 `project_document/.ai_state/active_context.md`
