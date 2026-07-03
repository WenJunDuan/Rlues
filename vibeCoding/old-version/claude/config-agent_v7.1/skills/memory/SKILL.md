---
name: memory
description: 项目记忆管理，跨会话持久化
mcp_tool: memory
---

# Memory Skill

项目记忆管理，跨会话持久化上下文和决策。

## 核心理念

> **事实为本**: 记忆中只存储事实和决策，不存储假设

## 自动触发

| 触发条件 | 动作 |
|:---|:---|
| 对话开始 | `memory.recall(project_path)` |
| 用户说 "请记住：xxx" | 总结后 `memory.add(content, category)` |
| 重要决策完成 | `memory.add` 存储决策 |
| 发现重复模式 | `memory.add(category: "pattern")` |

## 核心操作

### 回忆 (Recall)
```javascript
// 会话开始时必须调用
memory.recall({
  project_path: "/path/to/project"
})
```

### 记忆 (Add)
```javascript
memory.add({
  content: "项目使用 Result 类型处理错误",
  category: "pattern"  // rule|preference|pattern|context
})
```

## Category 分类

| 类型 | 用途 | 示例 |
|:---|:---|:---|
| `rule` | 项目规则 | "禁止使用 any 类型" |
| `preference` | 用户偏好 | "偏好函数式编程风格" |
| `pattern` | 常见模式 | "错误处理统一使用 Result 类型" |
| `context` | 项目背景 | "这是一个 SaaS 后台管理系统" |

## 记忆原则

### 什么值得记忆
- 用户明确的偏好
- 项目的技术决策
- 发现的代码模式
- 重要的设计选择

### 什么不记忆
- 临时的实现细节
- 可以从代码推断的信息
- 过于具体的上下文

## 降级方案

memory不可用时 → 使用本地 Markdown 笔记记录
