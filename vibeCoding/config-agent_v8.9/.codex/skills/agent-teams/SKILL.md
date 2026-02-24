---
name: agent-teams
description: 并行分工 — Path C+ (Codex 协作模式)
---
## Codex 并行方式
1. /collab 启动协作模式
2. 并发 shell 命令 (Codex 原生)
3. 从 plan.md 读取任务, 手动分配执行顺序
4. 无依赖任务可并发执行

## 平台限制
Codex 不支持自动子代理。使用 /collab + 并发 shell 实现并行。
手动验证确保质量。
