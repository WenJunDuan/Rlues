---
sprint_slug: "2026-09-21-writer-provenance-and-repo-boundary"
path: "System"
stage: "design"
author: "cc-main (rev 4: 38a8f5c6 三条闭合——schema 扩展、判定次序、收紧面入表)"
base_commit: "9784d8b"
---

# Writer provenance 与仓库边界（Q12#1/#2/#16 + 切片 3 承接②）

## WHY（两轮复核确认全部属实）

**#1** 外部写者唯一出口 = 裸布尔 `skip_impl_subagent_check`（gate:1245/py:1859/pi:1208），零 provenance；`external-writer.json` 三端零命中。**#2** `harness_target_outside_repo` 仅 2 个 worktree 豁免消费者（CC `subagent-worktree-check.cjs:104`、CX `subagent-worktree-audit.py:151`），gate 不读、无 sprint 归属。**#16** tracker 落账依赖可变全局指针（`currentSprint:37`，Start 端是事故根因），redirect 吞异常（:33）、`.git` 边界丢事件（:17→:135）。**承接** `tryRepoRoot:447`/`findAiState:28` 不在 exports:1488；`_review-binding:275-296` 复写。

## HOW

### 回执叠加制 + 账本/证据拆层（P0 两轮的合并落点）

- **规则 0（叠加，rev 3 落点）**：`external-writer.json` **存在即校验**（`validateExternalWriter`），与 generator 链检查相互独立叠加——mixed writer sprint（本 sprint 即首例）两者都必须过。三态只回答「缺 generator 链时什么可替代」。
- **判定次序（rev 4，P1-1）**：规则 0 **先于** `requireGeneratorEvidence` 执行——回执损坏且链断裂时报 M1-M7（回执错优先），不报 M8；三端同序，保证 AC6 逐字可判定。
- **validateLedgerIntegrity（无条件，作用域定死）**：`subagent-assignments.jsonl` / `subagent-events.jsonl` 各自**存在时**逐行 exact-key schema 校验（缺失文件→沿用现状 `requireFile` 语义仅在需要该文件的状态触发；存在但零行→按现状抛；单侧存在→存在侧照验，缺失侧仅在状态①需要时抛）。**lifecycle 时序校验保持现状作用域=仅 `role` 为 generator 的链**（不推广到其他 role——7 个已 ship sprint 账本回归约束）。generator 判定按 `String(role).toLowerCase()==='generator'` 归一（防大小写洗态）；其他 role 值仅 schema 校验、不参与三态。
- **requireGeneratorEvidence（三态，编号固定见下表）**：
  - **状态①** assignments 含 generator 行 → 链必须完整；**flag 无效**；断裂 → block（消息 M8）。
  - **状态②** 无 generator 行且回执存在 → 回执即链的替代（回执校验本身由规则 0 无条件执行）。
  - **状态③** 无 generator 行且无回执 → flag=true 且 path ∉ {Refactor,System} 放行；否则 block（消息 M9）。
- call site `:1245` 外层 flag 短路删除。

**八格矩阵（正文权威，测试按此编号）**：

| 格 | generator 行 | 回执 | flag | path | 判定 |
|---|---|---|---|---|---|
| G1 | 有·链完整 | 无 | 任意 | 任意 | ①通过（flag 无效不放大权限） |
| G2 | 有·链完整 | 有 | 任意 | 任意 | ①通过 且 规则 0 校验回执（叠加） |
| G3 | 仅非 generator 行 | 有 | 任意 | 任意 | ②，且账本存在行全部 schema 校验（不因回执失效） |
| G4 | 无 | 无 | true | 绿区 | ③放行（既有语义） |
| G5 | 无 | 无 | true | R/S | block M9（先红：今日放行） |
| G6 | 无 | 无 | false | 任意 | block（既有 `no role=generator assignment found` 保持） |
| G7 | 有·链断裂 | 无/合法 | true | R/S | block M8（flag 无效；出口=续跑至真实 Stop，或按外部接管重新集成——新回执+新 evidence；禁删改账本行） |
| G8 | 无 | 有 | true | 任意 | ②（flag 被忽略） |
| G9 | 有·链断裂 | 无/合法 | true | 绿区 | block M8（**收紧**：今日 `:1245` 外层短路放行；flag 在状态①一律无效，绿区不例外） |
| G10 | 任意 | 任意 | 任意 | 任意 | 账本存在坏行/零行 → M12 或既有 `contains no records`（**收紧**：今日 flag=true 时整体短路不校验） |

