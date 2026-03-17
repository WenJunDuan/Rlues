---
name: agent-teams
description: 多代理并行协作 — Path C/D 使用
context: main
---
## 管道位置: Path C/D 的 E 和 T 阶段

## 何时启用
Path C/D 且任务可并行 (如: 前端+后端, 多个独立模块)

## 编排模式
1. 主 agent 分配任务 → 用 Agent(builder) 并行实现不同模块
2. Agent(explorer) background 调研依赖/API
3. 全部完成后 → Agent(validator) 统一审查
4. 用 ExitWorktree 退出隔离环境

## 规则
- 每个子代理在独立 worktree (isolation: worktree)
- 子代理间通过 .ai_state/ 文件通信
- SubagentStop hook 自动检查子代理产出质量
