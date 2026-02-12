# vibe-brainstorm

需求讨论+方案探索。触发 RIPER-7 R+D 阶段。

## 语法

```
vibe-brainstorm "任务描述"
vibe-brainstorm --quick "任务描述"
```

## 用户体验

```
你: vibe-brainstorm "用户权限管理系统"

R 阶段:
  "RBAC 还是 ABAC？"
  "需要多租户吗？"
  "预期用户规模？"
  "需要审计日志吗？"

D 阶段:
  "方案 A: RBAC + Casbin — 简单直接"
  "方案 B: ABAC + OPA — 灵活复杂"
  推荐 + 理由
  → decisions.md
  → [寸止] 确认方案
```

## --quick

仅 3 问: 做什么？约束？怎样算完？直接推荐。

## 独立使用

可不接 vibe-dev。产出 decisions.md 后用 vibe-plan 继续。
