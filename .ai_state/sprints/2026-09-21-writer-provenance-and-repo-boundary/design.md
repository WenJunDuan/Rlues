---
sprint_slug: "2026-09-21-writer-provenance-and-repo-boundary"
path: "System"
stage: "design"
author: "cc-main (rev 2: e551a33f REWORK 全落实)"
base_commit: "9784d8b"
---

# Writer provenance 与仓库边界（Q12#1/#2/#16 + 切片 3 承接②）

## WHY（勘查逐行核实，首轮复核确认全部属实）

**#1** 外部写者唯一出口 = 裸布尔 `skip_impl_subagent_check`（gate:1245/py:1859/pi:1208），零 provenance；`external-writer.json` 三端零命中。**#2** `harness_target_outside_repo` 仅 2 个 worktree-check 消费者，gate 不读、无 sprint 归属、「ship 后移除」无强制。**#16** tracker 落账依赖可变全局指针（`currentSprint:37`），redirect 吞异常（:33）、`.git` 边界丢事件（:17→:135）；本会话两次落错账实录。**承接** `tryRepoRoot:447`/`findAiState:28` 不在 exports:1488；`_review-binding:275-296` 20 行复写。

## HOW

### 账本完整性与 generator 要求解耦（P0-1 落点）

`validateGeneratorChain` 拆两层：
- **validateLedgerIntegrity（无条件）**：`subagent-assignments.jsonl`/`subagent-events.jsonl` 只要存在，其中**每一行**都必须过 exact-key schema、时序与 lifecycle 一致性（现 `:147-220` 的结构校验全部保留，抽离「必须有 generator 行」判据）。任何状态下账本坏行都 block——回执不豁免账本结构（矩阵第 3 格闭合）。
- **requireGeneratorEvidence（三态）**：
  - ①assignments 含 `role=generator` 行 → 该链必须完整（Start→assignment→Stop）。**flag 在此状态无效**：链断裂即 block，出口消息=「续跑该 agent 至真实 SubagentStop，或按外部接管流程重新集成（新 external-writer.json + 新 evidence），不得删改账本行」（矩阵第 7 格闭合；proposals.md:47 类截断释放的合法出口由 flag 改为回执）。
  - ②无 generator 行但 `external-writer.json` 存在 → `validateExternalWriter`。flag 在此状态**被忽略**（矩阵第 8 格=②）。
  - ③两者皆无 → `skip_impl_subagent_check=true` 且 path ∉ {Refactor,System} 放行（绿区语义不变）；R/S 或 flag=false → block（消息含三条出口：补链/补回执/绿区改 flag）。
- call site 重构：`:1245` 的外层 flag 短路**删除**，flag 判定下沉到状态③内部——flag 从「关掉校验的总开关」降级为「状态③绿区的例外申报」，这是「不能做成 skip flag」的机械落点。

### validateExternalWriter（#1）

`sprints/<slug>/external-writer.json`，canonical schema（附录 A 定死字段名与消息，grok 逐字实现）：`schema_version:1`、`executor{tool,model}`、`dispatch_ref`、`receipt_ref`、`receipt_summary`、`original_commits[]`、`integration_commit`、`evidence_tool_use_id`。校验分级（附录 A 表内标注机械/半机械/纸面）：
- `integration_commit`：`git merge-base --is-ancestor <c> HEAD` 现场验（机械；仅证明进入本仓历史，不证明作者——免责句入 gate-contracts）。
- `evidence_tool_use_id`：在 evidence.yaml 命中**恰好一条**（0 条或 ≥2 条均 block——P1-1 唯一性字面）且该条经 `inputBinding.currentRecord` **现场重算**为 current + `result=pass`（P1-1：走 `:245` 同款重算基元，禁用 `:1028` 的字符串读取路径）；`inputBinding.required(sprintDir)` 为假 → 回执一律 block（无严格绑定环境=不可证）。
- `dispatch_ref`/`receipt_ref`：sprint 内相对路径、实存、非空（半机械）。
- 其余字段非空非占位（纸面，如实分级）。

### containment（#2，P0-2 落点）

- **新增伴随字段 `harness_target_outside_repo_sprint: "<slug>"`**（归属信号）。flag=true 必须伴随该字段：
  - 字段 == 当前 `current_sprint_slug` → 合法（impl 与 ship 全程，恢复 flag 的真实使用窗口，不复刻 P9 死锁）；
  - 字段 ≠ 当前 slug → **stale**：impl-entry 对实现写入 block，消息=「上一 sprint（<字段值>）的仓外授权未收口，复位两字段后重试」；
  - flag=true 而伴随字段缺失 → block（消息指明补法）。
- ship 时 flag=true → sprint session-log 须含**备份路径记录且该路径 existsSync 为非空目录**（P1-2：判据=从 session-log 提取 `~/.athena-backups/...` 或其他绝对路径样式的备份记录行并现场验存在性；正则匹配不再作为唯一判据）。历史两先例（install-sync-3 记法、.snapshots 记法）作测试夹具校准提取规则。
- **no-change 断言（P1-5）**：drift 判定本体零改动——flag sprint 下仓外写入不产生 drift block（fixture 断言），`changedFileSet` 噪音仍归切片 9。

### tracker 落账归属（#16，仅 CC；P1-4 修正）

