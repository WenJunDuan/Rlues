# Session Log — review-binding-preflight

- 2026-09-20：roadmap 第三项启动（Q12#6/#9/#10）。切片 2 已交付并清理分支，main 领先 origin 19 提交待推。
- 基线：`0ca066c`。
- 用户授权：本切片完成后推送 main，并把 CC/CX 有改动的 hook 同步覆盖到安装态。

## 现场核实（写设计前逐行读源码）

- **#6 自毁**：`prepare` 先经 `liveInput` 对 `input_paths` 算 `input_manifest_sha256`（:120），随后 `append` 把 athena-review 标记写进 `session-log.md`（:44-51）。若 session-log 在输入清单里，哈希刚算完就被自己改掉，bind/accept 必报漂移。
- **#6 诊断贫乏**：`assertLive`（:82-90）只抛字段名，如 `review input changed: packet_sha256`，不说是哪个文件、期望值与现值各是什么。本会话两次撞上，都要读 hook 源码才定位。
- **#9 延迟暴露**：`accept`（:177）把 `prepared.base_commit` 写成「Reviewed implementation commit」，而 `validateReviewBinding`（delivery-gate:541）要求它等于 manifest 的 `implementation_commit`。manifest 过期时不在 prepare 报错，拖到 ship 才炸，且不指明哪一侧过期。
- **#9 静默改写**：`accept`（:176）用正则从 reviewer 原文中删除既有的三行 Reviewed 绑定再换上自己的，属于对审查原文的静默改写。
- **#10 无出口**：`indexGovernanceSha256`（delivery-gate:508-512）未导出 CLI，写 manifest 只能手工复现算法。本会话算 `sourceDiffSha256` 时正因给错定义而白跑一轮审查。

<!-- athena-review:{"author_target":"","base_commit":"0ca066c2f42a161ed913fc76419e4e2b0370ec55","event":"prepared","evidence_docs":{},"evidence_ids":[],"input_manifest_sha256":"8552a725a1fa4b8e6dcd73728fb8f655420ebfa8ae9d9bd42ec8038e9a03b9bd","input_paths":[".ai_state/sprints/2026-09-20-review-binding-preflight/design.md",".ai_state/sprints/2026-09-20-review-binding-preflight/review-packet.md"],"mode":"design","packet_sha256":"bd61b0a442c51e6939f5e4c3e7b8dec0beafc705bcad0d758aefb2e94f3eeeba","recorded_at":"2026-09-20T05:44:21.200Z","review_run_id":"208cfc50-6523-4550-b840-ac0da10815f2","schema_version":1} -->

<!-- athena-review:{"dispatch_receipt_ref":"reviews/_native/208cfc50-6523-4550-b840-ac0da10815f2-dispatch.json","dispatch_receipt_sha256":"78f13e0c6a63658e024661402462311716bc878ad3f54f7ffc1e0e81308aaf3c","event":"bound","recorded_at":"2026-09-20T05:44:59.680Z","review_run_id":"208cfc50-6523-4550-b840-ac0da10815f2","reviewer_target":"a7874f964c12426f9"} -->

<!-- athena-review:{"event":"received","native_output_ref":"reviews/_native/208cfc50-6523-4550-b840-ac0da10815f2-result.json","native_output_sha256":"7c6dc4f262de4014a0785004d628dd773aea4739f64993ade087050548410e9d","output_ref":"reviews/design-review.md","output_sha256":"adb90c55a2324962873e654d6becc4145b453c0086c35d7d2fd4f47a95fc9266","recorded_at":"2026-09-20T05:51:34.340Z","review_run_id":"208cfc50-6523-4550-b840-ac0da10815f2","reviewer_target":"a7874f964c12426f9","verdict":"REWORK"} -->
- 2026-09-20：设计审查 run `208cfc50` 返回 **REWORK**（3×P0 + 3×P1 + 3×P2），已 accept。三条 P0 全部实证属实：
  - **我把一个有测试保护的特性当成了缺陷**。`accept` 删除 reviewer 自带的 Reviewed 绑定行不是「静默改写」，而是有意去重，用来保证门禁 `delivery-gate.cjs:525-527` 的「恰好一次」规则，回归测试是 `test_accept_deduplicates_reviewed_binding_lines`。该修复的提交 `4894588 fix(review 9.9.9): 去重正式件绑定行` 就在我会话开头读过的 git log 里。原 AC4 已整条删除——它既越界（不对应任何 roadmap 条目）又会破坏门禁不变量。
  - AC2 原样不可实现：`liveInput` 把逐项 map 丢弃只存折叠摘要，prepared row 无逐输入哈希。改为新增持久化 `input_hashes`，并按「声明路径可逐项归因 / 聚合摘要只能报轴名」拆分。
  - AC5 与 AC6 互斥：`indexGovernanceSha256` 不在 `module.exports`，要用就必须改 delivery-gate。改为把允许差异精确限定为两个导出名，逐行断言其余不变。
