---
sprint_slug: "2026-09-20-contract-parser-diagnostics"
path: "System"
stage: "design"
author: "cc-main"
base_commit: "4b0ba98"
---

# Contract parser diagnostics（Q12#5/#7/#8）

## WHY

门禁不读人的解释，只读合同文档的解析结果。三个解析缺陷让判定失真或失语，全部在当前源码逐行核实（行号为仓库副本）：

**#7 AC 标识从全文平面抓取，合同外字样进入约束集。** `extractAcIds` 对整段文本正则 `\bAC[0-9]+\b`（CC `delivery-gate.cjs:277`，CX `:923`，Pi `:277`）。design 侧已限定在验收小节（`:345`），但 packet 侧直接吃全文（`:347`；CX `:996-997`）：packet 正文一句「对照切片 3 的 AC5」即成 extra，双射校验假阳性 block。更深一层：`validateAcMapping` 从每条验收条目提取必须覆盖的 label（`:989-990`；CX `AC_LABEL:402` 同构），条目里反引号引用的测试名/历史 AC（如切片 5 承接项必然要写的「删除 \`test_…AC5…\` 断言」）会把无关 AC 拉进本 sprint 必须覆盖集，造成无证据可给的死 block。验收小节内的围栏代码行同理会被当作条目行扫描。

**#8 验收标题只认三个写法，报错还列不全。** `ACCEPTANCE_HEAD` 只认 done contract / acceptance criteria / 验收标准（CC `:765`，CX `:396-399`，Pi `:761`）。写 `## AC` 或 `## 验收` 的合同被判「无验收标准」；而 spec-gate 的报错文本（`:916`）只列出两个标题，连现在就接受的 done contract 都没说——作者按报错改也改不对。

**#5 TDD 证据诊断一刀切。** `validateTddEvidence`（CC `:616`，CX `:1272`，Pi `:612`）三处失败全是扁平消息：0 条记录只说 "contains no red-to-green records"（分不清文件为空、键名/缩进写错解析成 0 条、还是真没写）；缺字段只说 "missing red/implementation/green fields"（九字段合同，不说第几条记录、缺哪几个字段）；时间序违例不给三个实际值。与切片 3 修掉的 review 绑定「只甩字段名」同病。

**交叉项：切片 3 的字节断言在本切片必然变红。** `test_review_binding_gate_export_diff_is_sprint_scoped_and_pi_matches_cc`（`test_state_review.py:1019`）把三端 gate 钉死在 `0ca066c`+单行导出差。注释写明「合法改 gate 的切片负责移除」并预期是切片 5，但实施顺序令本切片先合法改 gate——移除义务由本切片承接，roadmap 同步更正。

## HOW

### AC 标识一律从合同结构提取（#7）

- packet 侧改为与 design 侧同构：`extractAcIds(acceptanceCriteria(packet).join('\n'))`。packet 的 AC 双射表本就在验收小节结构里，普通正文不再参与。
- 反引号排除在**提取层**统一做：新增 `stripInlineCode(text)`（CX `strip_inline_code`），在 `extractAcIds` 与 `validateAcMapping` 的 label 循环入口把 \`…\` span 置空后再匹配。单处实现，三个消费点（design ids、packet ids、criterion labels）共用。
- `acceptanceCriteria` 的小节扫描加围栏状态：``` 开合之间的行不作为条目/表行收集。
- evidence `covers` 不动——显式 YAML 列表，无此病。

### 标题别名 + 分层零条目诊断（#8）

- `ACCEPTANCE_HEAD` 增加 `AC`、`验收` 两个别名，沿用现有边界 lookahead（`## ACL`、`## 验收流程` 不会误配，负向测试钉死）。
- 别名清单提为常量 `ACCEPTANCE_HEAD_ALIASES`（正则与报错文本同源），spec-gate 零条目报错分两层：
  - 未找到小节 → 列全五个可接受标题；
  - 小节存在但条目全为占位/空 → 明说「小节已识别、0 条有效条目」，不再让作者怀疑标题。
  - 实现：`acceptanceSections(text)` 返回 `{found, items}`，`acceptanceCriteria` 委托之，导出面不变。

### TDD 分层诊断（#5）

`validateTddEvidence` 消息按证据可得性分层，合同本身九字段不变、不加模板不加 schema：

