---
name: agent-teams
description: Path D 并行编排 — 子代理分工 + Agent Teams 协作。需要 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
context: main
---

# Agent Teams & Subagents

## 两层并行架构

**子代理** (Task tool, 任意 Path): 快速聚焦任务, 结果报回主代理。
**Agent Teams** (仅 Path D): 多个 teammate 共享任务板, 互相通信协调。

## 预置子代理 (.claude/agents/)

| 代理 | 用途 | 工具 | 模型 |
|:---|:---|:---|:---|
| builder | 实现代码, 限定文件范围 | Read/Write/Edit/Bash | sonnet |
| validator | 测试+lint+安全扫描 | Read/Bash/Grep | sonnet |
| explorer | 只读调研, 搜索分析 | Read/Glob/Grep | sonnet |

## 调度规则

Path B: explorer 调研 → 主代理实现 → validator 验证
Path C: explorer 并行调研 → builder 实现 → validator 验证 → 循环
Path D: 创建 Agent Team, 按模块分 teammate:
```
创建 agent team 重构 {模块}:
- teammate-1: 后端 API ({文件范围})
- teammate-2: 前端组件 ({文件范围})
- teammate-3: 测试覆盖 ({文件范围})
要求: 每个 teammate 完成后 commit, 不修改其他 teammate 的文件
```

## 防冲突

子代理之间不共享文件 → 按目录/模块划分边界。
SubagentStop hook 自动验证子代理输出质量。
