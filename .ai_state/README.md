# `.ai_state` — Athena 10.1 project state

本目录是项目的持久状态与工程证据入口。机器状态以 [`_index.md`](./_index.md) 为准；不要从归档历史反推当前状态。

## 当前布局

| 路径 | 内容 |
|---|---|
| `_index.md` | ≤3 KB 路由器：当前 path、stage、sprint、roadmap、next action、豁免与指针 |
| `queue.md` | 跨 roadmap 的执行顺序与裁定来源，不复述 item 状态 |
| `issues.md` | 唯一问题账；类型 B/G/U/E/D/Q |
| `docs/requirements/` | 已定稿的原始需求与范围 |
| `docs/research/` | 调研、外部评审输入、勘察材料 |
| `docs/reports/` | 迁移、验收、审计与交付报告 |
| `decisions/` | 一事一档的长期决策 |
| `architecture/` | 当前系统架构与历史版本说明 |
| `roadmap/<slug>/` | `roadmap.md` + `items.yaml`；item 状态是计划真相 |
| `sprints/<slug>/` | 仅进行中或暂停的热 sprint，合计不超过 3 个 |
| `archive/sprints/<YYYY-MM>/` | 已完成 sprint；更老月份由 `athena tidy` 打包 |
| `archive/legacy/` | v1 台账与已退役机制，只作审计 |
| `.runtime/` | 本机证据、快照和迁移保留物；gitignored，不作为长期文档 |

## 工作方式

1. 恢复任务先运行 `athena status`，再按 `_index.md` 指针读取当前 design/log。
2. 新任务用 `athena sprint start`；验证用 `athena run --covers AC… -- <command>`。
3. 独立审查使用 `athena review prepare` / `accept`；完成使用 `athena ship` 自动归档。
4. 状态膨胀时先 `athena tidy --dry-run`，确认后再执行 `athena tidy`。
5. 历史正文不因移动改写；旧路径到新路径的映射见 [`archive/README.md`](./archive/README.md)。

## 本仓状态

- schema：`athena-state/2`
- Athena：`10.1.0`
- 当前 roadmap：`athena-10-1`
- Rlues 已完成 v1→v2 迁移；迁移报告在 `docs/reports/2026-09-24-migrate-rlues.md`。
- 迁移前索引、基线与快照保留在 `.runtime/`，其余可重建缓存按 retention 清理。
