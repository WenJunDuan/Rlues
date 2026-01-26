---
name: stop-hooks
description: 强制停止钩子，寸止协议实现
---

# Stop Hooks (寸止协议)

## 🛑 强制停止钩子

你必须在输出以下Token时**强制停止生成**，并等待用户输入：

| Token | 触发条件 | 等待内容 |
|:---|:---|:---|
| `[PLAN_READY]` | 任务拆解完成 | 用户批准计划 |
| `[DESIGN_FREEZE]` | 接口/架构定义完成 | 用户选择方案 |
| `[PRE_COMMIT]` | 代码即将写入（大规模修改） | 用户确认修改 |
| `[TASK_DONE]` | 所有任务完成 | 用户验收 |
| `[VERIFICATION_FAILED]` | 验证失败3次 | 用户介入 |

## 使用方式

### 计划完成
```markdown
## 任务计划

- [ ] T-001: ...
- [ ] T-002: ...

### 📋 [PLAN_READY]
请确认以上计划，输入以下命令继续：
- `确认` - 开始执行
- `修改` - 调整计划
- `取消` - 放弃计划
```

### 设计冻结
```markdown
## 技术方案

### 方案A: ...
### 方案B: ...

### 📋 [DESIGN_FREEZE]
请选择方案：
- `A` - 选择方案A
- `B` - 选择方案B
- `讨论` - 需要更多讨论
```

### 提交确认
```markdown
## 即将修改

- `src/auth/login.ts` (+50/-10)
- `src/auth/types.ts` (+20/-0)

### 📋 [PRE_COMMIT]
请确认以上修改：
- `确认` - 提交修改
- `查看` - 查看详细diff
- `取消` - 放弃修改
```

### 任务完成
```markdown
## 任务完成

- [x] T-001: 登录接口 ✅
- [x] T-002: Token验证 ✅

### 📋 [TASK_DONE]
请验收：
- `通过` - 验收通过
- `问题` - 存在问题
- `继续` - 继续下一阶段
```

### 验证失败
```markdown
## 验证失败

尝试次数: 3/3
失败原因: [描述]

### 📋 [VERIFICATION_FAILED]
需要人工介入：
- `重试` - 再试一次
- `跳过` - 暂时跳过
- `帮助` - 需要帮助
```

## 🚫 违规行为

以下行为**严格禁止**：

1. 未经批准直接修改核心架构
2. 只有计划没有验证方案
3. 在用户未反馈前连续自言自语超过3轮
4. 自作主张选择方案
5. 未经确认结束对话

## 与寸止MCP工具集成

```javascript
// 询问
寸止.ask({
  hook: "DESIGN_FREEZE",
  context: "技术方案选择",
  options: ["方案A", "方案B"]
})

// 确认
寸止.confirm({
  hook: "PRE_COMMIT",
  summary: "即将修改3个文件",
  changes: [...]
})

// 反馈
寸止.feedback({
  hook: "TASK_DONE",
  summary: "任务完成",
  results: [...]
})

// 升级
寸止.escalate({
  hook: "VERIFICATION_FAILED",
  issue: "验证失败",
  attempts: 3
})
```

## 状态记录

所有Stop Hook触发记录到 `.ai_state/hooks.log`:

```markdown
## Hook Log

### [日期] [PLAN_READY]
- 任务: 用户认证模块
- 状态: 等待确认
- 用户响应: 确认

### [日期] [DESIGN_FREEZE]
- 方案: A/B
- 状态: 等待选择
- 用户响应: 选择A
```
