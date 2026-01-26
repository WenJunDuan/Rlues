---
name: task-manager
description: WBS任务管理，Path B/C规划阶段
mcp_tool: shrimp-task-manager
---

# Task Manager Skill (Shrimp)

WBS任务管理，用于Path B/C的规划阶段。

## 使用场景

| Path | 使用 |
|:---|:---|
| Path A | 不使用 |
| Path B | 生成任务清单 |
| Path C | 分阶段WBS + 里程碑 |

## 核心操作

### 创建任务
```javascript
shrimp.create_task({
  name: "实现用户认证",
  description: "JWT登录API",
  priority: "high",
  dependencies: []
})
```

### 更新进度
```javascript
shrimp.update_task({
  id: "task-1",
  status: "completed"
})
```

### 查看任务
```javascript
shrimp.list_tasks()
shrimp.get_task("task-1")
```

## P阶段（计划）标准流程

```
1. 生成 WBS 任务清单
2. 调用 寸止 展示数据结构变更
3. 等待用户批准
4. 禁止未批准开始编码
```

## 任务清单模板

```markdown
## 任务清单

| ID | 任务 | 依赖 | 预估 | 状态 |
|:---|:---|:---|:---|:---|
| task-1 | 数据模型定义 | - | 1h | ⏳ |
| task-2 | API接口实现 | task-1 | 2h | ⏳ |
| task-3 | 前端页面 | task-2 | 2h | ⏳ |
```

## Path C 阶段划分

```
Phase 1: 基础架构
  - task-1: 数据模型
  - task-2: 核心接口
  → 寸止: 阶段验收

Phase 2: 功能实现
  - task-3: 业务逻辑
  - task-4: 前端集成
  → 寸止: 阶段验收

Phase 3: 完善优化
  - task-5: 错误处理
  - task-6: 性能优化
  → 寸止: 最终验收
```

## 降级方案

shrimp-task-manager不可用时 → 使用 Markdown Checklist
