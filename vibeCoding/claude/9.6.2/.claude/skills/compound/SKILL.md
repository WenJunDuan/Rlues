---
name: compound
description: |
  Compound Learning Loop. 跨 sprint 积累的经验、模式、约束沉淀到 lessons.md, 后续 sprint 自动加载.
effort: medium
---

# /compound — 经验积累循环 (v9.6.2)

## 概念

Compound Learning Loop = 每次 polish / review 完成后, 把"做对的 pattern + 踩的坑 + 硬约束"沉淀到 `.ai_state/lessons.md`. 下一个 sprint 进入 plan stage 时, 主 agent **必须** read lessons.md 一次, 防止重复犯错.

## 写入时机

| 时机 | 触发 | 写入什么 |
|---|---|---|
| review_pass1 完成 | evaluator 写 VERDICT 时 | 1 行 pattern (做对了什么) |
| polish 完成 | cleanup-pass.md 写完时 | 1 行 pitfall (踩了什么坑) |
| 用户显式 `/compound add` | 用户主动 | 任意经验 |
| reviewer 发现新 P0 finding | findings 写完时 | constraint (硬约束) |

## 格式

```markdown
# Project Lessons

## [2026-05-23 sprint-2] Refactor JWT module
- Pattern: 用 RS256 instead of HS256 for stateless verification across services [executed]
- Pitfall: useEffect deps 漏掉 user.id 导致重渲染 inf loop [inspected]
- Constraint: 任何 JWT secret 改动必须更新所有 microservice 同时部署 [executed]

## [2026-05-22 sprint-1] Initial setup
- Pattern: TDD 严格执行后, refactor 阶段省了 40% 时间 [executed]
```

## 读取时机

- **plan stage 开始**: 主 agent Read `.ai_state/lessons.md` (强制, 不允许跳)
- **review stage 开始**: reviewer 读 lessons.md 看是否本 sprint 触犯了已知 pitfall

## 增量规则

- lessons.md ≤ 200 行: 持续追加
- lessons.md > 200 行: 主 agent 在 polish 后做"压缩 pass", 把相似 pattern 合并, 保留高密度
- lessons.md > 500 行: 拆分 archive (`lessons-2026-Q1.md`), 主 lessons.md 只留最近 3 个 sprint

## 约束

- 每条 lesson 必须带状态标 (`[executed]` / `[inspected]` / `[deferred]`)
- 不允许长篇大论 (一条 ≤ 30 字)
- 不允许重复 pattern (相同 pattern 第二次出现 → 升级为铁律候选)
