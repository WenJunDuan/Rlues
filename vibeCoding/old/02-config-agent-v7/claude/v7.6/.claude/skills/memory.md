# Memory 系统

> 双轨分离：项目状态 → .ai_state/ | 通用知识 → Memory MCP

---

## 双轨架构

```
项目状态 (.ai_state/)          通用知识 (Memory MCP)
──────────────────────         ──────────────────────
✅ session.lock                ✅ user_preference
✅ active_context.md           ✅ forbidden_action
✅ kanban.md                   ✅ code_pattern
✅ conventions.md              ✅ lesson_learned
✅ decisions.md                ✅ high_freq_action
```

---

## Memory 分类

| Category | 用途 | 示例 |
|:---|:---|:---|
| `user_preference` | 用户偏好 | 代码风格、工具选择 |
| `forbidden_action` | 禁止动作 | 用户说不要做的 |
| `code_pattern` | 代码模式 | 常用设计模式 |
| `lesson_learned` | 错误教训 | 从Bug中学到的 |
| `high_freq_action` | 高频动作 | 常用操作 |

---

## 写入 Memory

```javascript
// 记录用户偏好
memory.add({
  category: "user_preference",
  content: "用户偏好 TypeScript strict 模式",
  tags: ["typescript", "config"]
})

// 记录禁止动作（用户纠正时立即执行）
memory.add({
  category: "forbidden_action",
  content: "不要使用 any 类型",
  tags: ["typescript", "user_correction"]
})

// 记录代码模式
memory.add({
  category: "code_pattern",
  content: "项目使用 Repository Pattern 访问数据",
  tags: ["architecture", "pattern"]
})

// 记录错误教训
memory.add({
  category: "lesson_learned",
  content: "异步函数要处理 Promise rejection",
  tags: ["async", "error_handling"]
})
```

---

## 读取 Memory

```javascript
// 启动时加载
const prefs = await memory.recall({ category: "user_preference" })
const forbidden = await memory.recall({ category: "forbidden_action" })
const patterns = await memory.recall({ category: "code_pattern" })
const lessons = await memory.recall({ category: "lesson_learned" })
```

---

## 禁止动作检查

```javascript
// 每个任务执行前
async function checkForbidden(task) {
  const forbidden = await memory.recall({ category: "forbidden_action" })
  
  for (const rule of forbidden) {
    if (taskViolates(task, rule)) {
      throw new Error(`违反禁止规则: ${rule.content}`)
    }
  }
}
```

---

## 自动记录时机

| 时机 | 记录内容 | Category |
|:---|:---|:---|
| 用户说"不要xxx" | 禁止动作 | forbidden_action |
| 发现可复用模式 | 代码模式 | code_pattern |
| 修复了Bug | 错误教训 | lesson_learned |
| 重复操作>3次 | 高频动作 | high_freq_action |
| 用户表达偏好 | 用户偏好 | user_preference |