### validateExternalWriter（#1）

`sprints/<slug>/external-writer.json`，字段与消息见附录 A。要点：
- `integration_commit`：`git merge-base --is-ancestor` 现场验（机械；仅证明进入本仓历史，不证明作者——免责句入 gate-contracts）。
- `evidence_tool_use_id`：evidence.yaml 恰一条命中（0/≥2 → block）且经 `inputBinding.currentRecord`（`:245` 同款）**现场重算** current+pass；`inputBinding.required(sprintDir)` 为假 → block（M7）。**FIELDS 不含 HEAD**（`_input-binding.cjs:128`：source/design/environment 三 sha）——ancestor 检查与 evidence 重算正交，ship 记账移动 HEAD 不失效 evidence（明文，防实现者误加 HEAD 绑定）。
- **施工时序（明文合同）**：外部 worktree 内采集的 evidence 不可迁移；顺序=整合进主仓 → 冻结 design.md → 主仓复跑验证生成 evidence → 写回执。design.md 后续任何编辑使全部已采 evidence 变 non-current（这是机制而非缺陷）。

### containment（#2）

- 伴随字段 `harness_target_outside_repo_sprint: "<slug>"`。三分支：匹配当前 slug=合法（impl+ship 全程）；不匹配=stale block（M10）；flag=true 而字段缺失=block（M11）。**gate 落点（P2-3）**：`validateImplEntry`（CC `:1099-1105` 区段，对实现写入）与 `validateShip`（`:1199` 起）各一处，与 `requireGeneratorEvidence` 的 `:1245` 同等精度；CX/Pi 对应同构位置。
- **豁免消费者同步（rev 3）**：CC `subagent-worktree-check.cjs` 与 CX `subagent-worktree-audit.py` 的豁免判据同步改为「flag=true **且**伴随字段==当前 slug」——消除 stale 下「spawn 豁免、写入被拦」的空转死锁与双消费者分叉。两文件入写集。
- ship 时 flag=true → session-log 须含 canonical 备份记录行（附录 A 格式 R1：`备份: <绝对路径>`）且该路径 existsSync 非空目录；**时序声明：ship 门禁通过前不得删除备份**（用户验后删惯例移到 ship 后）；判据依赖机器本地状态，如实注明。历史记法不受追溯（gate 只验当前 sprint）；夹具=新格式正例 + 缺记录/路径已删两负向。
- no-change 断言：drift 判定本体零改动，flag sprint 下仓外写入不产生 drift block（fixture）。
- 治理哈希：containment 两字段**不入** `INDEX_GOVERNANCE_FIELDS`（Non-goal——与 flag 同为 agent 可写，伪造面同级；免责句与 ancestor 同处 gate-contracts）。

### tracker 落账归属（#16，仅 CC；事故根因在 Start 端）

