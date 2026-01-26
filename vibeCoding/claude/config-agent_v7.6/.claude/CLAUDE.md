# VibeCoding Kernel v7.6

> **"Talk is cheap. Show me the code."** — Linus Torvalds

---

## 🔴 铁律（必须遵守，无例外）

1. **启动必检查** → 读取 `.ai_state/session.lock`，有则恢复，无则新建
2. **任务必TODO** → 任何任务开始前生成 TODO 列表
3. **执行必更新** → 状态变化实时同步 kanban.md（TODO→DOING→DONE）
4. **完成必核对** → 逐项核对 TODO，生成核对报告
5. **结束必寸止** → 调用 `cunzhi` MCP 等待用户确认（降级用 `mcp-feedback`）
6. **纠正必记录** → 用户说"不要xxx"立即写入 Memory (forbidden_action)
7. **文件是真理** → 不依赖会话记忆，状态全在 `.ai_state/`

---

## 🚀 启动协议

```
会话开始 → 检查 .ai_state/session.lock
         ↓
    存在？──Yes──→ 输出恢复选项，等待用户选择
         │
         No
         ↓
    加载 Memory（user_preference, forbidden_action）
         ↓
    读取 .ai_state/（active_context, kanban, conventions）
         ↓
    汇报状态，等待指令
```

---

## 📋 寸止点

| Token | 触发时机 | 调用工具 |
|:---|:---|:---|
| `[PLAN_READY]` | TODO 生成完 | cunzhi / mcp-feedback |
| `[DESIGN_FREEZE]` | 架构设计完 | cunzhi / mcp-feedback |
| `[PHASE_DONE]` | 阶段完成 | cunzhi / mcp-feedback |
| `[TASK_DONE]` | 全部完成 | cunzhi / mcp-feedback |

**寸止时必须调用工具，不是只输出文字！**

---

## 📂 状态文件

```
.ai_state/
├── session.lock      # 会话锁（工作流进行中存在）
├── active_context.md # 当前 TODO
├── kanban.md         # 看板（TODO/DOING/DONE 三栏）
├── conventions.md    # 项目约定
└── decisions.md      # 技术决策
```

---

## 🔄 工作流

**复杂度评估 → 选择路径 → 执行 RIPER**

| 路径 | 条件 | 加载文件 |
|:---|:---|:---|
| A | 单文件/<30行 | `workflows/path-a.md` |
| B | 2-10文件 | `workflows/path-b.md` |
| C | >10文件 | `workflows/path-c.md` |

**RIPER 按阶段加载**：
- R1 → `skills/research.md`
- I → `skills/innovate.md`
- P → `skills/plan.md`
- E → `skills/execute.md`
- R2 → `skills/review.md`

---

## 🛠️ 指令速查

| 指令 | 作用 |
|:---|:---|
| `/vibe-init` | 初始化项目 |
| `/vibe-plan` | 生成 TODO |
| `/vibe-code` | 执行编码 |
| `/vibe-pause` | 暂停工作流 |
| `/vibe-resume` | 恢复工作流 |
| `/vibe-status` | 查看状态 |

---

## ⚠️ 禁止行为

- ❌ 跳过 TODO 直接完成
- ❌ 不核对就说完成
- ❌ 不调用寸止就结束
- ❌ 工作流中开新任务
- ❌ 猜测用户意图（不确定就寸止澄清）

---

**详细说明按需加载，见 `skills/` 和 `workflows/`**
