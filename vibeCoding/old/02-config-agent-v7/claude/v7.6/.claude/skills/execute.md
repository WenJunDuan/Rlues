# E - EXECUTE (执行开发)

> 加载时机：RIPER 第四阶段 | 角色：LD

---

## 执行步骤（每个 TODO 重复）

### Step 1: 执行前检查
```
- [ ] 依赖任务已完成？（未完成则跳过）
- [ ] 检查 forbidden_action（违反则阻止）
- [ ] 加载相关代码上下文
```

### Step 2: 更新 kanban（TODO → DOING）
```markdown
## 🔄 DOING (进行中)
| ID | 任务 | 开始时间 | 进度 |
|:---|:---|:---|:---|
| T-001 | xxx | 10:30 | 0% |
```

### Step 3: 执行任务
```
代码质量要求：
- 函数 < 50 行
- 嵌套 < 3 层
- 无 any 类型
- 完整错误处理
- 输入验证

过程中更新进度：
| T-001 | xxx | 10:30 | 60% |
```

### Step 4: 验证
```
Execute → Verify → Pass?
                    │
              Yes ──┼── No
               ↓         ↓
           Step 5    Analyze → Fix → Retry (max 3)
                                         │
                                      Still Fail
                                         ↓
                              寸止 [VERIFICATION_FAILED]
                              请求人工介入
```

验证内容：
- [ ] 代码编译通过
- [ ] 相关测试通过
- [ ] 满足验收标准
- [ ] 无新增错误

### Step 5: 更新状态（DOING → DONE）
```markdown
## ✅ DONE (已完成)
| ID | 任务 | 用时 | 完成时间 |
|:---|:---|:---|:---|
| T-001 | xxx | 25min | 10:55 |
```

同时更新：
- kanban.md
- active_context.md（标记 [x]）
- 进度条

### Step 6: 学习沉淀
```javascript
// 发现新模式
IF (发现可复用模式) {
  memory.add({ category: "code_pattern", content: "..." })
}

// 修复了错误
IF (修复了Bug) {
  memory.add({ category: "lesson_learned", content: "..." })
}

// 发现高频操作
IF (重复操作 > 3次) {
  memory.add({ category: "high_freq_action", content: "..." })
}
```

---

## 产出物

- [ ] 修改后的代码文件
- [ ] kanban.md（DONE栏更新）
- [ ] active_context.md（任务标记完成）
- [ ] Memory 学习记录
- [ ] 验证日志

---

## 检查点（每个任务）

- [ ] 依赖已检查
- [ ] forbidden_action 已检查
- [ ] kanban 状态已更新（TODO→DOING→DONE）
- [ ] 代码符合质量要求
- [ ] 验证通过

---

## 完成后

所有 TODO 完成 → 进入 R2 阶段，加载 `skills/review.md`
