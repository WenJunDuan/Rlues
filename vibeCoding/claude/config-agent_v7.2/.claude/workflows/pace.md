# P.A.C.E. Complexity Router

## 任务分级逻辑

在任务开始前，评估以下指标选择执行路径。

---

## ⚡ Path A (Simple) - "Just Fix It"

### 条件
- 单文件修改
- <30行代码
- 纯Bug修复或文档

### 流程
```
LD (Execute) → Verify → Commit
```

### 寸止时机
- 无需寸止（验证通过直接完成）

### 示例
```markdown
用户: "修复登录按钮点击无反应"
→ Path A
→ sou搜索相关代码
→ codex修复
→ 验证
→ 完成
```

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

### 寸止时机
- `[PLAN_READY]` - 计划完成
- `[TASK_DONE]` - 任务完成

### 示例
```markdown
用户: "添加用户注册功能"
→ Path B
→ PM拆解任务
→ [PLAN_READY] 等待确认
→ LD执行
→ QE审查
→ [TASK_DONE]
```

---

## 🏗️ Path C (Hard) - "System Design"

### 条件
- >10个文件
- 架构变更
- 从0到1的新系统

### 流程
```
PDM (需求) → [PLAN_READY]
           → UI + AR (设计) → [DESIGN_FREEZE]
           → PM (任务分解) → [PLAN_READY]
           → LD (Execute Loop) → [PRE_COMMIT]
           → QE + SA (Review) → [TASK_DONE]
```

### 寸止时机
- 每个阶段结束
- 每个Phase完成
- 重大决策点

### 示例
```markdown
用户: "设计微服务认证系统"
→ Path C
→ PDM澄清需求 → [PLAN_READY]
→ AR设计架构 → [DESIGN_FREEZE]
→ PM分解任务 → [PLAN_READY]
→ LD执行Phase1 → [PRE_COMMIT]
→ QE+SA审查 → [TASK_DONE]
```

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
收到任务
    ↓
评估四个维度
    ↓
计算综合分数
    ↓
┌─────────────────────────────────┐
│ 1-3分 → Path A                  │
│ 4-6分 → Path B                  │
│ 7-10分 → Path C                 │
└─────────────────────────────────┘
    ↓
加载对应角色和技能
```

## 用户覆盖

用户可显式指定：

```markdown
"用完整RIPER" → 强制Path C
"快速修复" → 强制Path A
"简化流程" → 强制Path B
```
