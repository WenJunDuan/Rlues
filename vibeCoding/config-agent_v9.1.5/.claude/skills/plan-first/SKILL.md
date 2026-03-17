---
name: plan-first
description: 任务分解与规划 — 基于 design.md 终稿
context: main
---
## 用途
设计文档 → 可独立执行、可独立验证的最小任务。

## 思考
- 依赖关系清楚吗? 有隐藏耦合吗?
- 每个任务怎么验证 "做完了"? (验证标准)
- 粒度: 每个 Task ≤30min, 太大就拆
- **动手**: 不确定的技术细节 → `mcp-deepwiki` 查
- Path C+: 哪些可并行? 分给哪个子代理?

## 执行
1. 读 .ai_state/design.md 终稿
2. 可用 `/plan {design 一句话摘要}` 进入规划模式
3. 输出 .ai_state/plan.md:
   ```
   ## 需求: {一句话}
   ## 预估: {总时间}
   - [ ] Task 1: {描述} — {预估} — 文件: {列表}
   - [ ] Task 2: {描述} — 依赖: Task 1
   ```
4. cunzhi [PLAN_CONFIRMED]

## 铁律: plan 未确认 → delivery-gate 阻塞交付
