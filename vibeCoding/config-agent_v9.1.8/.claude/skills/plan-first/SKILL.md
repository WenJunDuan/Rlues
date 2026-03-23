---
name: plan-first
description: 任务分解 — P阶段
context: main
---
## 管道位置: P → plan.md → Plan Review → E

读design.md → 分解Task(描述/预估2-5min/文件/依赖) → plan.md

## 质量标准
- 粒度2-5min (初级工程师能执行)
- 文件路径具体 (src/utils/jwt.ts)
- 依赖明确 (T-002依赖T-001)

## 例子
```
- [ ] T-001: JWT签发 — 3min — src/utils/jwt.ts, tests/utils/jwt.test.ts
- [ ] T-002: /login路由 — 4min — 依赖:T-001
- [ ] T-003: 认证中间件 — 3min — 依赖:T-001
```
