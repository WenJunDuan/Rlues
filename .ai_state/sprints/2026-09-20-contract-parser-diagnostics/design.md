---
sprint_slug: "2026-09-20-contract-parser-diagnostics"
path: "System"
stage: "design"
author: "cc-main (revised after design review 563309c0 REWORK)"
base_commit: "4b0ba98"
---

# Contract parser diagnostics（Q12#5/#7/#8）

## WHY

门禁不读人的解释，只读合同文档的解析结果。三个解析缺陷让判定失真或失语，全部在当前源码逐行核实（行号为仓库副本）：

**#7 AC 标识从全文平面抓取，合同外字样进入约束集。** `extractAcIds` 对整段文本正则 `\bAC[0-9]+\b`（CC `delivery-gate.cjs:277`，CX `:923`，Pi `:277`）。design 侧已限定在验收小节（`:345`），但 packet 侧直接吃全文（`:347`；CX `:996-997`）：packet 正文一句「对照切片 3 的 AC5」即成 extra，双射校验假阳性 block。更深一层：`validateAcMapping` 从每条验收条目提取必须覆盖的 label（`:988-989`；CX `AC_LABEL:402` 同构），条目里反引号引用的测试名/历史 AC（如切片 5 承接项必然要写的「删除 \`test_…AC5…\` 断言」）会把无关 AC 拉进本 sprint 必须覆盖集，造成无证据可给的死 block。验收小节内的围栏代码行同理会被当作条目行扫描。

**#8 验收标题只认三个写法，报错还列不全。** `ACCEPTANCE_HEAD` 只认 done contract / acceptance criteria / 验收标准（CC `:765`，CX `:396-399`，Pi `:761`）。写 `## AC` 或 `## 验收` 的合同被判「无验收标准」；而 spec-gate 的报错文本（`:915`）只列出两个标题，连现在就接受的 done contract 都没说——作者按报错改也改不对。

**#5 TDD 证据诊断一刀切。** `validateTddEvidence`（CC `:616`，CX `:1272`，Pi `:612`）三处失败全是扁平消息：0 条记录只说 "contains no red-to-green records"（分不清文件为空、键名/缩进写错解析成 0 条、还是真没写）；缺字段只说 "missing red/implementation/green fields"（九字段合同，不说第几条记录、缺哪几个字段）；时间序违例不给三个实际值。与切片 3 修掉的 review 绑定「只甩字段名」同病。

**发行模板自身就写不出可识别的 packet 验收小节（design review P0-1）。** 三端 `templates/sprints/review-packet.md:13` 用 `## Contract`，切片 2/3 的实 packet 用 `## Acceptance mapping`——两者都不被 `ACCEPTANCE_HEAD` 识别。packet 侧一旦收窄到小节提取，按发行模板写的 packet 得到 `packetIds=[]`，报 AC set mismatch 却不提标题未识别。模板与报错必须与收窄同步修。

**交叉项：切片 3 的字节断言在本切片必然变红。** `test_review_binding_gate_export_diff_is_sprint_scoped_and_pi_matches_cc`（`test_state_review.py:1019`）把三端 gate 钉死在 `0ca066c`+单行导出差。注释写明由「真正开始改 gate 的切片」移除并预期是切片 5，但实施顺序令本切片先合法改 gate——移除义务由本切片承接，roadmap 同步更正。

## HOW

### AC 标识一律从合同结构提取（#7）

- packet 侧改为与 design 侧同构：`extractAcIds(acceptanceCriteria(packet).join('\n'))`。packet 零小节不复用 AC set mismatch，独立报错「review-packet 未识别到验收小节」并列全可接受标题（P0-1）。
- 三端 `templates/sprints/review-packet.md` 的 `## Contract` 改为 `## 验收标准`，发行默认即可被识别。已 ship sprint 的历史 packet 不受影响（门禁只验当前 sprint）。
- 反引号排除在**提取层**统一做：新增 `stripInlineCode(text)`（CX `strip_inline_code`），只置空**成对**反引号 span，落单反引号原样保留（P2-3 定死）；在 `extractAcIds` 与 `validateAcMapping` 的 label 循环入口应用。单处实现，三个消费点（design ids、packet ids、criterion labels）共用。
- `acceptanceCriteria` 的小节扫描加围栏状态：``` 开合之间的行不作为条目/表行收集。
- evidence `covers` 不动——显式 YAML 列表，无此病。

### 标题别名 + 分层零条目诊断（#8）

- `ACCEPTANCE_HEAD` 增加 `AC`、`验收` 两个别名。**别名边界严于全名**（P1-1）：`AC`/`验收` 仅在后随行尾或冒号（`:`/`：`）时成立——`## AC`、`## 验收:` 识别；`## AC 覆盖表`、`## 验收 流程`、`## AC-1`、`## AC(草案)`、本 design 自己的 `### AC 标识一律…` 小标题全部不识别（负向夹具，含本 design.md 实档）。全名三别名沿用现边界 lookahead 不变。
- 别名清单提为常量 `ACCEPTANCE_HEAD_ALIASES`（正则与报错文本同源），spec-gate 零条目报错分两层：
  - 未找到小节 → 列全五个可接受标题；
  - 小节存在但条目全为占位/空 → 明说「小节已识别、0 条有效条目」。
  - 实现：`acceptanceSections(text)` 返回 `{found, items}`，`acceptanceCriteria` 委托之，导出面不变。

### TDD 分层诊断（#5）

`validateTddEvidence` 消息按证据可得性分层，合同本身九字段不变、不加模板不加 schema：

