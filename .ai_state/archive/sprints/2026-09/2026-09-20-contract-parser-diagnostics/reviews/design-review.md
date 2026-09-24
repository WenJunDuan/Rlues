---
schema_version: 1
mode: "design"
review_run_id: "86be1284-c9ab-4d37-af5a-b88c3a8ff4b2"
reviewer_target: "a9b127a6bb4606253"
packet_sha256: "ac5adb8d42e0db39e836571bdbc358a957d1bc2fd3d75bc020bf49c021729cff"
input_manifest_sha256: "93247cdfcad8e8aeefe87ceb9bab0e50bf987e4889eaee326c23edf672fc8f13"
native_output_ref: "reviews/_native/86be1284-c9ab-4d37-af5a-b88c3a8ff4b2-result.json"
verdict: "CONCERNS"
---

## Native review output

---
schema_version: 1
mode: design
packet_sha256: "ac5adb8d42e0db39e836571bdbc358a957d1bc2fd3d75bc020bf49c021729cff"
review_run_id: "86be1284-c9ab-4d37-af5a-b88c3a8ff4b2"
verdict: CONCERNS
finding_counts: {P0: 0, P1: 2, P2: 3}
dimensions: [spec, correctness, security, tests, overengineering]
---

被审: design.md rev 2 (c48cb9ea… = packet source_design_sha256) + review-packet.md rev 2。基线 4b0ba98，HEAD a243f91。定向复核。

## 首轮 findings 闭合核验（全部实测）

P0-1 闭合：写集三模板路径全存在（:13 均 ## Contract）；(b) 路线正当，代价仅在飞旧 packet 改标题，零小节独立报错给出路。
P1-1 闭合：窄规则 (?:AC|验收)(?=$|[:：]) 复跑全仓 3410 md：首轮 6 条活体命中全不识别，宽边界另 26 条命中全排除；正向 ## AC、## 验收:、## 验收： 识别。全仓窄规则剩 2 条命中均非门禁输入（resolveAcceptanceCriteria 只读 design 与显式链接 requirements）。
P1-2 闭合：Pi↔CC 四同源函数逐字相等实测（extractAcIds 277/277、acceptanceCriteria 778/774、validateTddEvidence 616/612、ACCEPTANCE_HEAD 765/761），整体 55 行分叉不冲突，按函数取范围今天即可写绿。
P2×5 闭合：行号实测无误；AC3 矛盾消除；成对 span 定死；安装态时点=ship 收口；字节钉由 AC7 承接。
AC 双射：design/packet 三种口径（现装解析、全文、未来窄规则）均恰好 AC1-AC8；本 sprint 自身 ship 不被新旧规则任一卡住。现存测试无断言 AC set mismatch 文本。

## P1-1 · AC7 函数枚举漏掉新引入的 acceptanceSections，替代判据覆盖面小于删掉的字节钉

Pi 的 acceptanceSections 与 ACCEPTANCE_HEAD_ALIASES 漂移时 acceptanceCriteria 文本仍相等，断言全绿而行为分叉。改法：AC7 同源集合 = {stripInlineCode, extractAcIds, acceptanceSections, acceptanceCriteria, validateTddEvidence} + ACCEPTANCE_HEAD/ACCEPTANCE_HEAD_ALIASES 常量行，逐一文本相等；新增同源函数同步入集。

## P1-2 · 「本 design.md 实档作夹具」路径耦合，ship 归档即断

sprint 归档移路径 → FileNotFound；design 改字即变夹具输入。现有测试套一律临时树造夹具。改法二选一写进 AC1：命中行字面量内联，或 git show <base_commit>:<path> 不可变快照。

## P2 / INFO

1. AC1 正向集未覆盖 ## 验收 :（空格+冒号）与 ## **AC** 粗体——窄 lookahead 均不识别，AC1 应显式声明。
2. roadmap 模板 ## 验收 (…) 新规则下不识别，无功能影响；gate-contracts.md 别名节写明「别名仅用于 design/packet，roadmap 不受约束」。
3. packet 审查焦点「四处活体命中」与 design 实列 6 条（2 条合成）不符，措辞级。

## 其余维度

Security fail-closed 保持（误 block 非误 pass）。Over-engineering 无越界（三个新符号均有当下消费者）。Spec coverage AC1-AC8 无 MISSING/EXTRA。Test risk：删钉划分与实文件一致；roadmap :97「由切片 5 删除」待按 AC6 改口。

两条 P1 均为 AC 措辞级修订，不推翻 rev 2 方案；改完可直接进 impl，无需第三轮全面审查。

VERDICT: CONCERNS