# vibe-plan

微任务拆解。触发 RIPER-7 P 阶段。

## 语法

```
vibe-plan "任务描述"
```

## 用户体验

```
你: vibe-plan "实现购物车功能"

系统:
  1. 搜索相关代码 + 知识库
  2. 拆解微任务 (每个 2-5 分钟):
     [TASK-1] 写 CartItem 类型定义       | 3min
     [TASK-2] 写 useCart hook 测试 (RED)  | 3min
     [TASK-3] 实现 useCart hook (GREEN)   | 5min
     ...
  3. → plan.md + todo.md
  4. [寸止] 确认计划
```

无 decisions.md 时自动先触发 R+D 阶段。