1. **SubagentStart（修复力所在）**：事件 cwd 为 linked worktree 时读 worktree `_index` 的 slug，且主仓 `sprints/<slug>/` 目录实存 → 用之；否则主仓指针。最小复现序列（AC4 先红）：主仓指针指向 sprint-B 时于 sprint-A 的 worktree 内触发 Start——今日落 B（错），改后落 A。
2. **SubagentStop**：优先该 agent_id 的 assignment 行所在 sprint（候选=主指针 sprint 与 worktree slug 两目录）；无 → 既有 `startLocations` 唯一匹配；再无 → 同 Start 规则。（防御性排序，不宣称复现事故——rev 3 更正因果表述。）
3. 每条事件行加 `"sprint_source"` 审计字段，值域枚举 `assignment|worktree-index|main-index`。**同步扩展三端 event schema（P0-1 必做）**：`validateEvent` 的 `exactKeys`（CC `delivery-gate.cjs:116-117`、CX `delivery-gate.py:302-304`、Pi 同源）新增该键为**可选**——旧行缺该键仍合法（in-flight sprint 新旧行混存），值存在时必须在枚举内，否则 M12。漏此步则 tracker 写出的每条新事件在三端皆判坏行（手写 fixture 测不到，测试绿而系统砖）。**残余如实声明**：worktree `_index` 是分支提交版，未提交 spawn 携带旧 slug 的错位不可根除，经审计字段可判别可纠正；「spawn 前提交 `_index`」为流程建议入 gate-contracts，不做代码强制。
4. redirect 失败：stderr + 事件行 `"redirect":"failed"`；`.git` 边界丢事件：stderr 痕迹。CX/Pi 不改（负向断言）。

### 导出与复写消除（承接）

exports 增两名；`_review-binding` 复写删除，替换保持**两段式回退契约**：`const root = gate.tryRepoRoot(cwd) || ''; const aiState = (root && gate.findAiState(root)) || gate.findAiState(cwd) || '';`（rev 3：保留 `|| findAiState(cwd)` 回退，与原 `gateAiState(root) || gateAiState(cwd)` 及 gate `main():1455` 同形；`findAiState` 不裸传空值）；AC5 用例：无仓、root 为空、`.ai_state` 低于 repo root、`.git` 边界。CC==Pi 字节同改；CX 零改动。

## 附录 A：canonical 字段与消息（grok 逐字实现，三端一致）

| # | 触发 | block 消息（CC/CX 逐字同，英文） |
|---|---|---|
| M1 | schema_version ≠ 1 | `external-writer schema_version must be 1` |
| M2 | executor.tool/model 空 | `external-writer executor tool/model missing` |
| M3 | dispatch_ref/receipt_ref 缺失或空文件 | `external-writer <field> missing or empty: <path>; if this sprint had no external writer, delete external-writer.json` |
| M4 | receipt_summary 空/占位 | `external-writer receipt_summary is placeholder or empty` |
| M5 | original_commits 元素非 40-hex | `external-writer original_commits entries must be 40-hex` |
| M6 | integration_commit 非 ancestor | `external-writer integration_commit is not an ancestor of HEAD: <sha>` |
| M7 | evidence 非恰一条 current+pass 或 required()=false | `external-writer evidence not uniquely bound and currently verifiable: <id>` |
| M8 | G7 断裂链 | `generator lifecycle incomplete for agent_id=<id>; resume it to a real SubagentStop or reintegrate via external-writer.json with fresh evidence; ledger rows must not be edited` |
| M9 | G5 红区裸 flag | `red-zone sprint requires a complete generator chain or external-writer.json; skip_impl_subagent_check alone is not admissible` |
| M10 | stale 伴随字段 | `harness_target_outside_repo left over from sprint <slug>; reset both fields before implementation writes` |
| M11 | flag=true 无伴随字段 | `harness_target_outside_repo requires harness_target_outside_repo_sprint: <current slug>` |
| M12 | 账本坏行 | `subagent ledger row invalid in <file>: <reason>` |
| M13 | ship 备份记录缺失/路径不存在 | `outside-repo sprint requires a backup record line (备份: <absolute-path>) whose path exists and is non-empty` |
| R1 | 备份记录行格式 | `备份: <路径>`（session-log 独立一行）。路径形态：允许 `~` 前缀（实现按 `os.homedir()` 展开后再验）；目标须为**目录**且非空（manifest 等单文件记法不满足，须记其所在目录）；相对路径拒绝 |

