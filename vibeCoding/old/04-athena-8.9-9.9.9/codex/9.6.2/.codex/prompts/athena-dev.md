---
name: athena-dev
description: |
  Athena 开发主入口 skill. 用户说"实施这个 task" / "做这个 feature" 时调度.
  按 PACE 路径推进 stage 状态机.
effort: medium
---

# /athena-dev — 开发主入口 (v9.6.2)

## 触发

用户给一个 high-level task → 主 agent 自动路由:
- "fix this bug" → Bugfix 路径
- "add a feature for X" → Feature 路径
- "refactor module Y" → Refactor 路径 (强制 polish)
- "build a system Z" → System 路径 (含 design + polish)

## 工作流

1. Read `.ai_state/_index.md` 确认项目已 init
2. 路由判断 (按用户输入)
3. 写入 `_index.md.path` + `stage = plan`
4. 进入 plan stage, Read `~/.agents/skills/_athena/pace/SKILL.md` 跟随 stage 切换

详见 `~/.agents/skills/_athena/pace/SKILL.md`.
