# Path A: Quick Fix (快速修复)

> 适用：单文件 / <30行 / Bug修复 / 小调整

---

## 流程图

```
开始 → 创建 session.lock
     ↓
生成 TODO（即使只有1项）
     ↓
更新 kanban（→TODO栏）
     ↓
执行任务（TODO→DOING→DONE）
     ↓
核对 TODO
     ↓
寸止 [TASK_DONE]（调用 cunzhi）
     ↓
用户确认 → 删除 session.lock → 结束
```

---

## 必须步骤

### 1. 初始化
```bash
# 创建会话锁
echo '{"mode":"workflow","type":"path_a"}' > .ai_state/session.lock
```

### 2. 生成 TODO
```markdown
- [ ] T-001: [任务描述]
  - **文件**: [文件路径]
  - **预估**: [时间]
  - **验收**: [验收标准]
```

### 3. 更新 kanban
```
T-001 → TODO栏 → DOING栏 → DONE栏
```

### 4. 执行
```
加载 skills/execute.md 执行
```

### 5. 核对 + 寸止
```
调用 cunzhi MCP（降级用 mcp-feedback）

输出核对结果，等待用户确认
```

---

## 检查清单

- [ ] session.lock 已创建
- [ ] TODO 已生成（即使只有1项）
- [ ] kanban 已更新
- [ ] 已调用寸止
- [ ] 用户确认后 session.lock 已删除
