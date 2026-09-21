---
sprint_slug: "2026-09-21-writer-provenance-and-repo-boundary"
path: "System"
stage: "design"
author: "cc-main"
base_commit: "9784d8b"
---

# Writer provenance 与仓库边界（Q12#1/#2/#16 + 切片 3 承接两项）

## WHY（勘查逐行核实，行号=仓库副本）

**#1 外部写者唯一出口是纯布尔 skip flag。** `skip_impl_subagent_check` 为真即跳过 generator 链全部校验（CC `delivery-gate.cjs:1245`、CX `:1859`、Pi `:1208`），零字段记录谁写的/写了什么/凭什么。`external-writer.json` 三端零命中——roadmap 安全不变量节要求的替代路径完全不存在。切片 3 的 grok 施工正是走这条裸 flag。generator 链本体（`validateAssignment:100` + `validateGeneratorChain:147-220`）与 evidence 绑定基元（`_input-binding.cjs:6` FIELDS、gate `:1028/:1050`）已在，可复用。
**#2 containment 与 drift 门禁零关联。** `harness_target_outside_repo` 仅 2 个 worktree-check 消费者（`subagent-worktree-check.cjs:102`、CX audit `:151`），注释写「ship 后应移除」但无代码强制；`validateShip` 与 drift 判定（`:559-593`）不读该字段。两个方向都失守：flag=true 时门禁不核实备份记录在案；ship 后残留 flag 无人拦。
**#16 落账依赖可变全局指针。** `subagent-tracker.cjs:25-35` `redirectToMainRepo` 吞异常静默降级；`findAiState:17` 的 `.git` 边界会在 worktree 无 `.ai_state` 时提前 return null → 事件**丢失**（:135 直接 return）；`currentSprint:37` 只读主仓 `_index.current_sprint_slug`——多 sprint 期间指针移动即落错账。本会话实测两次同根因事故（run `1b32be6e`/`f50e0e37` prepare 落错账本）。**worktree 自己的 `_index` 是 spawn 时刻的快照，才是该事件的真 sprint。** CX `subagent-tracker.py` 无 redirect 机制（调度模型不同），Pi 无 tracker——不伪造对称。
**承接（切片 3 遗留②）**：`tryRepoRoot:447`/`findAiState:28` 仍不在 `module.exports:1488`；`_review-binding.cjs:275-296` 的 `gateRepoRoot`/`gateAiState` 20 行复写（CC==Pi 字节同，`test_pi_review_binding_matches_cc` 牵连），注释行号引用已漂移；CX 侧 `_review_binding.py:366-369` 本就 import 无需改。

## HOW

### external-writer.json（#1）——generator 链的互斥替代路径，不是旁路

- 位置 `sprints/<slug>/external-writer.json`。exact schema（roadmap 安全不变量逐条）：`schema_version:1`、`executor`（{tool, model}，如 grok/grok-4.6）、`dispatch_ref` + `receipt_ref`（sprint 内相对路径，实存文件）+ `receipt_summary`、`original_commits[]`（施工分支原 SHA，仅 provenance/patch 对照，不验可达）、`integration_commit`（必须为 HEAD ancestor，`git merge-base --is-ancestor` 现场验）、`evidence_tool_use_id`（必须在 evidence.yaml 中恰好一条命中且 `binding_status=current`、`result=pass`——复用既有基元，绑定 source/design/environment/output 四轴随之成立）。任一字段缺失/占位/校验失败 = block。
- 门禁改造（三端 gate）：ship 时 generator 链校验分三态——①assignments 有 generator 行 → 走既有 `validateGeneratorChain`；②无 generator 行但 `external-writer.json` 存在 → 走新 `validateExternalWriter`；③两者皆无 → 仅当 `skip_impl_subagent_check=true` **且 path ∉ {Refactor, System}**（绿区例外，stages.md 既有规则）放行，R/S 一律 block（裸 flag 对红区失效——「不能做成 skip flag」的机械落点）。两路径并存（既有 generator 又有 external-writer）合法：分别校验（混合施工场景，如本批 grok+polish-worker）。
- 明示：回执证明**可审计 provenance**，不宣称密码学证明外部身份（roadmap 原话入 gate-contracts 文档）。

### containment × ship（#2）

- `validateShip` 新增：`harness_target_outside_repo=true` 时，要求 sprint `session-log.md` 含备份路径记录（机械判据：正则 `\.athena-backups|逐文件备份` 命中 ≥1 行），缺失 = block（备份是该 flag 的授权前提，铁律[零写入]原文）。
- impl-entry 新增 stale-flag 拦截：`current_sprint_slug` 已切换到新 sprint 而 flag 仍为 true → 实现写入 block，消息指明「上一 sprint 的仓外授权未收口，先复位 flag」。ship 本 sprint 期间 flag=true 合法（安装态同步就发生在 ship）。
- drift 判定本体不改（repo 外写入 git 本就不可见；`changedFileSet` 的 `ls-files --others` 噪音归切片 9 既有记账）。

### tracker 落账归属（#16，仅 CC）

