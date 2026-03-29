---
name: plan-first
description: 任务分解与计划生成 — P 阶段
---
## 管道位置: P → 产出 plan.md → Plan Review → 交给 E

## 流程
1. 读 design.md (定稿)
2. 分解为 Task, 每个含: 描述、预估(2-5min)、文件列表、依赖
3. 写入 .ai_state/plan.md

## 质量标准
- 粒度 2-5 min (初级工程师能执行)
- 文件路径具体 (src/utils/jwt.ts, 不是 "相关文件")
- 依赖关系明确

## 例子
```markdown
- [ ] T-001: JWT签发函数 — 3min — src/utils/jwt.ts, tests/utils/jwt.test.ts
- [ ] T-002: /login路由 — 4min — src/routes/auth.ts — 依赖: T-001
- [ ] T-003: 认证中间件 — 3min — 依赖: T-001
```
