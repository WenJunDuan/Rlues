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

新项目 `athena init`；9.9.x 项目 `athena migrate --to 10.1 --dry-run` 先看计划。模板在 `~/.athena/current/templates/`。

## 恢复中断

1. `athena status`：路由、热 sprint、队列、等待项（resume 条件满足的标 ready）、未关 issue、豁免。
2. 读当前 sprint 的 design.md 与 log.md 末尾；核对 worktree 与子 agent 是否还在跑，不凭摘要重派或覆盖文件。
3. 证据与 review 以当前源码树为准：树变了就重跑，不沿用旧结论。

## 梳理

A7 提示（热层 >3 个 sprint、issues >40 行、`_index` >3 KB）时跑 `athena tidy --dry-run`，确认后 `athena tidy`：月结、打包、热层限额、`.runtime` 保留期。