- `hook()` 的 sprint 解析改为：**优先读事件 cwd 所在 worktree 自己的 `_index.md`**（linked worktree 的 checkout 是 spawn 时刻快照=事件的真 sprint）；worktree 无 `_index` 或非 worktree（gitDir==commonDir）时按现状读主仓指针。账本文件仍写主仓（redirect 不变）。
- `redirectToMainRepo` 失败不再静默：catch 分支写 stderr `[subagent-tracker] redirect failed: <err>` 并在事件行加 `"redirect":"failed"` 字段（可审计降级）。
- `findAiState` 提前 null（事件丢失分支）：return 前写 stderr `[subagent-tracker] event dropped: no .ai_state from <cwd>`——丢失可观察。
- CX/Pi 不改（负向断言：CX tracker 无 redirect 符号、Pi 无 tracker 文件）。

### 导出与复写消除（承接）

- `module.exports` 增 `tryRepoRoot`、`findAiState` 两名（延续切片 3「仅导出所需名」纪律）。
- `_review-binding.cjs` 删 `gateRepoRoot`/`gateAiState` 20 行复写，`governance` 改用 `gate.tryRepoRoot`/`gate.findAiState`（`:298` 已 require gate）；注释更新（含漂移的行号引用）；CC==Pi 字节同改。既有 `test_governance_uses_main_repo_index_from_linked_worktree` 与跨端字节等测试必须续绿；补 `.git` 边界停止行的直接测试（承接项明示无覆盖）。CX 零改动。

## 允许写集

| 文件 | 变更 |
|---|---|
| `vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs` + Pi `cc-core/delivery-gate.cjs` | validateExternalWriter、三态分派、containment 两检、exports 两名（Pi 侧同源函数同改，不动其既有分叉） |
| `vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py` | 同构（validate_external_writer、三态、containment） |
| `vibeCoding/claude/9.9.9/.claude/hooks/_review-binding.cjs` + Pi 同名 | 删复写改 require（字节同改） |
| `vibeCoding/claude/9.9.9/.claude/hooks/subagent-tracker.cjs` | #16 三处（仅 CC） |
| `vibeCoding/scripts/tests/athena999/test_writer_provenance.py`（新建）+ `test_state_review.py`（仅增 `.git` 边界用例，不删既有） | 行为测试 |
| 三端 `skills/pace/references/gate-contracts.md` | external-writer schema 与三态规则文档 |
| `.ai_state/`（记账） | 常规 |

Non-goals：不做密码学身份证明；不改 drift 判定本体与 `changedFileSet`（切片 9）；不给 CX/Pi 造 tracker 对称物；不动 `skip_impl_subagent_check` 的绿区语义；不迁移历史 sprint 档案。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | external-writer.json 全 schema 校验：合法回执（ancestor 真、evidence current+pass 唯一命中）ship 通过；缺任一字段/占位/非 ancestor/evidence 不 current 逐项 block（负向矩阵）；R/S 下裸 `skip_impl_subagent_check` 无回执 = block（先红：今日放行）；绿区（Feature 等）裸 flag 行为不变 |
| AC2 | flag=true 且 session-log 无备份记录 = ship block（先红）；有记录通过；新 sprint 残留 stale flag = impl-entry block（先红）；本 sprint ship 期 flag=true 合法 |
| AC3 | worktree 内 SubagentStart 落账 sprint = 该 worktree `_index` 的 slug（先红：今日取主仓指针，指针错位夹具复现本会话事故）；redirect 失败事件带 `"redirect":"failed"` 且不丢；无 `.ai_state` 丢弃有 stderr 痕迹；CX tracker 无 redirect 符号、Pi 无 tracker（负向断言） |
| AC4 | exports 增两名；`_review-binding` 复写删除改 require，governance 行为与既有测试续绿；`.git` 边界停止有直接用例；CC==Pi 字节相等（既有 parity 测试续锁） |
| AC5 | CX gate 同构行为：external-writer 三态与 containment 两检同夹具驱动 CC/CX 判定与消息一致 |
| AC6 | roadmap 承接清单更正：切片 3 遗留第 2 条（复写消除）标记完成 |
| AC7 | 全套回归绿（干净路径，基线 160 + 新增） |

## 测试场景

1. 回执合法/非法矩阵（≥8 负向）先红后绿；2. R/S 裸 flag 先红；3. containment 双检先红；4. tracker 指针错位夹具（复现 `1b32be6e` 类事故）先红；5. redirect 失败与事件丢失可观察性；6. governance 复写删除后行为等价 + `.git` 边界用例；7. CC/CX 同夹具矩阵；8. 全套回归。

## 风险

- 三态分派改动 ship 主路径：AC1 负向矩阵 + 既有 sprint 档案回归（本批 7 个已 ship sprint 的账本形态各异，等价抽验入场景 8）。
- tracker 改 sprint 解析可能影响正常主仓路径：非 worktree 分支逐字节保持今日行为（等价断言）。
- external-writer 首个真实消费者就是本切片自己的 grok 施工——ship 时用新机制自校验（吃自己的狗粮，回执样本随 sprint 落档）。
