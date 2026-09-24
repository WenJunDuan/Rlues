---
name: athena-requirements
description: 为一项新能力写长效需求档（原始动机、范围取舍、用户视角验收）并澄清到定稿；Feature/System 开工前或需求变更时用。
---

# athena-requirements — 需求档

需求档记「为什么要这个能力、当时怎么取舍」，比 design 活得久；代码烂掉时它是重写的依据。

| 档 | 回答 | 何时改 |
|---|---|---|
| `docs/requirements/<slug>.md` | 为什么要、范围、用户视角验收 | 需求本身变时 |
| `architecture/` | 现在长什么样 | 随实现 |
| `sprints/<slug>/design.md` | 这次怎么做 | 一次性 |
| `decisions/` | 技术上为什么这样选 | 推翻时追加新档 |

何时用：Feature/System 新能力（brainstorm 收敛后、design 前）；roadmap 拆出的每个子能力；需求范围或验收变了（必须更新）。Bugfix/Quick/Hotfix 不用。

## 步骤

1. 从 `~/.athena/current/templates/requirement.md` 建 `.ai_state/docs/requirements/<slug>.md`。
2. 写背景与目标、范围与不做（写明划出去的原因）、用户视角验收。用户原话优先，不脑补。
3. 澄清循环：没把握的点逐条写进「待澄清问题」，一次问用户最影响范围的 1–3 条；回答写成结论。全部有结论 → `status: final`。
4. 开 sprint 时带上需求：`athena sprint start --req docs/requirements/<slug>.md --path P --slug S`（design 的 `req:` 字段指向它，reviewer 可回溯原始意图）。
5. 定稿后变更：文末追加「修订」节（日期、改了什么、谁拍板），不删旧取舍。

## 不写

实现（design / 源码）、架构现状（architecture）、技术选型理由（decisions）、小修小补。

完成条件：需求档 `status: final`，每条待澄清问题有结论，design 的 `req:` 指向它。
