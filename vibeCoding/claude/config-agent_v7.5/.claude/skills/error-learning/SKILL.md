---
name: error-learning
description: 错误学习系统，从Bug和错误中学习并记忆
trigger: 验证失败时自动加载
---

# Error Learning Skill

> **从错误中学习是最有效的成长方式**
> 每个 Bug 都是一次学习机会

---

## 🎯 核心使命

1. **识别错误** — 发现代码中的问题
2. **分析原因** — 深入理解为什么出错
3. **总结教训** — 提炼可复用的经验
4. **记忆固化** — 写入 Memory MCP，避免重复

---

## 🔄 错误学习流程

```
错误发生 → 识别类型 → 分析原因 → 修复验证 → 总结教训 → 写入Memory
```

### Step 1: 识别错误类型

| 类型 | 特征 | 示例 |
|:---|:---|:---|
| **编译错误** | TypeScript/ESLint 报错 | 类型不匹配 |
| **运行时错误** | 执行时崩溃 | undefined 访问 |
| **逻辑错误** | 结果不符合预期 | 边界条件遗漏 |
| **性能问题** | 响应慢/内存高 | N+1 查询 |
| **安全漏洞** | 安全检查发现 | SQL 注入 |

### Step 2: 分析原因

```markdown
## 错误分析

### 现象
[描述错误表现]

### 根因（5 Why分析）
1. Why: 为什么报错？→ 变量是 undefined
2. Why: 为什么是 undefined？→ 异步没等待
3. Why: 为什么没等待？→ 忘加 await
4. Why: 为什么会忘？→ 没有严格检查
5. Why: 根本原因 → **缺乏 async/await 规范检查**

### 直接原因
[直接导致错误的代码]

### 深层原因
[设计/流程/习惯层面的问题]
```

### Step 3: 修复验证

```
修复 → 本地验证 → 回归测试 → 确认修复
```

### Step 4: 总结教训

```markdown
## 教训总结

### 问题
[简述问题]

### 教训
[提炼的经验]

### 预防措施
1. [措施1]
2. [措施2]

### 检查清单更新
- [ ] [新增检查项]
```

### Step 5: 写入 Memory

```javascript
memory.add({
  category: "lesson_learned",
  content: "异步函数调用必须检查是否需要 await，漏掉 await 会导致 undefined",
  tags: ["async", "await", "undefined"],
  severity: "high",
  date: "2025-01-11"
})
```

---

## 📚 常见错误教训库

### 1. 空值相关

```javascript
// 教训: 访问属性前必须检查
memory.add({
  category: "lesson_learned",
  content: "对象属性访问前必须检查是否存在，使用可选链 ?. 或提前判断",
  tags: ["null", "undefined", "optional_chaining"]
})

// ❌ 错误
const name = user.profile.name;

// ✅ 正确
const name = user?.profile?.name ?? 'Unknown';
```

### 2. 异步相关

```javascript
// 教训: 循环中不要直接 await
memory.add({
  category: "lesson_learned",
  content: "循环中使用 await 会串行执行，应使用 Promise.all 并行",
  tags: ["async", "loop", "performance"]
})

// ❌ 错误
for (const id of ids) {
  await fetchUser(id);
}

// ✅ 正确
await Promise.all(ids.map(id => fetchUser(id)));
```

### 3. 类型相关

```javascript
// 教训: 不要用 any
memory.add({
  category: "lesson_learned",
  content: "使用 any 会丢失类型检查，后续出错难以追踪",
  tags: ["typescript", "any", "type_safety"]
})
```

### 4. 边界条件

```javascript
// 教训: 考虑空数组
memory.add({
  category: "lesson_learned",
  content: "数组操作要考虑空数组情况，如 arr[0] 在空数组时是 undefined",
  tags: ["array", "boundary", "empty"]
})
```

---

## 🔍 错误检测清单

每次验证时检查：

### 空值检查
- [ ] 对象属性访问是否安全？
- [ ] 数组是否可能为空？
- [ ] 函数参数是否可能为 null/undefined？

### 异步检查
- [ ] await 是否遗漏？
- [ ] 并行操作是否正确？
- [ ] 错误是否被捕获？

### 类型检查
- [ ] 是否有 any 类型？
- [ ] 类型转换是否安全？
- [ ] 泛型是否正确？

### 边界检查
- [ ] 空字符串？
- [ ] 空数组？
- [ ] 零值？
- [ ] 负数？

---

## 📊 错误统计

定期分析错误模式：

```markdown
## 错误统计 (本月)

| 类型 | 次数 | 占比 |
|:---|:---|:---|
| 空值错误 | 5 | 35% |
| 异步错误 | 3 | 21% |
| 类型错误 | 4 | 29% |
| 其他 | 2 | 15% |

### 趋势
- 空值错误仍然最多，需要加强检查
- 异步错误在减少（之前的教训起作用了）

### 行动
- 添加 ESLint 规则检查可选链
```

---

## 🔗 与其他技能协作

| 技能 | 协作方式 |
|:---|:---|
| `verification` | 验证失败时触发错误学习 |
| `memory` | 教训写入 Memory MCP |
| `code-simplifier` | 根据教训优化代码检查 |
| `qe` | 审查时应用教训清单 |

---

## ⚡ 自动触发

当以下情况发生时自动加载：

1. **验证失败** — 测试不通过
2. **编译错误** — TypeScript 报错
3. **用户报告 Bug** — 用户说有问题
4. **回滚发生** — 代码被撤销

---

**核心价值**: 不重复犯同样的错误 | **输出**: Memory 教训记录 | **触发**: 错误发生时
