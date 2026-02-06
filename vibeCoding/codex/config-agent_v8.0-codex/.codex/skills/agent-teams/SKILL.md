---
name: agent-teams
description: |
  Agent Teams orchestration for Claude Code. Coordinates multiple Claude
  instances working in parallel on shared codebase. Requires experimental
  flag CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1.
  New in v8.0, replaces multi-ai skill for Claude Code platform.
---

# Agent Teams Skill

## 何时激活

- P.A.C.E. 路由到 Path D
- 用户显式 `vibe-dev --team`
- Lead Agent 判断任务可并行

## 架构

```
Lead Agent (你的主 Claude Code 会话)
  ├── 分析任务 + 拆分子任务
  ├── cunzhi [TEAM_PLAN] 确认分配方案
  │
  ├── Teammate A (独立上下文窗口)
  │   └── 子任务 + 限定 MCP + 限定文件范围
  ├── Teammate B (独立上下文窗口)
  │   └── 子任务 + 限定 MCP + 限定文件范围
  ├── Teammate C (独立上下文窗口)
  │   └── 子任务 + 限定 MCP + 限定文件范围
  │
  └── Lead 监控进度 → 合并结果 → cunzhi [TEAM_DONE]
```

## Agent Teams vs Subagents

| 特性 | Subagents | Agent Teams |
|:---|:---|:---|
| 通信 | 只向主 agent 汇报 | teammates 互相通信 |
| 上下文 | 共享主 agent 窗口 | 各自独立窗口 |
| 适用 | 快速聚焦子任务 | 需要协调的并行工作 |
| Token | 较低 | 显著更多 |

**决策原则**: 如果 teammates 不需要互相沟通，用 subagents。需要互相挑战和协调的，用 Agent Teams。

## 最佳场景

| 场景 | 团队结构 |
|:---|:---|
| 代码审查 | 3 个 reviewer 分别审查不同模块 |
| 新功能开发 | frontend / backend / tests 各一个 |
| Bug 竞争假设 | 3 个 agent 分别验证不同假设 |
| 跨层变更 | UI / API / DB 各一个 |

## 反模式 (不要用 Agent Teams)

- 顺序依赖的任务 (A 必须等 B 完成)
- 同一文件的修改 (merge 冲突)
- 简单任务 (overhead 不值得)

## 任务状态与 .ai_state 联动

```
Lead 创建团队:
  → .ai_state/doing.md 记录 "[TEAM] 任务名: N teammates"

Teammate 完成:
  → Lead 更新 doing.md 进度

全部完成:
  → Lead 合并 → doing.md → done.md
  → cunzhi [TEAM_DONE]
```

## 配置

```json
// settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## 降级策略

Agent Teams 失败或不可用 → 自动降级到 Path C (单 agent 顺序执行)。
Lead Agent 记录降级原因到 `.ai_state/decisions.md`。
