---
source_design_sha256: "a8ec4014f7c7db38ff396b329b66b2c4d150e8dbb70be68575f30128a0fb8a88"
mode: "design"
---

# Review Packet — contract parser diagnostics

## Decision

门禁的合同解析必须只认合同结构、认得下常用标题写法、失败时说清哪一层坏了。AC 标识提取收窄到验收小节并排除反引号/围栏引用；验收标题接受五个别名且报错列全；TDD 证据三类失败分层可区分。全部仍 fail-closed，只改判定的准确性与失败的可读性。附带接管切片 3 的字节断言移除（本切片先于切片 5 合法改 gate）。

## 验收标准

| AC | Roadmap | 判据 |
|---|---|---|
| AC1 | Q12#8 | `## AC` / `## 验收` 及边界变体在 CC/CX/Pi 被识别为验收小节；`## ACL 配置`、`## 验收流程说明` 不识别（负向） |
| AC2 | Q12#8 | 无小节报错逐字列全五个可接受标题；有小节但 0 条有效条目为另一条明确消息（负向钉死两层） |
| AC3 | Q12#7 | packet 的 AC 集只来自其验收小节结构；小节外合同外标识不再产生 extra/missing；design 侧行为回归不变 |
| AC4 | Q12#7 | 条目内反引号 span 的 AC 标识不进覆盖集；小节内围栏行不产生条目；design/packet/mapping 三消费点同规则 |
| AC5 | Q12#5 | TDD 空文件 vs 未解析出记录（含期望形状）、缺字段（record 序号+test_file+确切字段名）、时间序（三实际值）三层可区分；CC/CX 消息逐字同 |
| AC6 | 交叉项 | 切片 3 字节断言测试删除；Pi `_review-binding` == CC 不变量独立保留；roadmap 承接清单更正 |
| AC7 | 平行性 | AC1-AC5 行为以同一夹具驱动 CC 与 CX，判定与消息一致；Pi 仅同源函数补丁一致 |

## 审查焦点

- 别名边界 lookahead 是否足够（`验收` 后接汉字不误配）；现存 sprint 档案有无被新别名意外纳入合同解析的标题（design 风险节承诺 impl 期 grep 核实，审查可抽查）。
- packet 侧收窄到 `acceptanceCriteria(packet)` 后，双射校验对既有已 ship sprint 无追溯影响（门禁只验当前 sprint）。
- `stripInlineCode` 置空策略对未闭合反引号的行为。
- 分层诊断是否引入第二套模板/schema（Non-goal 红线）。
- 写集是否越界：三端 gate + 两个测试文件 + 三份 gate-contracts 文档。

## 证据入口

- 现状缺陷行号：design WHY 节（CC/CX/Pi 各消费点）。
- 字节断言现文：`vibeCoding/scripts/tests/athena999/test_state_review.py` 注释明言由合法改 gate 的切片移除。
- 基线：`4b0ba98`。