- 0 条：文件仅空白/注释 → 「文件为空」；有内容但无 `- test_file:` 命中 → 报「内容未解析出记录」并给出期望的记录形状（首键 `- test_file:` + 八字段清单）。
- 缺字段：`record #N (test_file: X) missing: <确切字段名列表>`。
- 时间序：报出 red/implementation/green 三个实际值。
- CC/CX/Pi 消息逐字相同。

### 字节断言接管（交叉项）

删除 `test_…_export_diff_is_sprint_scoped_and_pi_matches_cc` 中钉死 gate 文件的三段（CC/Pi 单行差、CX 字节等于 `0ca066c`）；其中仍然成立的不变量「Pi `_review-binding.cjs` == CC」独立成 `test_pi_review_binding_matches_cc` 保留。不再立新的字节钉——本切片改动面由 design 写集 + review 现场核验约束。切片 5 承接项中仅此一条转归本切片，helper 导出与 governance 复写消除仍归切片 5。

## 允许写集

| 文件 | 变更 |
|---|---|
| `vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs` | #5/#7/#8 三组解析与诊断 |
| `vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py` | 同构同步 |
| `vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs` | 仅同源函数同步，不对齐其他既有分叉 |
| `vibeCoding/scripts/tests/athena999/test_contract_parsers.py` | 新增，AC1-AC5 红→绿行为测试 |
| `vibeCoding/scripts/tests/athena999/test_state_review.py` | 仅删字节断言测试并保留 Pi==CC 不变量 |
| `vibeCoding/{claude,codex}/9.9.9/**/skills/pace/references/gate-contracts.md` + Pi 对应 | 文档：别名清单与诊断分层 |
| `.ai_state/`（sprint 档案、roadmap 记账） | 常规 |

Non-goals：不重造模板/schema；不动 gate helper 导出（切片 5）；不改 covers 语义；不消除 Pi gate 的既有分叉；不改 `_review-binding` 系。

## 验收标准

| AC | Roadmap | 可观察判据 |
|---|---|---|
| AC1 | #8 | `## AC` / `## 验收`（含 `:`、`：`、括号等边界变体）在三端被识别为验收小节；`## ACL 配置`、`## 验收流程说明` 不被识别（负向） |
| AC2 | #8 | 无小节时报错逐字列全五个可接受标题；小节存在但 0 条有效条目时报错明确区分该情形（两条不同消息，负向测试钉死） |
| AC3 | #7 | packet 的 AC 集只来自其验收小节结构；正文（小节外）出现合同外的 AC+数字标识不再产生 extra/missing；design 侧行为回归不变 |
| AC4 | #7 | 验收条目内反引号 span 中的 `ACn` 不进入必须覆盖集；小节内围栏代码行不产生条目；design/packet/mapping 三个消费点同规则 |
| AC5 | #5 | TDD 三类失败各自可区分：空文件 vs 未解析出记录（含期望形状）；缺字段报 `record #N (test_file: X) missing: 字段名`；时间序报三个实际值。CC/CX 消息逐字相同 |
| AC6 | 交叉项 | 字节断言测试删除；`Pi _review-binding == CC` 不变量独立保留且全绿；roadmap 切片 5 承接清单同步更正 |
| AC7 | 平行性 | AC1-AC5 每个行为在 CC 与 CX 上用同一夹具驱动，判定与消息一致；Pi 仅对同源函数比对补丁一致性 |

## 测试场景（红→绿计划）

1. 别名标题正/负向 ×2 端（AC1）；2. 零条目两层消息 ×2 端（AC2）；3. packet 正文 AC 引用不再 extra（AC3，先红：现状 block）；4. 条目反引号 `AC5` 引用不进覆盖集（AC4，先红：现状要求覆盖）；5. 围栏内伪条目不收集（AC4）；6. TDD 空文件/坏缩进/缺字段/时间序四夹具消息断言 ×2 端（AC5）；7. 删字节断言后全套仍绿 + Pi==CC 独立测试（AC6）。

## 风险

- 别名扩大识别面：既有文档中恰有 `## AC`/`## 验收` 标题的小节会**开始**被当作合同解析——对本仓 sprint 档案 grep 核实无此类标题后再合入（impl 期第一步）。
- packet 侧收窄提取面理论上可能使既有 packet 的 AC 集变化——仅影响未 ship 的在飞 sprint，本切片自身的 packet 按新规则书写。