sprint 归属解析链（写入位置仍是主仓账本）：
1. **SubagentStop**：优先「该 agent_id 的 assignment 行所在 sprint」（在主指针 sprint 与 worktree `_index` slug 两个候选目录中查找 assignment；assignment 是握手时显式绑定，最强信号）；无 assignment → 沿用既有 `startLocations` 唯一匹配；再无 → 第 3 档。
2. **SubagentStart** 与第 3 档：worktree `_index` 的 slug 且主仓 `sprints/<slug>/` 目录实存 → 用之；否则主仓指针。
3. 每条事件行新增 `"sprint_source":"assignment"|"worktree-index"|"main-index"` 审计字段——**P1-4 残余（worktree `_index` 为分支提交版，未提交 spawn 时可携带旧 slug）经此可审计可纠正**，并在 gate-contracts/orchestration 记流程建议「spawn 前提交 `_index`」；不做代码强制。
4. redirect 失败：stderr + 事件行 `"redirect":"failed"`；`.git` 边界丢事件：stderr 痕迹。CX/Pi 不改（负向断言）。

### 导出与复写消除（承接，P1-3 修正）

exports 增 `tryRepoRoot`/`findAiState`；`_review-binding` 复写删除，替换用**适配式**：`const root = gate.tryRepoRoot(cwd) || ''; const aiState = root ? (gate.findAiState(root) || '') : '';`（保持原 `''` 契约与空值短路，`findAiState` 无空守卫不裸传）；AC4 加无仓/空根两用例 + `.git` 边界直接用例；CC==Pi 字节同改；CX 零改动。

## 附录 A：canonical 字段与消息（grok 逐字实现，三端一致；P2-3）

| 字段 | 校验 | block 消息（CC/CX 逐字同） |
|---|---|---|
| schema_version | ==1 | `external-writer schema_version must be 1` |
| executor.tool / executor.model | 非空字符串 | `external-writer executor tool/model missing` |
| dispatch_ref / receipt_ref | sprint 内实存非空文件 | `external-writer <field> missing or empty: <path>` |
| receipt_summary | 非空非占位 | `external-writer receipt_summary is placeholder or empty` |
| original_commits | 数组（可空数组），元素 40-hex | `external-writer original_commits entries must be 40-hex` |
| integration_commit | 40-hex 且 is-ancestor HEAD | `external-writer integration_commit is not an ancestor of HEAD: <sha>` |
| evidence_tool_use_id | 恰一条命中且 currentRecord 重算 current+pass | `external-writer evidence not uniquely bound and currently verifiable: <id>` |
| （三态③ R/S） | — | `red-zone sprint requires a complete generator chain or external-writer.json; skip_impl_subagent_check alone is not admissible` |
| （stale flag） | — | `harness_target_outside_repo left over from sprint <slug>; reset both fields before implementation writes` |

## 允许写集

同 rev 1（三端 gate、`_review-binding` CC+Pi、`subagent-tracker.cjs` CC、`test_writer_provenance.py` 新建、`test_state_review.py` 仅增用例、三端 gate-contracts.md、`.ai_state` 记账）。**新增**：`_index` 伴随字段属状态 schema（文档于 gate-contracts，不新增代码文件）。
Non-goals：不做密码学身份证明（ancestor 免责句显式落文档）；不改 drift 本体与 `changedFileSet`（切片 9）；不给 CX/Pi 造 tracker 对称物；不迁移历史 sprint；不做 spawn 前提交 `_index` 的代码强制（流程建议）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 回执全 schema 校验按附录 A 逐字段负向矩阵（≥9 条）+ 合法回执通过；evidence 走 currentRecord 重算（伪造 sha 的记录 block，先红）；重复 id block；required() 假 block |
| AC2 | 三态×flag 八格矩阵逐格测试（含第 3 格账本结构校验不因回执失效、第 7 格断裂链+flag+R/S block、第 8 格=②）；R/S 裸 flag block（先红）；绿区裸 flag 不变；call site 外层短路删除 |
| AC3 | containment：伴随字段三分支（匹配/不匹配/缺失）各一用例（stale 先红）；ship 备份路径 existsSync 判据（历史两记法夹具校准）；flag sprint 仓外写入 no-change 断言 |
| AC4 | tracker：Stop 优先 assignment 归属（指针错位夹具先红，复现本会话事故）；Start 走 worktree `_index`+目录实存回退链；`sprint_source` 审计字段；redirect 失败/丢事件可观察；CX/Pi 负向断言；非 worktree 主路径等价 |
| AC5 | exports 两名 + 复写删除按适配式 + governance 既有测试续绿 + 无仓/空根/`.git` 边界三用例 + CC==Pi 字节 |
| AC6 | CC/CX 同夹具：三态、containment、回执消息逐字一致；Pi gate 同源函数文本相等断言（P2-1） |
| AC7 | 自指缓解：首个真实回执的 ancestor 与 evidence 两项由主 agent 以基线工具独立复算落 session-log；负向矩阵先红提交经 review 核实（P1-6）。gate-contracts 三端含 schema/免责/流程建议（P2-2） |
| AC8 | 全套回归绿（干净路径，基线 160 + 新增） |

## 测试场景

1. 附录 A 负向矩阵先红；2. 八格三态矩阵（第 3/7/8 格重点）；3. containment 三分支 + no-change；4. tracker 指针错位夹具先红 + 回退链 + 审计字段；5. 适配式三用例 + governance 等价；6. CC/CX 消息逐字矩阵；7. 主 agent 独立复算脚本可执行；8. 全套回归。

## 风险

- ship 主路径重构（call site 短路删除）：八格矩阵 + 本批 7 个已 ship sprint 账本形态回归抽验。
- P1-4 残余如实声明：未提交 spawn 的旧 slug 错位不可根除，`sprint_source` 使其可审计（对比今日：静默且不可判别）。
- 自指路径：AC7 双缓解 + 本切片 ship 的回执样本随档。
