---
description: "智能开发入口 — 自动路由复杂度并执行"
---
# /vibe-dev $ARGUMENTS

你收到开发需求: "$ARGUMENTS"

## 执行步骤
1. 读 .claude/workflows/pace.md → 判断复杂度路径 (A/B/C/D)
2. 读 .claude/workflows/riper-7.md → 按路径执行对应阶段
3. 如果 .ai_state/ 存在且有未完成任务 → 先恢复断点再继续

注意: 每个阶段的具体工具和检查点在 riper-7.md 中定义。
