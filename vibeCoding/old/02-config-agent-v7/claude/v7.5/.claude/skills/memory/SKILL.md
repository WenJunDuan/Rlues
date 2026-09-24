---
name: memory
description: 记忆管理系统，分离项目状态与通用知识
mcp_tool: memory
---

# Memory Skill (Enhanced v7.5)

> **双轨记忆**: 项目状态 → 文件系统 | 通用知识 → Memory MCP
> **异步意识**: 你只是并发运行的多个AI会话之一

---

## 🧠 记忆架构

```
┌─────────────────────────────────────────────────────────────┐
│                      记忆系统架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────┐    │
│  │  项目状态 (Project) │    │  通用知识 (Universal)   │    │
│  │                     │    │                         │    │
│  │  .ai_state/         │    │  Memory MCP             │    │
│  │  ├── active_context │    │  ├── code_pattern      │    │
│  │  ├── kanban         │    │  ├── user_preference   │    │
│  │  ├── handoff        │    │  ├── forbidden_action  │    │
│  │  └── decisions      │    │  ├── high_freq_action  │    │
│  │                     │    │  └── lesson_learned    │    │
│  │  每个项目独立       │    │  跨项目共享            │    │
│  └─────────────────────┘    └─────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目状态 (Project-Specific)

**存储位置**: `project_document/.ai_state/`

**只记录当前项目相关的内容**:

| 文件 | 内容 |
|:---|:---|
| `active_context.md` | 当前任务、TODO列表、进度 |
| `kanban.md` | 项目进度看板 |
| `handoff.md` | AI交接记录 |
| `decisions.md` | 项目技术决策 |
| `conventions.md` | 项目特定约定 |

**不要放在 .ai_state 的内容**:
- ❌ 通用编码规范（放 Memory）
- ❌ 用户偏好（放 Memory）
- ❌ 高频动作（放 Memory）
- ❌ 错误教训（放 Memory）

---

## 🌐 通用知识 (Universal - Memory MCP)

**存储位置**: Memory MCP

**跨项目共享的知识**:

### 1. 高频动作 (high_freq_action)

```javascript
// 记录用户常用的操作模式
memory.add({
  category: "high_freq_action",
  content: "用户习惯先写接口再实现，TDD风格",
  tags: ["workflow", "tdd"]
})

memory.add({
  category: "high_freq_action", 
  content: "用户喜欢用 zod 做运行时类型验证",
  tags: ["typescript", "validation"]
})
```

### 2. 用户偏好 (user_preference)

```javascript
// 记录用户的偏好设置
memory.add({
  category: "user_preference",
  content: "偏好函数式编程风格，避免class",
  tags: ["style", "functional"]
})

memory.add({
  category: "user_preference",
  content: "代码注释用中文",
  tags: ["style", "comment"]
})
```

### 3. 禁止动作 (forbidden_action) ⚠️

```javascript
// 用户明确指出不该做的事情
memory.add({
  category: "forbidden_action",
  content: "禁止使用 moment.js，用 dayjs 替代",
  tags: ["library", "date"]
})

memory.add({
  category: "forbidden_action",
  content: "禁止在循环中使用 await，要用 Promise.all",
  tags: ["async", "performance"]
})

memory.add({
  category: "forbidden_action",
  content: "不要自动添加 console.log，用户会自己加",
  tags: ["debug", "logging"]
})
```

### 4. 代码模式 (code_pattern)

```javascript
// 记录常用的代码模式
memory.add({
  category: "code_pattern",
  content: "错误处理统一用 Result<T, E> 模式",
  tags: ["error", "pattern"]
})

memory.add({
  category: "code_pattern",
  content: "API响应统一格式: { success, data, error }",
  tags: ["api", "response"]
})
```

### 5. 错误教训 (lesson_learned)

```javascript
// 从错误中学习
memory.add({
  category: "lesson_learned",
  content: "上次因为没检查 null 导致线上 bug，以后必须做空值检查",
  tags: ["bug", "null_check"]
})

