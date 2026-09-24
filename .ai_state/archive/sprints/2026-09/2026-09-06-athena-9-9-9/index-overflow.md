# Index overflow — 2026-09-06 Athena 9.9.9 design

## route-before-design

2026-07-10 System: user-approved impl-first flow; Fable5 post-implementation review remains mandatory

## rh-4

2026-07-14 System: repair Athena 9.9.3 review findings, full regression, formal review, merge and publish

旧索引中以下缩写锚点来自9.9.8；保留跳转，避免当前sprint切换后误解原文位置。

## rh-0

[原始完整条目](../2026-08-27-athena-9-9-8/index-overflow.md#rh-0)

## rh-1

[原始完整条目](../2026-08-27-athena-9-9-8/index-overflow.md#rh-1)

## rh-2

[原始完整条目](../2026-08-27-athena-9-9-8/index-overflow.md#rh-2)

## rh-3

[原始完整条目](../2026-08-27-athena-9-9-8/index-overflow.md#rh-3)

## previous-current-state

以下是迁移前完整状态段。此段内部旧的 `index-overflow.md` 引用属于 [9.9.8 overflow](../2026-08-27-athena-9-9-8/index-overflow.md)。

## 当前状态

[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 sprints/{slug}/index-overflow.md]

- 2026-08-27 close-out: 9.9.8 已 ship, 项目转 idle (path/stage/sprint 空); 21 个旧 sprint 入 archive/2026 →index-overflow.md#st-11
- 2026-08-27 reset: plan_critique_disabled / skip_impl_subagent_check 复位 false (本 sprint 一次性授权不外溢); _index 迁 9.9.8 schema
- 2026-08-27 ship: 9.9.8 推 origin/main。validator 120/0/0。本机 CC/CX 已同步。
- 2026-08-27 leftover: AC11 eval PASS (labeled); 160B overflow on; ~/.claude|codex 9.9.8 synced, user model/effort kept. Targeted packet ready.
- 2026-08-27 rework: F1–F7 已修。validator 106/0/0。待独立复核。F8 eval 为 ship 前置。未同步 ~/.claude|codex。
- 2026-08-27 design：Grok/Codex 已完善 `Thin PACE Control Plane`：一次原生 review、hook 红黄绿（现场复现无害 `rg` pa →index-overflow.md#st-1
- 2026-07-29 ship：hotfix2 已完成提交并推送 `main`（`19dd8d5`）；delivery-gate exit 0，工作树干净，当前 sprint/road →index-overflow.md#st-2
- 2026-07-29 W35-W40 hotfix2：canonical 双端包已同步 ~/.claude 与 ~/.codex（30 个目标，逐文件事务备份）；历史/ →index-overflow.md#st-3
- 2026-07-28 W31-W34 安装态部署已完成：12 个源条目、10 个唯一目标，9 个过期目标更新；两端哈希、语法 →index-overflow.md#st-4
- older 当前状态 →index-overflow.md#st-12


## route-before-implementation

2026-07-13 System: user-approved Athena 9.9.2 overall architecture upgrade; four primitives + spec-gate + two-tier memory are mandatory
