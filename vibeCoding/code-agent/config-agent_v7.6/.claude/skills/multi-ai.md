# Multi-AI 协调

> 多 AI 协作是未来趋势，通过文件系统实现状态共享

---

## 支持的引擎

| 引擎 | 用途 | 触发方式 |
|:---|:---|:---|
| Claude | 默认执行 | 直接执行 |
| Codex | 快速编码 | `--engine=codex` |
| Gemini | 大上下文 | `--engine=gemini` |

---

## 协调机制

```
                    .ai_state/
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    Claude          Codex           Gemini
        │               │               │
        └───────────────┴───────────────┘
                        │
                   共享状态文件
```

---

## 状态文件格式

### session.lock
```json
{
  "mode": "workflow",
  "workflow_id": "WF-001",
  "current_engine": "claude",
  "phase": "EXECUTE",
  "resume_point": "T-003",
  "updated_at": "2025-01-13T10:00:00Z"
}
```

### handoff.md
```markdown
# AI 交接记录

## 最近交接
| 时间 | 从 | 到 | 任务 |
|:---|:---|:---|:---|
| 10:00 | Claude | Codex | T-003 编码 |

## 当前状态
- 进度: 2/5
- 当前任务: T-003
- 未完成: T-003, T-004, T-005

## 注意事项
- 用户偏好 strict 模式
- 禁止使用 any 类型
```

---

## 引擎切换流程

```javascript
// 切换到 Codex
async function switchToCodex(task) {
  // 1. 更新 session.lock
  await updateSessionLock({
    current_engine: 'codex',
    handoff_at: new Date()
  })
  
  // 2. 更新 handoff.md
  await updateHandoff({
    from: 'claude',
    to: 'codex',
    task: task,
    context: getCurrentContext()
  })
  
  // 3. 调用 Codex
  // (实际调用方式取决于环境)
}
```

---

## 引擎特点

### Claude
- 擅长：复杂推理、设计决策
- 适用：R1, I, P, R2 阶段

### Codex
- 擅长：快速编码、代码补全
- 适用：E 阶段简单任务

### Gemini
- 擅长：大文件分析
- 适用：大规模代码审查

---

## 交接检查清单

- [ ] session.lock 已更新
- [ ] handoff.md 已更新
- [ ] 当前上下文已记录
- [ ] 用户偏好已传递
- [ ] 禁止动作已传递
