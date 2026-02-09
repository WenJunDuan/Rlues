---
name: stop-hooks
description: 强制停止钩子，寸止协议实现
---

# Stop Hooks (寸止协议)

## 🛑 强制停止钩子

输出以下Token时**必须停止**，等待用户输入：

| Token | 触发条件 | 等待内容 |
|:---|:---|:---|
| `[PLAN_READY]` | 任务拆解完成 | 用户批准计划 |
| `[DESIGN_FREEZE]` | 接口定义完成 | 用户选择方案 |
| `[PRE_COMMIT]` | 大规模修改前 | 用户确认修改 |
| `[TASK_DONE]` | 任务完成 | 用户验收 |
| `[VERIFICATION_FAILED]` | 验证失败3次 | 用户介入 |

## 使用示例

### [PLAN_READY]
```markdown
## 任务计划

| ID | 任务 | 预估 |
|:---|:---|:---|
| T-001 | ... | 2h |

### 📋 [PLAN_READY]
请确认：`确认` / `修改` / `取消`
```

### [DESIGN_FREEZE]
```markdown
## 技术方案

### 方案A: ...
### 方案B: ...

### 📋 [DESIGN_FREEZE]
请选择：`A` / `B` / `讨论`
```

### [PRE_COMMIT]
```markdown
## 即将修改

- `src/auth/login.ts` (+50/-10)

### 📋 [PRE_COMMIT]
请确认：`确认` / `查看` / `取消`
```

### [TASK_DONE]
```markdown
## 任务完成

- [x] T-001 ✅
- [x] T-002 ✅

### 📋 [TASK_DONE]
请验收：`通过` / `问题` / `继续`
```

## 🚫 违规行为

1. 未经批准直接修改核心架构
2. 只有计划没有验证方案
3. 用户未反馈前连续自言自语超过3轮
4. 自作主张选择方案
5. 未经确认结束对话

## 状态记录

记录到 `project_document/.ai_state/hooks.log`
