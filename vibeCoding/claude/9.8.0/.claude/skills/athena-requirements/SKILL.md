---
name: athena-requirements
description: |
  维护 .ai_state/requirements/ 长效需求档 (软件要素: 为什么要这个能力).
  原始用户故事 + 当时权衡, 独立于会演化的 design.md —— 代码烂掉时弃码重生的逃生通道.
  借 CodeStable requirements 实体, 适配 agent-in-loop: 需求落盘可召回, 隐知识不丢.
effort: medium
---

# /athena-requirements — 需求逃生通道 (v9.8.0 新)

## 为什么存在 (痛点)

Athena 原本 brainstorm → design → impl, **没有独立的"原始需求 + 当时权衡"长效档**.
design.md 随实现演化, 半年后回看已认不出"最初到底要解决什么、为什么这么取舍".
本 skill 把需求作为**软件要素**独立存档 (借 CodeStable), WHY 与 HOW 分离。

| 档案 | 答什么 | 演化性 |
|---|---|---|
| **requirements/{slug}.md** (本) | **为什么要这能力** + 当时权衡 | 长效, 只在需求本身变时改 |
| architecture/{type}-{slug}.md | 现在长什么样 | 长效, 随实现刷新 |
| sprints/{slug}/design.md | 这次怎么做 | 一次性, 随 sprint 丢 |
| compound/decision-*.md | 为什么这样选 (技术) | 永久 |

> **逃生通道 (CodeStable 核心价值)**: 代码烂成一坨时, requirements/ 是弃码重生的依据 —— 留着需求和权衡, 让 agent 重新生成实现, 而不是对着烂代码缝缝补补.

## 触发

| 时机 | 强制度 |
|---|---|
| Feature / System 路径 (新能力) plan 前 (brainstorm 收敛后) | **建议** 先落 requirement |
| 用户显式 `/athena-requirements {slug}` | 触发 |
| 需求变更 (范围 / 验收标准变了) | **强制** 更新对应 requirements/{slug}.md |
| roadmap 拆分大需求 | 每条子 feature 一条 requirement |
| Bugfix / Quick / Hotfix | 跳过 (无新需求, 是修既有) |

## 产出: `.ai_state/requirements/{slug}.md`

```markdown
---
slug: jwt-refresh
status: active            # active | superseded | dropped
created: 2026-06-22
linked_sprints: []        # 实现它的 sprint slug 列表
---

# 需求: {一句话}

## 原始用户故事
[用户原话 / 场景: 作为 X, 我想 Y, 以便 Z]

## 当时的权衡 (为什么这样圈定范围)
- 要: ...
- 不要 (本期划出去的): ... — 因为 ...
- 取舍: 选 A 不选 B, 因为 ...

## 高层验收 (能力级, 非实现级)
- [ ] ...

## 逃生通道备注
[若弃码重生, 哪些约束/边界必须保留]
```

## 与 design 的契约 (req_ref)

`design.md` frontmatter 加 `req_ref: requirements/{slug}.md`. 这样 review 的 spec-compliance 不只对 design, 还能回溯**原始需求**, 抓"实现偏离了最初意图"这一层 (design 自己可能就已经偏了)。

## 工作流

1. brainstorm 收敛 (或用户直接给清晰需求) → 主 agent 起 `requirements/{slug}.md`
2. 写原始故事 + 权衡 + 高层验收 (用户原话优先, 不要 agent 脑补)
3. 进 design 时在 design.md 写 `req_ref`
4. 需求变更 → 回来改 requirements/{slug}.md 的对应段 + 标注变更, **不删旧权衡** (审计用)
5. 更新 `_index.pointers.latest_requirement`

## 不做

- ❌ 不写实现 (那是 design / 源码)
- ❌ 不写架构现状 (那是 architecture/)
- ❌ 不写技术选型理由 (那是 compound/decision-*.md)
- ❌ 不随实现刷新 (只在需求本身变时改; 实现怎么变是 architecture/ 的事)
- ❌ 不给小修小补建需求 (Bugfix/Quick 无新需求)

## 与 architect-doc 对称

requirements/ (WHY 长效) 和 architecture/ (HOW 长效) 是一对: 一个记"要解决什么", 一个记"现在长啥样". design.md 是连接两者的一次性桥。
