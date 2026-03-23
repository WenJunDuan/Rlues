---
name: agent-teams
description: 多代理并行 — Path C/D
context: main
---
## 编排
1. Agent(builder) 并行实现
2. Agent(explorer) background调研
3. Agent(validator) 统一审查
4. ExitWorktree 退出隔离

## 子代理上下文隔离 (核心)
每个子代理只拿: Task文本 + 文件路径 + conventions.md
**不传**完整对话历史。精确context > 更多信息。