- 0 条：文件仅空白/注释 → 「文件为空」；有内容但无 `- test_file:` 命中 → 报「内容未解析出记录」并给出期望的记录形状（首键 `- test_file:` + 八字段清单）。
- 缺字段：`record #N (test_file: X) missing: <确切字段名列表>`。
- 时间序：报出 red/implementation/green 三个实际值。
- CC/CX/Pi 消息逐字相同。

### 字节断言接管（交叉项）

删除 `test_…_export_diff_is_sprint_scoped_and_pi_matches_cc` 中钉死 gate 文件的三段（CC/Pi 单行差、CX 字节等于 `0ca066c`）；其中仍然成立的不变量「Pi `_review-binding.cjs` == CC」独立成 `test_pi_review_binding_matches_cc` 保留。Pi gate 的机械判据由 AC7 的函数文本相等断言承接（P1-2），不再立全文件字节钉。切片 5 承接项中仅字节钉一条转归本切片，helper 导出与 governance 复写消除仍归切片 5。

### 安装态同步时点（P2-4）

本切片改的是活门禁。仓库合入后，三端 gate 与 packet 模板的安装态同步在 **ship 收口时经用户授权执行**（与切片 3 惯例一致）；本 sprint 自身的 ship 由当时已安装的门禁判定，新解析规则自下一个 sprint 生效。写集不含安装态路径，同步动作单列不混入实现 diff。

## 允许写集

| 文件 | 变更 |
|---|---|
| `vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs` | #5/#7/#8 三组解析与诊断 |
| `vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py` | 同构同步（含 spec-gate 报错文本 `:598`） |
| `vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs` | 仅同源函数同步，不对齐其他既有分叉 |
| `vibeCoding/{claude/9.9.9/.claude,codex/9.9.9/.codex,pi-agent/plugin}/skills/pace/templates/sprints/review-packet.md` | `## Contract` → `## 验收标准`（P0-1） |
| `vibeCoding/scripts/tests/athena999/test_contract_parsers.py` | 新增，AC1-AC5、AC7 红→绿行为测试与函数文本相等断言 |
| `vibeCoding/scripts/tests/athena999/test_state_review.py` | 仅删字节断言测试并保留 Pi==CC `_review-binding` 不变量 |
| `vibeCoding/{claude,codex}/9.9.9/**/skills/pace/references/gate-contracts.md` + Pi 对应 | 文档：别名清单与诊断分层 |
| `.ai_state/`（sprint 档案、roadmap 记账） | 常规 |

Non-goals：不重造模板/schema；不动 gate helper 导出（切片 5）；不改 covers 语义；不消除 Pi gate 的既有分叉；不改 `_review-binding` 系；不在本切片同步安装态（ship 收口单列）。

## 验收标准

| AC | Roadmap | 可观察判据 |
|---|---|---|
| AC1 | #8 | `## AC`、`## 验收:`（行尾或冒号边界）在三端被识别；`## AC 覆盖表`、`## 验收 流程`、`## AC-1`、`## AC(草案)`、`## ACL 配置`、`## 验收流程说明` 均不识别；本 design.md 实档作夹具时其 HOW 小标题不产生验收小节 |
| AC2 | #8 | 无小节时报错逐字列全五个可接受标题；小节存在但 0 条有效条目时为另一条明确消息（两条不同消息，负向测试钉死） |
| AC3 | #7 | packet 的 AC 集只来自其验收小节结构；小节外合同外标识不再产生 extra/missing；packet 零小节报独立错误并列全标题；design 侧仍限定在验收小节 |
| AC4 | #7 | 验收条目内成对反引号 span 中的 AC 标识不进入必须覆盖集，落单反引号原样保留（负向夹具）；小节内围栏行不产生条目；design/packet/mapping 三消费点同规则 |
| AC5 | #5 | TDD 三类失败各自可区分：空文件 vs 未解析出记录（含期望形状）；缺字段报 record 序号+test_file+确切字段名；时间序报三个实际值。CC/CX 消息逐字相同 |
| AC6 | 交叉项 | 字节断言测试删除；Pi `_review-binding` == CC 不变量独立保留且全绿；roadmap 切片 5 承接清单同步更正 |
| AC7 | 平行性 | AC1-AC5 每个行为在 CC 与 CX 上用同一夹具驱动，判定与消息一致；Pi 的四个同源解析函数（extractAcIds / acceptanceCriteria 及标题常量 / validateTddEvidence / stripInlineCode）与 CC 文本相等，由测试机械断言 |
| AC8 | P0-1 | 三端 packet 模板含可识别验收小节标题；按发行模板新建的 packet 经 `validateReviewPacket` 不因标题落入 AC set mismatch |

## 测试场景（红→绿计划）

1. 别名标题正/负向 ×CC/CX + 本 design 实档夹具（AC1）；2. 零条目两层消息 ×2 端（AC2）；3. packet 正文合同外标识不再 extra + 零小节独立报错（AC3，先红）；4. 条目成对反引号引用不进覆盖集 + 落单反引号保留 + 围栏伪条目不收集（AC4，先红）；5. TDD 空文件/坏缩进/缺字段/时间序四夹具消息断言 ×2 端（AC5）；6. 删字节断言后全套仍绿 + Pi `_review-binding`==CC 独立测试（AC6）；7. Pi 四函数文本相等断言（AC7）；8. 模板渲染的 packet 过 `validateReviewPacket`（AC8）。

## 风险

- 别名扩大识别面：边界已收窄到行尾/冒号；impl 第一步仍 grep 三端包与 `.ai_state` 现存文档核实无 `## AC`/`## 验收` 后随行尾/冒号的非合同标题。
- packet 侧收窄使旧标题惯例（`## Acceptance mapping`）失效：仅影响未 ship 的在飞 packet；本切片后新 packet 按模板即合规，零小节报错会直接给出全部合法标题。
- 模板属发行面：模板改动随本切片 ship 一并进入候选包，不单独发布。
