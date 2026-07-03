---
name: ai-state-template
description: 项目状态文件模板（v7.5增强版）
location: project_document/.ai_state/
---

# .ai_state 项目状态模板 (v7.5)

## 目录结构

```
project_document/
└── .ai_state/
    ├── session.yaml          # 🆕 会话状态（核心）
    ├── workflow.lock         # 🆕 工作流锁
    ├── checkpoint.md         # 🆕 断点恢复信息
    ├── active_context.md     # 当前任务和TODO
    ├── kanban.md             # 三态进度看板
    ├── handoff.md            # AI交接记录
    ├── conventions.md        # 项目约定
    ├── decisions.md          # 技术决策
    └── doc_check.yaml        # 🆕 文档检查记录
```

---

## session.yaml 模板

```yaml
# 会话状态 - 每次操作都要更新
session:
  id: "sess_YYYYMMDD_XXX"
  created_at: "2025-01-12T09:00:00Z"
  updated_at: "2025-01-12T10:30:00Z"

# 当前模式
mode:
  type: "workflow"           # workflow | conversation | paused
  workflow_name: ""          # vibe-plan | vibe-code | vibe-review 等
  phase: ""                  # R1 | I | P | E | R2
  step: ""                   # 当前步骤编号

# 工作流状态
workflow:
  started_at: ""
  current_task: ""
  total_tasks: 0
  completed_tasks: 0
  status: "idle"             # idle | running | paused | completed | failed | aborted

# 上下文摘要
context:
  goal: ""
  last_action: ""
  next_action: ""
  pending_questions: []
```

---

## workflow.lock 模板

```yaml
# 工作流锁 - 防止模式切换
locked: true
workflow: "vibe-code"
locked_at: "2025-01-12T09:00:00Z"
reason: "工作流执行中"

unlock_conditions:
  - "所有TODO完成"
  - "用户通过寸止确认"
  - "用户执行 /vibe-pause"
  - "用户执行 /vibe-abort"
```

---

## checkpoint.md 模板

```markdown
# 断点信息

## 暂停时间
2025-01-12T10:30:00Z

## 工作流信息
- **名称**: vibe-code
- **阶段**: Execute (E)
- **步骤**: 4.3

## 当前任务
- **ID**: T-XXX
- **描述**: [任务描述]
- **进度**: XX%

## 当前位置
- **文件**: path/to/file.ts
- **行号**: XX
- **动作**: [正在做什么]

## 待继续工作
1. [待完成项1]
2. [待完成项2]

## 恢复指令
/vibe-resume
```

---

## active_context.md 模板

```markdown
# Active Context State

> **异步意识**: 这是AI的唯一真理来源

## 🎯 当前目标

> [里程碑描述]

## 📋 TODO 列表

### Phase 1: [阶段名]

- [ ] T-001: [任务描述]
  - **文件**: [涉及文件]
  - **依赖**: 无
  - **预估**: 30分钟
  - **验收**: [验收标准]
  - **Owner**: LD

- [ ] T-002: [任务描述]
  - **文件**: [涉及文件]
  - **依赖**: T-001
  - **预估**: 1小时
  - **验收**: [验收标准]
  - **Owner**: LD

## 🧩 关键约束

- TypeScript 无 any
- 函数 < 50行

## 📝 验证日志

### [日期] T-XXX
- **状态**: ✅/❌
- **验证**: [证据]
- **用时**: [实际用时]
```

---

## kanban.md 模板

见 `templates/kanban.md`（三态看板）

---

## doc_check.yaml 模板

```yaml
# 文档检查记录
last_check: "2025-01-12T10:30:00Z"

documents:
  README.md:
    last_modified: ""
    last_checked: ""
    hash: ""

  conventions.md:
    last_modified: ""
    last_checked: ""
    extracted_rules: 0

  decisions.md:
    last_modified: ""
    last_checked: ""
    extracted_decisions: 0

extracted:
  - source: ""
    type: ""
    content: ""
    added_at: ""
```

---

## 初始化命令

```bash
/vibe-init
```

自动创建所有必需的状态文件。

---

## 状态检查命令

```bash
/vibe-state
/vibe-state --full
```

查看当前所有状态文件的内容。
