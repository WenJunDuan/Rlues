---
name: vibe-plan
aliases: ["/vp"]
description: 深度规划模式，生成WBS和风险评估
loads:
  agents: ["pdm", "pm"]
  skills: ["meeting/"]
  plugins: ["feature-dev"]
---

# /vibe-plan - 深度规划模式

> **Plan Mode Priority**: 绝不直接让开发写代码。先规划，再执行。

## 触发方式

```bash
/vibe-plan              # 完整规划
/vibe-plan --quick      # 快速规划（跳过风险评估）
/vp                     # 简写
```

## 工作流

```
需求澄清 → WBS分解 → 风险评估 → [PLAN_READY] → 用户确认
```

## 执行步骤

### 1. 状态同步
```
读取 project_document/.ai_state/active_context.md
memory.recall(project_path)
```

### 2. 需求澄清会议
```markdown
召集: PDM + PM
目标: 厘清所有疑点

议程:
1. 用户要解决什么问题？（第一性原理）
2. 功能边界在哪里？
3. 什么是"完成"的标准？
4. 有哪些约束？

产出: 用户故事 + 验收标准
```

### 3. WBS分解
```markdown
原则:
- 任务粒度 < 4小时
- 每个任务有明确验收标准
- 识别依赖关系
- MECE原则（互斥穷尽）
```

### 4. 风险评估
```markdown
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| R1 | 高 | 高 | [措施] |
```

### 5. 寸止点
```
输出 [PLAN_READY]
等待用户批准
```

## 输出模板

写入 `project_document/.ai_state/active_context.md`:

```markdown
# Active Context

## 🎯 当前目标
> [里程碑描述]

## 📋 Phase 1: [阶段名]

| ID | 任务 | Owner | 预估 | 依赖 | 状态 |
|:---|:---|:---|:---|:---|:---|
| T-001 | 数据模型 | LD | 1h | - | ⏳ |
| T-002 | API接口 | LD | 2h | T-001 | ⏳ |

## ⚠️ 风险清单
- R1: [风险] → [缓解]

## 📝 验收标准
- [ ] 标准1
- [ ] 标准2
```
