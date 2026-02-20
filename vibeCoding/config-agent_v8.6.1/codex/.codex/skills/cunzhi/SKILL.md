---
name: cunzhi
description: 寸止检查点 — 关键节点人工确认, 不可降级
context: main
---
调用 cunzhi MCP 在关键节点暂停等待用户确认。
检查点: REQ_CONFIRMED, DESIGN_READY, PLAN_CONFIRMED, VERIFIED, TASK_DONE, TEAM_PLAN, TEAM_DONE
MCP 不可用时 → 直接在对话中请求用户确认, 不可跳过。
