---
name: agent-teams
description: 多代理并行协作 — Path C/D
---
## 何时启用
Path C/D 且任务可并行

## Codex 原生子代理
1. spawn_agent 分配任务给 builder/explorer
2. wait_agent 等待完成
3. spawn_agents_on_csv 批量分发 (大规模任务)
4. 子代理间通过 .ai_state/ 文件通信

## 上下文隔离 (核心原则)
每个子代理只拿: Task 文本 + 相关文件路径 + conventions.md
**不传** 完整对话历史。精确 context > 更多信息。
