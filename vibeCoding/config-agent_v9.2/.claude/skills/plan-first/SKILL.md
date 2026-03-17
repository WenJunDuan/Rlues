---
name: plan-first
description: 任务分解与计划生成 — P 阶段使用
context: main
---
## 管道位置: P → 产出 plan.md → 交给 E

## 流程
1. 读 design.md (定稿的方案)
2. 分解为可独立完成的 Task, 每个 Task 包含:
   - 描述、预估时间、涉及文件、依赖关系
3. 写入 .ai_state/plan.md

## 例子 (直接可用的格式)
```markdown
# 计划: JWT认证实现

## 任务清单
- [ ] T-001: 实现 JWT 签发工具函数 — 20min — src/utils/jwt.ts, tests/utils/jwt.test.ts
- [ ] T-002: 实现 /login 路由 — 25min — src/routes/auth.ts, tests/routes/auth.test.ts — 依赖: T-001
- [ ] T-003: 实现认证中间件 — 20min — src/middleware/auth.ts, tests/middleware/auth.test.ts — 依赖: T-001
- [ ] T-004: 实现 /refresh 路由 — 15min — src/routes/auth.ts — 依赖: T-001, T-003

## 执行顺序: T-001 → T-002, T-003 (可并行) → T-004
```
