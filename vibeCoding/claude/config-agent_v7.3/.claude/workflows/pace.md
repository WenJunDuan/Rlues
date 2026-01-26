# P.A.C.E. Complexity Router

## 任务分级逻辑

在任务开始前，评估指标选择执行路径。

---

## ⚡ Path A (Simple) - "Just Fix It"

### 条件
- 单文件修改
- <30行代码
- 纯Bug修复或文档

### 流程
```
LD (Execute) → Verify → Done
```

### 寸止
- 无需寸止（验证通过直接完成）

---

## 🤝 Path B (Medium) - "Plan First"

### 条件
- 2-10个文件
- 新增功能
- 局部重构

### 流程
```
PM (Plan) → [PLAN_READY] → 用户确认
          → LD (Execute) → Verify
          → QE (Review) → [TASK_DONE]
```

### 寸止
- `[PLAN_READY]` - 计划完成
- `[TASK_DONE]` - 任务完成

---

## 🏗️ Path C (Hard) - "System Design + Step-by-Step"

### 条件
- >10个文件
- 架构变更
- 从0到1的新系统

### 流程
```
PDM (需求) → [PLAN_READY]
           → AR (设计) + 逐步思考 → [DESIGN_FREEZE]
           → PM (任务分解) → [PLAN_READY]
           → LD (Execute Loop) → [PRE_COMMIT]
           → QE + SA (Review) → [TASK_DONE]
```

### 🧠 逐步思考协议 (Path C 必须)

**对于复杂模块化开发，必须启用逐步思考：**

```markdown
## Step-by-Step Thinking Protocol

### 1. 问题分解
将大问题拆解为小问题：
- 子问题1: [描述]
- 子问题2: [描述]
- 依赖关系: 1 → 2 → 3

### 2. 逐步推理
一步一步思考，每步都要验证：

**Step 1: [子问题1]**
- 思考: ...
- 结论: ...
- 验证: ✅

**Step 2: [子问题2]**
- 思考: ...
- 结论: ...
- 验证: ✅

### 3. 阶段验收
每个Phase完成后寸止确认：
- Phase 1完成 → [PRE_COMMIT] → 用户确认
- Phase 2完成 → [PRE_COMMIT] → 用户确认

### 4. 决策记录
重要决策写入 project_document/.ai_state/decisions.md
```

### 寸止
- 每个阶段结束
- 每个Phase完成
- 重大决策点

---

## 评估维度

| 维度 | 低(1-3) | 中(4-6) | 高(7-10) |
|:---|:---|:---|:---|
| 文件数 | 1个 | 2-10个 | >10个 |
| 代码量 | <30行 | 30-300行 | >300行 |
| 时间 | <30分钟 | 30分-4小时 | >4小时 |
| 架构影响 | 无 | 局部 | 全局 |

## 决策流程

```
收到任务 → 评估四维度 → 计算分数
                         ↓
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
      1-3分           4-6分           7-10分
      Path A          Path B          Path C
         ↓               ↓               ↓
      静默执行        计划先行      逐步思考+分阶段
```

## 用户覆盖

```bash
/vibe-code --path=C "任务"  # 强制Path C + 逐步思考
/vibe-code --path=A "任务"  # 强制Path A 静默执行
```
