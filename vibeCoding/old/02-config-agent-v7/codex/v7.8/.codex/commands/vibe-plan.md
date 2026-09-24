---
name: vibe-plan
description: 任务规划，整合知识库和经验库
---

# vibe-plan - 任务规划

## Usage

```bash
vibe-plan "任务描述"
```

## Workflow

1. 检索 knowledge-base
2. 检索 experience
3. 使用 context7 获取库文档
4. 生成 TODO.md + kanban.md
5. `[PLAN_READY]` 寸止等待

## Output

- .ai_state/meta/TODO.md
- .ai_state/meta/kanban.md
