---
name: vibe-init
description: 初始化项目，创建 .ai_state/ 和 .knowledge/ 目录结构
---

# /vibe-init - 项目初始化

## Usage

```bash
vibe-init              # 初始化当前项目
vibe-init --full       # 完整初始化（含模板）
```

## Creates

```
.ai_state/
├── requirements/
├── designs/
├── experience/
│   └── learned/
├── checkpoints/
└── meta/
    └── kanban.md

.knowledge/
├── project/
├── standards/
├── company/
└── tech/
```

## Base Command

Calls `/init` first, then enhances with VibeCoding structure.
