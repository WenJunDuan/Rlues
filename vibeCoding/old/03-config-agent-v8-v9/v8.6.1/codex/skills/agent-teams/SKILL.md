---
name: agent-teams
description: 并行编排 — Codex collab 模式
context: main
---
# 并行编排 (Codex collab)

## 调度策略
1. 分析任务可并行性, 按模块划分
2. cunzhi [TEAM_PLAN] 确认
3. 使用 collab + parallel features 并行执行
4. 每个子任务限定文件范围
5. 结果汇总 → 验证 → cunzhi [TEAM_DONE]

## 防冲突
- plan.md 中标注每个任务的文件边界
- parallel 子命令之间不共享写入文件
