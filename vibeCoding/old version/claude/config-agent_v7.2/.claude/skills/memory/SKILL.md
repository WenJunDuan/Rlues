---
name: memory
description: 记忆管理，但文件系统是唯一真理
mcp_tool: memory
---

# Memory Skill

项目记忆管理。但记住：**文件系统是唯一的真理**。

## 异步意识

> 你只是并发运行的多个AI会话中的一个。不要依赖你的内存。

## 双重持久化

### 1. MCP Memory
```javascript
memory.recall({ project_path: "/path/to/project" })
memory.add({ content: "...", category: "rule" })
```

### 2. 文件系统 (.ai_state/)
```
.ai_state/
├── active_context.md   # 当前任务状态
├── conventions.md      # 项目约定
└── decisions.md        # 决策记录
```

**优先级**: 文件系统 > MCP Memory

## 启动协议

```
1. 读取 .ai_state/active_context.md
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

| 类型 | 用途 | 示例 |
|:---|:---|:---|
| `rule` | 项目规则 | "禁止使用any" |
| `preference` | 用户偏好 | "函数式风格" |
| `pattern` | 常见模式 | "Result类型" |
| `context` | 项目背景 | "SaaS后台" |

## 降级

memory不可用 → 完全依赖 .ai_state 文件
