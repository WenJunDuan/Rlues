---
name: vibe-plan
description: 增强的计划命令，整合知识库和经验库
---

# /vibe-plan - 增强计划

## Usage

```bash
vibe-plan "任务描述"
```

## Workflow

1. 调用官方 `/plan`
2. 检索 knowledge-base
3. 检索 experience
4. 使用 context7 获取库文档
5. 生成 TODO.md + kanban.md
6. `[PLAN_READY]` 寸止等待

## Output

- .ai_state/meta/TODO.md
- .ai_state/meta/kanban.md
