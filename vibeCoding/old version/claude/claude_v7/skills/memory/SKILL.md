---
name: memory
description: 项目记忆管理，跨会话持久化
mcp_tool: memory
---

# Memory Skill

项目记忆管理，跨会话持久化上下文和决策。

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

### 搜索 (Search)
```javascript
memory.search_nodes("认证方案")
```

### 建立关系 (Relate)
```javascript
memory.create_relations([{
  from: "auth_module",
  to: "jwt_implementation",
  relationType: "uses"
}])
```

## Category 分类

| 类型 | 用途 | 示例 |
|:---|:---|:---|
| `rule` | 项目规则 | "禁止使用 any 类型" |
| `preference` | 用户偏好 | "偏好函数式编程风格" |
| `pattern` | 常见模式 | "错误处理统一使用 Result 类型" |
| `context` | 项目背景 | "这是一个 SaaS 后台管理系统" |

## 记忆固化时机

### R2阶段（仅重要变更）
```javascript
memory.add({
  content: "<简洁描述>",
  category: "rule|preference|pattern|context"
})
```

### 用户明确要求
```
用户: "请记住我偏好使用Tailwind"
→ memory.add({ content: "用户偏好使用Tailwind CSS", category: "preference" })
```

## 降级方案

memory不可用时 → 使用本地 Markdown 笔记记录