## 允许写集

三端 gate（CC/Pi 同源函数同改 + CX 同构）；`_review-binding.cjs` CC+Pi；`subagent-tracker.cjs`（CC）；**`subagent-worktree-check.cjs`（CC）+ `subagent-worktree-audit.py`（CX）**（rev 3 增）；`test_writer_provenance.py` 新建 + `test_state_review.py` 仅增用例；三端 `gate-contracts.md`（schema/免责/流程建议/治理 Non-goal——AC7 对应）；`.ai_state` 记账。
Non-goals：不做密码学身份证明；containment 字段不入治理哈希（免责代替）；不改 drift 本体与 `changedFileSet`；不给 CX/Pi 造 tracker；不迁移历史 sprint；lifecycle 校验不推广到非 generator role；不做 spawn 前提交 `_index` 的代码强制。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 附录 A M1-M7 逐字段负向矩阵 + 合法回执通过；伪造 sha 的 evidence 经 currentRecord 重算 block（先红）；重复 id block；required()=false block（M7）；规则 0 叠加：G2 回执坏 → 链完整也 block（先红）；**次序：回执坏+链断裂报 M1-M7 不报 M8（三端同判）** |
| AC2 | 十格 G1-G10 逐格（G3/G7/G8 重点，G9/G10 为收紧面先红）；G5 先红；G4 绿区不变；外层短路删除；role 大小写归一；**`sprint_source` 键经三端 schema 扩展后事件行合法（新行）且旧行缺键仍合法（混存夹具）** |
| AC3 | containment：伴随字段三分支（M10 先红）+ 两豁免消费者同判据（stale 下 spawn 即拦，无空转）；M13 备份判据（R1 正例 + 缺记录/已删两负向）；仓外写入 no-change 断言 |
| AC4 | tracker Start 端最小复现序列先红（指针指 B、worktree A 内 Start 落 A）；Stop 归属链；`sprint_source` 字段；redirect 失败/丢事件可观察；CX/Pi 负向；非 worktree 主路径等价 |
| AC5 | exports 两名 + 两段式回退适配 + governance 既有测试续绿 + 无仓/空根/`.ai_state` 低于 root/`.git` 边界四用例 + CC==Pi 字节 |
| AC6 | CC/CX 同夹具：八格（含 G9/G10）、containment、M1-M13 消息逐字一致；Pi gate 同源函数文本相等断言**点名清单**：`validateGeneratorChain`/`validateAssignment`/`validateEvent`/`validateImplEntry`/`findAiState`/`tryRepoRoot`（不含 `validateShip`——CC 多 `validateAcMapping` 属既存差异，泛化断言会误红）；`sprint_source` 键的 schema 扩展三端一致 |
| AC7 | 自指双缓解（主 agent 基线工具独立复算 ancestor+evidence 落 log；负向矩阵先红提交经 review 核实）；gate-contracts 三端（schema/两免责/时序声明/流程建议） |
| AC8 | 全套回归绿：基线 160（测量命令 `python3 -m unittest discover -s vibeCoding/scripts/tests/athena999 -t vibeCoding/scripts/tests/athena999`，2026-09-21 实测 Ran 160）+ 本切片新增 |

## 测试场景

1. M1-M7 负向先红；2. G1-G8 矩阵（G2 叠加先红、G5 先红、G7）；3. containment 三分支+豁免同判+M13+no-change；4. tracker Start 端先红+回退链+审计；5. 适配式四用例+governance 等价；6. CC/CX 消息逐字矩阵；7. 独立复算脚本；8. 全套回归。

## 风险

ship 主路径重构：八格矩阵 + 本批 7 个已 ship sprint 账本形态回归抽验。P1-4 残余（worktree `_index` 提交版）如实声明经 `sprint_source` 可审计。自指路径 AC7 双缓解。备份判据依赖机器本地状态（明文）。
