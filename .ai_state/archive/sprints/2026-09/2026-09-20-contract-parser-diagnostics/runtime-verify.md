---
sprint_slug: "2026-09-20-contract-parser-diagnostics"
verified_at: "2026-09-20"
result: PASS
---

# Runtime Verify — contract parser diagnostics

实现合入 main（`fd9d1d0`，rebase 后 ff）后，以**真实 gate hook 进程**（发行文件原样，非测试探针路径*）对受控 git 夹具（/tmp/rv-fixture-rv-1789897346）实跑。CC=node delivery-gate.cjs / CX=python3 delivery-gate.py，payload 为 PreToolUse 实现写入（impl-entry 面）。

## 测试场景

| # | 场景 | 驱动 | CC | CX | 结论 |
|---|---|---|---|---|---|
| S1 | design 用 `## AC` 别名 + 有效条目 + 双射 packet | hook 进程 | 放行 exit=0 | 放行 exit=0 | 别名轴端到端生效 |
| S2 | design 无验收小节 | hook 进程 | block，报错逐字列全五标题+短别名边界说明 | 同 CC 逐字 | 分层第一层 |
| S3 | 小节存在但全占位 | hook 进程 | block，「小节已识别, 0 条有效条目」独立消息 | 同 CC 逐字 | 分层第二层，与 S2 消息不同 |
| S4a | packet 正文含合同外 AC7/AC9 引用、小节双射 AC1 | hook 进程 | 放行 | 放行 | 全文抓取污染消除 |
| S4b | packet 用旧惯例 `## Acceptance mapping` | hook 进程 | block，「review-packet 未识别到验收小节; 可接受标题: …」 | 同 CC 逐字 | 零小节独立报错，不再假 AC set mismatch |
| S5 | TDD 四层诊断（全注释/未解析/缺字段/时间序） | 进程级加载发行文件调 validateTddEvidence* | 四条消息互异、含 record #1 (test_file)+确切字段名+三实际时间值 | 与 CC 逐字相同 | 分层诊断全达 |

\* S5 说明：CC 的 validateTddEvidence 按设计不在 module.exports（导出面不变是本切片合同），故 CC 用 node Module 探针加载发行文件原文后调用、CX 用 sys.path 注入后 import 发行文件；两者执行的均为发行文件的真实代码路径。可达 hook 面的 S1-S4 全部走纯 hook 进程。

## 佐证

- 主仓合入后全套：test_contract_parsers 15/15 + test_state_review 52/52（主 agent 复跑）。
- generator 活体回归：baseline vs 新 gate 对 15 份现存 design/packet 跑 acceptance_criteria 集合零差异。
- ~~既有 8 条 discover 失败~~ 更正（review P2-2）：reviewer 以 `discover -p 'test_*.py'` 实测 123 tests 全 OK，generator 报告的 8 条基线失败未在主仓复现（疑为其 worktree 环境或 discover 参数差异），该豁免声明作废；当前判定基于全绿，无被掩盖的失败。