- 另修正：排除集不止 session-log，还须含 `_index.md` 与上一轮的 `reviews/<mode>-review.md`（后者最阴——accept 在自己的 assertLive 之后才写，故拖到 ship 经 validateCurrent 才炸）；且排除必须作用于**存储的** input_paths。
- 另发现真 bug：Pi 的 `cc-core/_review-binding.cjs` 是 dedup 之前的旧副本，完全没有 strip，遇到 reviewer 自带绑定行会产生重复并被门禁拦。已纳入本切片修复。

<!-- athena-review:{"author_target":"","base_commit":"0ca066c2f42a161ed913fc76419e4e2b0370ec55","event":"prepared","evidence_docs":{},"evidence_ids":[],"input_manifest_sha256":"a09f0777ce832fce51f0b3a9cb3c61148779eda8da8a036767cdd4f17e960e3c","input_paths":[".ai_state/sprints/2026-09-20-review-binding-preflight/design.md",".ai_state/sprints/2026-09-20-review-binding-preflight/review-packet.md"],"mode":"design","packet_sha256":"d7c306ecbb167e951d60a77c571a39488bc0600a461f408be59453fa2c11797e","recorded_at":"2026-09-20T05:53:42.813Z","review_run_id":"6fa2c766-3786-4802-98b6-f640761f0432","schema_version":1} -->

<!-- athena-review:{"dispatch_receipt_ref":"reviews/_native/6fa2c766-3786-4802-98b6-f640761f0432-dispatch.json","dispatch_receipt_sha256":"ba3c6b0986cc5c323eea1c7842a9f5864de4b6adb342f5fd8cf028241a998de4","event":"bound","recorded_at":"2026-09-20T05:54:11.753Z","review_run_id":"6fa2c766-3786-4802-98b6-f640761f0432","reviewer_target":"a71221739be2a76e6"} -->

<!-- athena-review:{"event":"received","native_output_ref":"reviews/_native/6fa2c766-3786-4802-98b6-f640761f0432-result.json","native_output_sha256":"74f4b43591f32638ffbd91424716d4ff3ed8415d60462f417ba31d7f52a5b752","output_ref":"reviews/design-review.md","output_sha256":"2a4635dc5bfa8fa733bd11b80a8175105a57bc2c7a12cb4563c6020ca87c4995","recorded_at":"2026-09-20T06:03:56.987Z","review_run_id":"6fa2c766-3786-4802-98b6-f640761f0432","reviewer_target":"a71221739be2a76e6","verdict":"CONCERNS"} -->
- 2026-09-20：定向复核 run `6fa2c766` 返回 CONCERNS，3×P0 与 3×P1 全部 CLOSED，新出 3×P1 已按复核给的确切改法逐条落实：
  - 治理子命令的 `_index.md` 解析必须走门禁的规则（`tryRepoRoot` + `findAiState`）而非 `input.context`。已实测：在本项目 worktree 里两者分别解析到 worktree 根与主仓，且两份 `_index.md` 此刻已不同——用 CLI 惯用写法会打印门禁根本不读的哈希。
  - `input_hashes` 必须持久化 `liveInput` 的**整个** inputs map（声明路径 + snapshot 轴），否则聚合轴连轴名都报不出。
  - WHY 提到 `evidence_ids` 却无对应 AC；已把 `evidence_docs`/`evidence_ids` 纳入 AC2（两者本就带逐项数据，只需 filter）。
