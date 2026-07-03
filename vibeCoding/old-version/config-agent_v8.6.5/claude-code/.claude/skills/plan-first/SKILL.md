---
name: plan-first
description: 强制先规划后执行 — 基于 session.md 设计方案段生成计划
context: main
---
Path B+ 任务 (brainstorm 完成后):
1. 读 `.ai_state/session.md` 设计方案段作为规划输入
2. 使用 `/plan` 进入规划模式
3. context7 查询涉及的库文档, 确保计划技术细节准确
4. 输出到 `.ai_state/plan.md`: 任务列表+依赖+预估+子代理分配
5. cunzhi [PLAN_CONFIRMED] 确认后才能写代码
6. plan.md 中未完成任务不能关闭 session (delivery-gate 检查)

## 管道: brainstorm → context7 → plan-first → E (开发)
session.md 设计方案段是输入, plan.md 是最终执行蓝图。
