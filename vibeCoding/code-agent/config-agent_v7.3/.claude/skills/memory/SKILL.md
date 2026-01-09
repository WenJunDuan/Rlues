---
name: memory
description: 记忆管理，文件系统是唯一真理
mcp_tool: memory
---

# Memory Skill

项目记忆管理。**文件系统是唯一的真理**。

## 异步意识

> 你只是并发运行的多个AI会话之一。不要依赖会话记忆。

## 双重持久化

### 1. MCP Memory
```javascript
memory.recall({ project_path: "/path/to/project" })
memory.add({ content: "...", category: "rule" })
```

### 2. 文件系统 (优先)
```
project_document/.ai_state/
├── active_context.md   # 当前任务
├── conventions.md      # 项目约定
└── decisions.md        # 决策记录
```

## 启动协议

```
1. 读取 project_document/.ai_state/active_context.md
2. memory.recall(project_path)
3. 汇报当前状态
```

## 结束协议

```
1. 更新任务状态
2. memory.add 重要决策
3. 保存到 .ai_state/
```

## Category分类

| 类型 | 用途 |
|:---|:---|
| `rule` | 项目规则 |
| `preference` | 用户偏好 |
| `pattern` | 常见模式 |
| `context` | 项目背景 |

## 降级

memory不可用 → 完全依赖 .ai_state 文件
