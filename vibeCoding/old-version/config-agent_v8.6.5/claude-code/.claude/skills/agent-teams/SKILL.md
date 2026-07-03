---
name: agent-teams
description: Path D 并行编排 — Claude Code Agent Teams
context: main
---
# Agent Teams (仅 Path D)

## 前置条件
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 (已在 settings.json env 中设置)

## 创建团队流程
1. 分析任务可并行性, 按模块划分 teammates
2. cunzhi [TEAM_PLAN] 确认
3. 每个 teammate 用 Task() 分配, 指定 agent 和文件边界
4. TeammateIdle hook 自动分配下一个未完成任务
5. TaskCompleted hook 强制质量门禁 (测试+类型检查)
6. 所有任务完成 → cunzhi [TEAM_DONE]

## 防冲突
- 每个 teammate 只写自己负责的目录
- plan.md 中明确标注文件边界
- 冲突时主代理仲裁
