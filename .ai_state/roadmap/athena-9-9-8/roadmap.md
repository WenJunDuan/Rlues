---
roadmap_slug: athena-9-9-8
created: 2026-08-27
trigger: user_explicit
estimated_total_complexity: L
---

# Roadmap — Athena 9.9.8

## 目标

保留 PACE + `ai_state` 内核，把 agent loop、compaction、原生 review 与工具权限交还 CC/CX。删除设计自审、实现后 2+1/passN、过宽 hook block、无界状态与重复上下文，让控制面 token 至少下降 40%，质量与真正的安全/交付门禁不降。

## 三个可回滚切片

| # | slug | 交付 | 依赖 |
|---|---|---|---|
| 1 | review-contract-and-flow | 派生 packet、一次原生 review、final-diff gate、hook 红黄绿合同 | 无 |
| 2 | harness-context-and-model-policy | 去重复 prompt/绑定、quote-aware hook fixture、原生能力适配、model/effort eval | 1 |
| 3 | state-retention-and-retrieval | 有界 `_index`、冷归档、可重建 cache、telemetry retention | 1 |

设计真相：`sprints/2026-08-27-athena-9-9-8/design.md`。本次用户要求的独立 Claude 复盘从同目录 `review-packet.md` 开始；通过前不授权实现。

## 发布门槛

- 三个切片分别有双端 fixture 与回滚点。
- 代表性历史任务对比交付成功率、有效 findings、控制面 tokens、总 tokens 与耗时。
- System ship 前更新 architecture；不创建第二状态树或人工 catalog。
