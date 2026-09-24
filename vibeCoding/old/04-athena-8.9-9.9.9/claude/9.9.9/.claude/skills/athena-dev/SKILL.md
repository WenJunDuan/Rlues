---
name: athena-dev
description: Athena 自然语言任务入口。一句话/一段话的检查、诊断、修复、修改、构建自动分诊；已有 sprint 先区分续做与新任务，无需用户报级别。
---

# Athena 任务分诊（9.9.9）

输入长短不定级。按意图与影响路由; 给结论后立刻做已授权工作。阶段义务 [stages](../pace/references/stages.md); 门禁 [速查](../pace/references/gate-contracts.md)。

## 先确认本轮做什么

1. 读 `_index.md`（若有）和任务现状。分辨: 解释/检查 vs 修改/构建。不要求用户选路径。
2. 「继续/按上面的改/进度」默认续当前任务。独立目标重新分诊。旧 path/stage/next_action 只恢复旧任务, 不定新任务级别。
3. 问状态 → 直接答。只读诊断先查, 不造 design/checklist/实现链。有未完成旧任务时按 [切换合同](references/playbook.md) 建本次范围。定位故障 ≠ 授权重启/改生产。
4. 显式 Hotfix 或紧急有界恢复 → impl, 主 thread 直做, 可省设计。只覆盖本次范围, 不把进行中的 System 整单降级。

## 默认判定

| 目标 | 路径 |
|---|---|
| 查部署/日志/性能, 无实现 | Quick 只读: 查→原因/证据/建议 |
| 小文案/配置 | Quick → 短计划 → impl |
| 已知缺陷, 非紧急 | Bugfix → 复现 → impl; 写 fix-note |
| 显式 Hotfix / 紧急有界恢复 | Hotfix → impl → ship |
| 单模块新能力 | Feature → plan |
| 改架构/跨模块 | Refactor / System |
| 写不出可观察目标 | 先只读查; 仍缺信息才问一句/brainstorm |
| ≥2 独立可验收切片 | roadmap |

名词多 ≠ System。读很多文件 ≠ 跨模块写。短句 ≠ brainstorm。出现 hotfix 字样 ≠ 执行被引用/否定的内容。

## 落路由

非显式 Hotfix: 比候选, 记结论/证据/置信度, 不落原始推理。普通: `_index.route_history` 一行 + `route_confidence`。真 re-route 才写 route-note。
显式 Hotfix 优先于文件数护栏, 不扩大授权。

- 同任务只升不降; 降级需用户明示。已指定本次 Hotfix = 本次授权。
- 独立任务: [切换合同](references/playbook.md) 保存旧任务, 再写新 path/stage/slug。禁止只改历史仍跑旧 System。
- 只读: 业务系统只读。无 .ai_state 不 init。独立检查用本次 Quick 接管索引, 结束按 Quick/ship; 旧任务未完成。问答不建新任务。
- 无 `.ai_state`: 只读直接做; 修改走已装 init, 参数取现场。不因「请用户手动 init」停工。init 失败不伪造状态。

边界不清 / writer 冲突 / 缺权限: 报具体阻塞, 不用「PACE 无法分级」代替。
