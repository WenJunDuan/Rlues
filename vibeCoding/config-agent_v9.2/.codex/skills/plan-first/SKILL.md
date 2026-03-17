---
name: plan-first
description: 任务分解与计划生成 — P 阶段使用
---
## 管道位置: P → 产出 plan.md → 交给 E

## 流程
1. 读 design.md
2. 分解为 Task, 每个含: 描述、预估、文件列表、依赖
3. 写入 .ai_state/plan.md

## 例子
```markdown
- [ ] T-001: 实现 JWT 签发函数 — 20min — src/utils/jwt.ts, tests/jwt.test.ts
- [ ] T-002: 实现 /login 路由 — 25min — 依赖: T-001
```
