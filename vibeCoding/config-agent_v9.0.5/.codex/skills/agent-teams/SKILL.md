---
name: agent-teams
description: 多代理并行协作 — Path C/D 的 E 阶段
context: main
---
## 触发: Path C/D 的 E(执行) 阶段

## 前提
- Codex collab + parallel 模式已启用 (config.toml features)
- plan.md 中任务已标注可并行/有依赖

## 编排策略
1. 读 plan.md → 识别无依赖的任务组
2. 为每组 fork 子代理 (sub-agent fork from thread)
3. spawn_agents_on_csv 可用于批量分派
4. 每个子代理独立工作, 完成后合并

## 并行规则
- 无依赖任务: 并行执行
- 有依赖任务: 串行, 前置完成后触发
- 同文件不并行修改
- 完成后 /review 审查合并结果