memory.add({
  category: "lesson_learned",
  content: "异步操作要考虑竞态条件",
  tags: ["async", "race_condition"]
})
```

### 6. 简化模式 (simplification)

```javascript
// 代码简化经验
memory.add({
  category: "simplification",
  content: "超过3层嵌套时使用早返回模式",
  tags: ["refactor", "nesting"]
})
```

---

## 🔄 记忆生命周期

### 启动时加载

```javascript
async function onSessionStart(projectPath) {
  // 1. 加载项目状态
  const context = await readFile(`${projectPath}/.ai_state/active_context.md`);
  
  // 2. 加载通用知识
  const preferences = await memory.recall({ category: "user_preference" });
  const forbidden = await memory.recall({ category: "forbidden_action" });
  const patterns = await memory.recall({ category: "code_pattern" });
  
  // 3. 应用到当前会话
  applyKnowledge({ preferences, forbidden, patterns });
}
```

### 执行中学习

```javascript
// 用户纠正时记录
function onUserCorrection(correction) {
  if (correction.type === 'forbidden') {
    memory.add({
      category: "forbidden_action",
      content: correction.content,
      tags: correction.tags
    });
  }
}

// 发现好模式时记录
function onPatternDiscovered(pattern) {
  memory.add({
    category: "code_pattern",
    content: pattern.description,
    tags: pattern.tags
  });
}
```

### 结束时保存

```javascript
async function onSessionEnd(projectPath) {
  // 1. 保存项目状态到文件
  await saveFile(`${projectPath}/.ai_state/active_context.md`, context);
  
  // 2. 通用知识已实时保存到 Memory MCP
  // 无需额外操作
}
```

---

## 📋 Memory 分类索引

| Category | 用途 | 示例 |
|:---|:---|:---|
| `user_preference` | 用户偏好 | 代码风格、工具选择 |
| `forbidden_action` | 禁止动作 | 用户明确说不要做的 |
| `high_freq_action` | 高频动作 | 常用操作模式 |
| `code_pattern` | 代码模式 | 常用设计模式 |
| `lesson_learned` | 错误教训 | 从Bug中学到的 |
| `simplification` | 简化经验 | 代码简化技巧 |
| `tool_usage` | 工具用法 | MCP工具使用技巧 |

---

## 🛡️ 禁止动作检查

**每次执行前检查 forbidden_action**:

```javascript
async function beforeExecute(action) {
  const forbidden = await memory.recall({ category: "forbidden_action" });
  
  for (const rule of forbidden) {
    if (violates(action, rule)) {
      console.warn(`⚠️ 禁止动作: ${rule.content}`);
      return false;
    }
  }
  return true;
}
```

---

## 🔍 记忆查询

```javascript
// 查询用户偏好
memory.recall({ category: "user_preference" })

// 查询禁止动作
memory.recall({ category: "forbidden_action" })

// 查询特定标签
memory.recall({ category: "code_pattern", tags: ["api"] })

// 全局搜索
memory.recall({ query: "错误处理" })
```

---

## ⚠️ 重要提醒

### 项目状态 vs 通用知识

```
✅ 项目状态 (.ai_state/):
   - 当前任务 T-001, T-002
   - 项目进度 40%
   - 本项目的技术选型决策

❌ 不要放在 .ai_state/:
   - "用户喜欢函数式" ← 放 Memory
   - "禁止用 moment" ← 放 Memory
   - "常用早返回模式" ← 放 Memory
```

### 用户纠正必须记录

```
用户: "以后不要自动加 console.log"
AI: 好的，我记录下来了。

→ memory.add({
    category: "forbidden_action",
    content: "不要自动添加 console.log"
  })
```

---

## 📊 记忆统计

```markdown
## Memory 统计

| 类别 | 数量 |
|:---|:---|
| user_preference | 12 |
| forbidden_action | 8 |
| high_freq_action | 15 |
| code_pattern | 23 |
| lesson_learned | 6 |

最近添加:
- [今天] forbidden: 不要用 var
- [昨天] pattern: Result<T,E> 模式
```

---

**核心原则**: 项目状态放文件，通用知识放 Memory，用户纠正必记录
