---
name: agent-teams
---

# Agent Teams (Path D)

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| Agent Teams API | Claude Code | 并行执行 | env: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 |
| skill/worktrees | VibeCoding Skill | 隔离分支 | E 阶段自动加载 |
| skill/tdd | VibeCoding Skill | 每个 teammate 强制 TDD | 自动 |
| cunzhi MCP | MCP | Lead gates | `cunzhi.confirm(TEAM_PLAN / TEAM_DONE)` |
| commit-commands | Plugin | 各 teammate 提交规范 | 自动: `git commit` 时 |
| Superpowers subagent-driven-dev | Plugin Skill | teammate 内部子任务 | 自动 |

## 架构

```
Lead Agent (主会话)
  ├─ R→D→P→C          ← Lead 独立完成
  ├─ cunzhi [TEAM_PLAN] ← 寸止: 确认分工
  ├─ Teammate A         ← 独立窗口, 模块 A
  ├─ Teammate B         ← 独立窗口, 模块 B
  └─ Lead: V→Rev       ← 合并后审查
```

## Teammate 上下文传递

Teammates 继承 CLAUDE.md 和 settings.json，但不继承 .ai_state。
Lead 分配时必须传入:

```
# Lead 分配模板 (每个 Teammate)
---
## 你的任务
[从 plan.md 截取该 teammate 负责的 TASK 列表]

## 项目约定
[从 conventions.md 完整复制]

## 目标文件范围
[该 teammate 可以修改的文件/目录列表]

## 分支
feature/vibe-{id}-{module}

## 完成标准
- 所有 TASK 的 RED-GREEN-REFACTOR 完成
- 测试覆盖率 ≥85%
- 无 TypeScript any
- commit 后推送到子分支
---
```

## 何时用 Teams vs Subagent

| | Subagent | Agent Teams |
|:---|:---|:---|
| 粒度 | 单任务 (2-5min) | 模块级 (数小时) |
| 上下文 | 共享主会话 | 各自独立 |
| 适用 | Path B/C E 阶段 | Path D |
| 工具 | Superpowers subagent-driven-dev | Claude Code Agent Teams |

不需要互通 → subagent。需要协调 → Teams。

## Git 策略

加载 skill/worktrees:

```
Lead:  feature/vibe-{id}-main
  ├─ Teammate: feature/vibe-{id}-frontend
  ├─ Teammate: feature/vibe-{id}-backend
  └─ Teammate: feature/vibe-{id}-tests
合并顺序: tests → backend → frontend → main
冲突处理: Lead 手动解决 + cunzhi 确认
```

## 降级

Agent Teams 失败 → Path C 顺序执行。记录原因到 decisions.md。
Codex CLI: Path D 自动降级 Path C (无 Agent Teams 支持)。
