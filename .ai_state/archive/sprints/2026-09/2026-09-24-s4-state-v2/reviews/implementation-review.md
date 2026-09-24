# Implementation review — S4 state-v2

独立 reviewer：general-purpose 子 agent，只读 bundle + /tmp 对抗探针。

| 轮 | 结论 | 要点 | 处置 |
|---|---|---|---|
| r1 | REWORK | P0：migrate 回滚会删未跟踪/忽略文件（`git add -A .ai_state` 把它们变成已跟踪）。P1：ship 暂存路径型忽略文件；setItem 留孤儿嵌套块；嵌套 `- id:` 被当 item；v2 再迁移把当前 sprint 标 paused；ship 非原子；tidy/start 暂存无关文件。P2×10 | 精确暂存（只暂存 CLI 移动/写入且原已跟踪的文件）；月份含松散文件不打包、tar 只打已跟踪；全部可失败检查前置；blockEnd 整块替换；runtimeReads fail-closed；保留期保护 snapshots/archive/_index.v1/热层证据；queue 整词匹配；真实 tag 名 |
| r2 | CONCERNS | P1：块内注释行截断替换。P2：计划内重复目标、review.json 未暂存、路径型忽略文件迁后暴露、Rlues 冻结源码字面引用触发 55 个 blocker | 注释/空行归入块；重复目标前置拒绝；ship 显式暂存四文件；`archive/.gitignore` 精确条目；`--allow-reads "<理由>"` |
| r3 | PASS | P2：回滚后被迁移的忽略文件与 .runtime 文件暴露；P3：gitignore 条目未转义、深缩进注释被视为块内 | 回滚说明列出须手动移回/删除的文件；条目转义；P3 注释归属记为已知 |

VERDICT: PASS
