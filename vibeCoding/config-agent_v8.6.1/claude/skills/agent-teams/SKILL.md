---
name: agent-teams
description: Path D 并行编排 — Agent Teams + TeammateIdle/TaskCompleted
context: main
---
# Agent Teams (仅 Path D)

## 前置条件
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 (已在 settings.json 中设置)

## 创建团队流程
1. 分析任务可并行性, 按模块划分 teammates
2. cunzhi [TEAM_PLAN] 确认
3. 创建 Agent Team: `TeamCreate + TaskCreate + Task(spawn teammates)`
4. TeammateIdle hook 自动分配空闲 teammate 到下一个未完成任务
5. TaskCompleted hook 强制质量门禁 (测试+类型检查)
6. 所有任务完成 → cunzhi [TEAM_DONE]

## Teammate 模板
```
Task({
  prompt: "你是 {角色}. 负责 {模块}. 只修改 {目录范围} 的文件.",
  subagent_type: "builder",
  team_name: "{team}",
  name: "{name}"
})
```

## 防冲突
- 每个 teammate 只写自己负责的目录
- plan.md 中明确标注文件边界
- 冲突时主代理仲裁
