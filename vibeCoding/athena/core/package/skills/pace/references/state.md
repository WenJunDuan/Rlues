# 项目状态 v2（`.ai_state/`）

| 文件 | 内容 | 谁写 |
|---|---|---|
| `_index.md` | 路由器（≤3 KB）：path、stage、sprint、roadmap、next_action、route、exemptions、flags | CLI |
| `sprints/<slug>/` | design.md、log.md、review.json、external-writer.json（可选） | 主 agent + CLI |
| `roadmap/<slug>/` | roadmap.md、items.yaml（item status：pending / active / done / deferred / paused / dropped） | 主 agent + CLI |
| `issues.md` | 唯一问题账，类型 B/G/U/E/D/Q | `athena issue` |
| `queue.md` | 执行序与裁定来源，不复述状态 | 主 agent |
| `archive/` | 已完成 sprint（按月），`archive/README.md` 记重定向 | `athena ship` / `tidy` |
| `.runtime/` | 证据、review run、快照；不入库 | CLI / 门禁 |

新项目 `athena init`；9.9.x 项目 `athena migrate --to 10.1 --dry-run` 先看计划。模板在 `{{athena:TEMPLATES_DIR}}/`。

## 恢复中断

1. `athena status --brief` + HANDOFF 顶段：活跃 sprint、队列前 N（默认 5，`--limit 1..10`）、开放 P0/P1 计数与前几条、waiting、交接标题；输出 ≤2 KB。不整读 queue / SPRINTS / issues；需详情再用 `athena status`（含 ready 条件、豁免与验收矩阵）或按条目定位。
2. 读当前 sprint 的 design.md 与 log.md 末尾；核对 worktree 与子 agent 是否还在跑，不凭摘要重派或覆盖文件。
3. 证据与 review 以当前源码树为准：树变了就重跑，不沿用旧结论。

## 梳理

A7 提示（热层 >3 个 sprint、issues >40 行、`_index` >3 KB、queue.md / SPRINTS.md >16 KB）时跑 `athena tidy --dry-run`，确认后 `athena tidy`：月结、打包、热层限额、`.runtime` 保留期。

queue.md / SPRINTS.md 热层目标各 ≤16 KB。tidy 仅移动状态明确为完成的表格行或列表记录到 `archive/ledgers/`；未知、pending、active、paused、deferred 保留。未完成内容本身超限时报告人工梳理，不强制截断。`athena status --json` 的 ledgers 计数含归档；tidy 对账 total / unfinished，dry-run 不写入。表格使用 `status` / `状态` 列，列表使用 `[x]` 或行末 `— status: done` 等明确终态；正文提到 done 不算完成；代码块与含嵌套内容的复杂列表保守保留。

`.runtime/subagents.jsonl` >1 MB 时轮转到同目录带时间戳文件，热 sprint 的溯源行留在活动文件；活动文件含热 sprint 溯源行时不按保留期删除；轮转文件与其他 runtime 文件同用 14 天 / 总量 50 MB 保留期。
