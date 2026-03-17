---
name: agent-teams
description: 多代理并行 — Path C/D 的 E 阶段
context: main
---
## 前提
- config.toml [features] multi_agent=true, collaboration_modes=true
- [agents] 定义了 builder/reviewer/explorer 角色
- 所有子代理遵循 AGENTS.md 思维协议

## 编排
1. 读 plan.md → 识别无依赖任务组
2. Codex 自动编排多代理 (基于 [agents] 角色)
3. spawn_agents_on_csv 可用于批量分派

## 规则
- 无依赖→并行, 有依赖→串行
- 同文件不并行修改
- 完成后 `/review` 审查合并结果
