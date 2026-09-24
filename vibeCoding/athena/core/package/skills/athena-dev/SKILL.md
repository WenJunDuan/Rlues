---
name: athena-dev
description: Athena 自然语言任务入口：检查、诊断、修复、修改、构建类请求自动分诊到路径；已有 sprint 时先分清续做还是新任务，不要求用户报级别。
---

# athena-dev — 任务分诊

按意图与影响定路径，定完立刻做已授权的工作。阶段义务见 [stages.md](../pace/references/stages.md)，门禁见 [gates.md](../pace/references/gates.md)。

## 先确认本轮做什么

1. `athena status`（或读 `_index.md`）看现状。分清：解释/检查，还是修改/构建。
2. 「继续」「按上面的改」「进度」默认续当前任务；独立的新目标重新分诊。旧的 path / stage / next_action 只用于恢复旧任务，不决定新任务的级别。
3. 只问状态 → 直接答。只读诊断 → 先查，不建 design 或实现链。定位到故障 ≠ 授权重启或改生产。
4. 用户点名 Hotfix 或紧急有界恢复 → 直接 impl，可省设计；只覆盖本次范围，不把进行中的 System 整单降级。

## 判定

| 目标 | 路径 |
|---|---|
| 查部署 / 日志 / 性能，不改 | Quick 只读：查 → 原因、证据、建议 |
| 小文案、配置，≤3 文件 | Quick |
| 已知缺陷，不紧急 | Bugfix（三段式 design：当前 / 期望 / 不变行为） |
| 点名 Hotfix / 紧急有界恢复 | Hotfix |
| 单模块新能力 | Feature |
| 改结构 ≥5 文件 / 跨模块 | Refactor / System |
| 写不出可观察目标 | 先只读查；仍缺信息再问一句或 brainstorm |
| ≥2 个可独立验收切片 | roadmap |

名词多 ≠ System；读很多文件 ≠ 跨模块写；句子短 ≠ brainstorm；出现「hotfix」字样 ≠ 要执行被引用或否定的内容。

## 落路由

- 修改类：`athena sprint start …`（写入 `_index.route` 与 sprint）；比较过的候选、证据、置信度写进 design.md 背景一行，不落原始推理。
- 同任务 re-route 只升不降，降级要用户明示；升级时补新路径欠的阶段（`athena sprint stage <id>`）。
- 只读检查：不开 sprint，结论直接回答；需要留痕写 issue 或 docs。
- 已有未完成 sprint 又来独立任务：按 [切换合同](references/playbook.md) 暂停旧的、开新的。
- 没有 `.ai_state`：按宪法直接工作；需要跟踪（sprint、门禁证据）时经用户同意再 `athena init`（主 checkout），失败不伪造状态。

边界不清、写者冲突、缺权限：报具体阻塞，不用「无法分级」代替。