- 另并入 P2：AC5 的逐行断言声明为 sprint 范围，切片 5 动 gate 时负责移除；零输入 prepare 合法（整个测试套件都这么用），失败条件精确化为「声明非空但排除后为空」；路径按解析后比较。
- **不开第三轮设计审查**：剩余全为子句级澄清且复核已给逐条改法，已照抄落实；设计与代码的一致性交由 implementation review 现场核。
- 2026-09-20：grok 施工完成（65 轮 / $1.72 / end_turn / 6 commit），测试 40→52 全绿。主 agent 核实：门禁两端差异确为单行导出名、`delivery-gate.py` 未动、Pi `_review-binding.cjs` 已与 CC 字节同一（修好去重缺失）、禁改文件未触碰。
- 2026-09-20：AC4 关键点主 agent 单独实测——从自带不同 `_index.md` 的 linked worktree 调用 `governance`，输出哈希 `c092c488…` 与主仓及门禁权威值三者一致，两端输出逐字节相同。证明它读的是门禁会读的那份文件。
- 2026-09-20：runtime-verify run `d35b4c47408a411a87c546613a24cdc7` PASS（11 个目标场景在受控 bundle 实跑；AC5 的 git 历史断言按前例留源码工作区）。已合入主仓 `baf5d9c`。
- 2026-09-20：**记录一条待审判断题**：grok 在 `governance` 里复写了门禁 `tryRepoRoot`/`findAiState` 约 20 行路径解析而非 import（验收只许导出两名）。治理哈希本身是 import 的未重写。本切片的立意正是「别重抄权威算法」，此处留了新的重抄；但解析属稳定基础设施且有 worktree 回归兜底。主 agent 不单方改写，交实现审查定级。
- 2026-09-20：polish PASS。删除 `mapDiffs` 里自相矛盾的死守卫（`Object.keys(x||{})` 防 null 但下一行就无保护索引 `x[key]`）；补三处非显然决策的注释，其中 `gateRepoRoot` 那处最关键——有人改成 `input.context` 就会静默重新引入 worktree 错哈希。三份 gate-contracts 各补一句记录自排除（AC1 引入了两个操作者可见行为，合同文档原本无从预知），主 agent 认可此为合同应尽义务而非范围蔓延。
- 2026-09-20：路径解析复写经逐行比对判定**忠实**（含最易丢的 2026-09-07 `.git` 边界停止），组合语义等价。仍原样交独立 review 定级，不由作者一方裁定。
- 2026-09-20：四项字节不变量主 agent 复核成立：两处门禁各只差一行导出名、`delivery-gate.py` 未变、Pi 与 CC 同一、`accept` 函数体未变。测试 polish 前后均 52/52。

<!-- athena-review:{"author_target":"","base_commit":"baf5d9cd5c7422aa1f63a72aade09dab07f0f1f1","event":"prepared","evidence_docs":{".ai_state/sprints/2026-09-20-review-binding-preflight/cleanup-pass.md":"3f1d2f823ae98c8cc6be74651780d9f9f17691510454adf728dc32162369ecc3",".ai_state/sprints/2026-09-20-review-binding-preflight/runtime-verify.md":"85407a3db14969ffbd12b9eafc31dfadc1d6acf75a55c1e8649897966b28e4fe"},"evidence_ids":["toolu_013K6u763QLZoogRdt6yk6YK","toolu_01BwurttyVPxEQrdj7JnDYVf","toolu_01DpYHdwqziG7VkBJvBTSu8o","toolu_01GwQf3bkbhnSrHdnSmkZ3v7"],"input_manifest_sha256":"75b178243a9a1a4d636aa34656ba8e4b7d23dbd5ca72f3c47c437c397178de43","input_paths":[".ai_state/architecture/ARCHITECTURE.md",".ai_state/sprints/2026-09-20-review-binding-preflight/cleanup-pass.md",".ai_state/sprints/2026-09-20-review-binding-preflight/design.md",".ai_state/sprints/2026-09-20-review-binding-preflight/review-packet.md",".ai_state/sprints/2026-09-20-review-binding-preflight/runtime-verify.md"],"mode":"implementation","packet_sha256":"ecf568bb53e225169bb87b6e86f928e95e7f98d512fc3429f6f91b93b35b8b0c","recorded_at":"2026-09-20T07:20:14.266Z","review_run_id":"cdfb7313-3b66-4914-a1a3-9d81353dc08f","schema_version":1} -->

<!-- athena-review:{"dispatch_receipt_ref":"reviews/_native/cdfb7313-3b66-4914-a1a3-9d81353dc08f-dispatch.json","dispatch_receipt_sha256":"e458c30dbb9456ae361a0cf21246aafc571fcf20308945a4c4f44bc382aa3edc","event":"bound","recorded_at":"2026-09-20T07:21:18.240Z","review_run_id":"cdfb7313-3b66-4914-a1a3-9d81353dc08f","reviewer_target":"ad2b07493d2c787aa"} -->
- 2026-09-20：implementation review run `cdfb7313-3b66-4914-a1a3-9d81353dc08f` 已 bind 到只读 reviewer `ad2b07493d2c787aa`。简报明示实现由外部执行器所写、仅经一次 polish，并把路径解析复写这条判断题原样交它定级（要求自行复算忠实性，不接受转述）。

<!-- athena-review:{"event":"accepted","native_output_ref":"reviews/_native/cdfb7313-3b66-4914-a1a3-9d81353dc08f-result.json","native_output_sha256":"72bec515f380441655e8a5c26682594f9c83574fb1ea046bb297c04b754a2543","output_ref":"reviews/implementation-review.md","output_sha256":"bba5068aa54405d837c0d1a81f79b0364028df95c70cc5c941e223df5877d432","recorded_at":"2026-09-20T07:28:53.872Z","review_run_id":"cdfb7313-3b66-4914-a1a3-9d81353dc08f","reviewer_target":"ad2b07493d2c787aa","verdict":"PASS"} -->
