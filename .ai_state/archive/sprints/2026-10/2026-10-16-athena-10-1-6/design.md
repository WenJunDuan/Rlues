---
sprint: "2026-10-16-athena-10-1-6"
path: "Bugfix"
created: "2026-10-16"
req: "quantum-links-G003-G004-G014-G015-G016"
roadmap: ""
item: ""
base_commit: "8446d31"
repro_test: "vibeCoding/athena/evals/fixtures/test_feedback_g003.py"
review_ignore: []
---

# Bugfix — Athena 10.1.6

## 当前行为
review 暂停排除仅依赖 HEAD 区间，晚合入的暂停期提交可漏排；install 覆盖 rules 索引；run 对无账本外仓不记录证据。
背景：按源码确认采用局部 Bugfix；保留旧日志 HEAD 边界兼容，不引入新账本或门禁豁免。

## 期望行为
暂停区间按提交者时间排除；恢复后 cherry-pick 的提交保留。rules 索引保留用户表格行。无账本目标回落调用仓活跃 sprint，记录 target；有账本保持归属。

## 不变行为
旧日期日志保留 HEAD 区间行为；源码树审查绑定不变；有账本目标（含空闲和无法映射的 worktree）不回落；不可证明命令不变为可证明。

## 验收标准
- AC1: G-003 测试先红后绿，暂停期提交按 committer date 排除，保留本 sprint 的已提交和未提交改动。
- AC2: G-004 测试先红后绿，恢复后 cherry-pick 不因暂停期作者时间被排除；新暂停日志含精确时间，旧 HEAD 日志回归通过。
- AC3: G-014 临时 HOME 安装保留 models.md 行、更新发行版行、重复安装不重复，rollback 可恢复。
- AC4: G-015 无账本目标证据回落并记录 target，有账本活跃/空闲目标保持原归属，kind 与 provability 不变。
- AC5: G-016 纯无账本外仓修改可经真实检查证据通过 H2；全量 unittest 通过，VERSION 与 CHANGELOG 为 10.1.6（五条）。
