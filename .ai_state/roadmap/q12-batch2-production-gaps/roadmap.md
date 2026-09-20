---
roadmap_slug: q12-batch2-production-gaps
created: 2026-09-20
trigger: user_explicit
estimated_total_complexity: L
status: active
implementation_authorized: true
---
# Roadmap — Q12 批二生产缺口

## 目标与边界

以当前 9.9.9 源码和可复现行为为准，修复 Rlues 自身的门禁、状态、证据和运行时缺口；不把 Claude Code 平台问题、已经修复的问题或既定语义重复实现进仓库。

本轮是 System 路径。每个切片独立设计、TDD、运行时验证、polish、review 和 ship；共享 `delivery-gate` 的切片串行，避免多个写者同时修改同一门禁。CC/CX 只同步语义相同的实现；Pi 仅同步其实际拥有且同源的 hook，不伪造平台对称性。

## 现场分诊

| # | 结论 | 处理 |
|---|---|---|
| 1 | Rlues 缺陷 | 增加严格的外部写者 provenance 回执；不能做成 skip flag |
| 2 | Rlues 缺陷 | repo containment 后才对实现写入执行 ship drift 门禁；仓库外写入放行 |
| 3 | Rlues 缺陷 | overflow 统一到 `.ai_state/index-overflow.md`，pointer 使用一致的项目相对路径 |
| 4 | 部分命中 | 当前已能绑定 `tail/tee` 管道；仍缺可证明的 pipefail/首段退出状态语义 |
| 5 | 部分命中 | 九字段合同已有；补 0 条记录与缺字段的分层诊断，不再复制一套模板 |
| 6 | Rlues 缺陷 | prepare 排除自身会写的账本，并逐文件报告输入漂移 |
| 7 | Rlues 缺陷 | AC 只从合同结构提取，排除普通正文与反引号引用 |
| 8 | Rlues 缺陷 | 接受 `## AC` / `## 验收`，错误列全可接受标题 |
| 9 | Rlues 缺陷 | prepare 对 stale `implementation_commit` fail-fast，不自动静默改 manifest |
| 10 | Rlues 缺陷 | 增加受支持的 governance hash 输出 CLI |
| 11 | Rlues 缺陷 | architecture 绑定到 implementation base..reviewed commit 及 review 输入，不再看任意工作区 |
| 12 | 部分命中 | 裸标识符已不会误杀；修 quoted placeholder/reference 假阳性，真实 secret 仍 fail-closed |
| 13 | 已修 | 保留 head+tail 的实现与回归测试，不重复改 |
| 14 | Rlues 缺陷 | shell parser 识别 quoted heredoc delimiter，正文不参与命令危险模式匹配 |
| 15 | 既定合同 | counts 是活跃热层计数，archive 默认不扫；只补防回归措辞/测试 |
| 16 | Rlues 缺陷 | CC Start 从调度 worktree 的真实 `_index` 取 sprint；不套到不存在该路径的 CX/Pi |
| 17 | Rlues 缺陷、原改法不足 | 只读 Stop 可结束但不能产生 ship PASS；必须有可靠会话归属与 mutation 信号 |
| 18 | 仓库外 | Claude Code 凭据分类器挂起，只记录生产观察，不写 Rlues 修复 |

## 安全不变量

### 外部写者回执

- `external-writer.json` 是内部 generator 链的互斥替代路径，不是失败后的宽松 fallback。
- exact schema 至少绑定 executor、派发/回执引用与摘要、原提交到集成提交映射、当前 evidence ID。
- 只把集成提交要求为 HEAD ancestor；原提交可能因 cherry-pick 改 SHA，只作 provenance/patch 对照。
- evidence 必须唯一、`binding_status=current`、`result=pass`，并绑定当前 source/design/environment/output。
- 回执证明可审计 provenance，不宣称密码学证明外部身份。

### Architecture 证明

- 保持 `runtime-verify → polish/architecture → review`；因此不能只看 `reviewed commit..HEAD`。
- review prepare 把架构文档纳入输入绑定；ship 核对未漂移及当前 sprint 归属。
- Git 范围使用 implementation base..reviewed commit；不再把未提交工作区当作已审证明。

### 只读 Stop

- “允许会话结束”与“ship 已通过”分离；warning 不改 stage、next_action，也不产生 GatePass。
- 没有可靠的同 sprint/session 与 repo mutation 证明时继续 fail-closed。
- 若只能依赖不稳定 transcript 或新增泛化遥测，本切片停止在设计结论，不以弱启发式放宽门禁。

## 实施顺序

| # | slug | 覆盖 | 依赖 | 独立验收点 |
|---|---|---|---|---|
| 1 | index-overflow-root-transaction | 3 | 无 | 双端原子 spill 到根文件、pointer 可解析、并发与 no-op 回归 |
| 2 | evidence-pipeline-integrity | 4、13 回归 | 无 | 管道摘要可绑定且不能把失败测试误记 PASS；长输出尾部仍保留 |
| 3 | review-binding-preflight | 6、9、10 | 无 | prepare 不自毁、stale commit 提前报错、governance CLI 跨端一致 |
| 4 | contract-parser-diagnostics | 5、7、8 | 无 | TDD 分层诊断；AC 结构提取与标题别名均有负向测试 |
| 5 | writer-provenance-and-repo-boundary | 1、2、16 | 4 | 外部回执严格验证；repo 外写不触发 drift；worktree Start 归属正确 |
| 6 | ship-session-and-architecture-binding | 11、17 | 3、5 | 架构证明绑定已审范围；只读 Stop 不误报 ship PASS 且不放宽真实写会话 |
| 7 | runtime-secret-false-positive | 12 | 无 | placeholder/reference 保留，真实 token 仍剔除；豁免若存在则按文件 SHA 绑定 |
| 8 | heredoc-aware-shell-guard | 14 | 无 | 白名单窄形（首行封闭文法+消费者正集）的 quoted 正文不误拦；一切非窄形与今日行为逐字节等价（解释器族/命令位置照拦） |
| 9 | package-parity-and-release-regressions | 13、15、18 记录及全量收口 | 1–8 | 仅同步适用平台，完整 validator 通过，外部项明确不纳入修复 |

切片 1–4、7、8 在文件写集互斥时可并行设计，但 System 实现按红区规则隔离；切片 5、6 因共享门禁且合同相关，按依赖串行。第 9 项只做发行一致性与全量回归，不重新实现第 13、15、18 条。

## 发布判据

- 每个 A 类问题都有先红后绿的行为测试；B/C 类问题有明确 no-change 证据。
- CC、CX、Pi 的差异按真实能力记录，不以文件数量制造“同步完成”。
- 完整 9.9.9 validator 与目标行为测试全绿；与本批无关的基线异常单列处理。
- 最终 architecture、review、runtime evidence 与交付 commit 同一绑定链。

## 切片顺序补充 (2026-09-20)

切片 8 `heredoc-aware-shell-guard` 现排在切片 2 之后：切片 2 新增的 `_shell-lex` 只服务证据策略，`pre-bash-guard` 字节未改；切片 8 实际交付（2026-09-20 更正）：heredoc 白名单窄形判定单源 `_shell-lex`（`simpleHeredoc`），guard 以函数内惰性载入消费；guard 自有引号扫描保留为 lexer 缺失回退层（安全关键可用性），完整合并经八轮审查裁定不做——黑名单与全文法路线证伪档案在该 sprint reviews/。

## 切片 2 遗留，指名切片 8 承接 (2026-09-20)

- **CX 4000 字符决策截断**：`codex/9.9.9/.codex/hooks/evidence-collector.py:117` 在分类与策略调用**之前**把 command 截到 4000 字符，与切片 2 刚在 CC 端修掉的是同一缺陷类，只是阈值高一个数量级。实测 4518 字符的被掩盖管道：CC 记 `unknown`，CX 记 `pass`。修法与 CC 相同一行：决策用 `command_of(payload)`，只在 `:153` 落盘处截断。切片 2 未修，因为改动会使已绑定的 implementation review PASS 失效而需重开一轮；独立 reviewer 评为 P2 可延后（4000 字符的验证命令不现实，且该上限早于本切片存在）。
- **`_shell-lex` 不在 `setup-athena.py` 的 `REQUIRED_ASSETS`**：既有 9.9.9 home 若拿到新 `_input-binding` 而缺 lexer，`managed_complete()` 仍判其完整，此后验证全记 `unknown`。方向是永久卡住交付而非假通过。归切片 9（发行一致性）。
- **ship architecture 检查的变更集失真**（2026-09-20 实测，详见 `proposals.md` P17）：`changedFileSet` 首条探针 `git diff main...HEAD` 在默认分支上恒空，已提交改动不可见；`ls-files --others` 又把其他 sprint 的未跟踪遗留计入，导致「本次变更集」既漏掉本切片 55 个文件、又被 13 个无关文件推过 ≥5 阈值。建议改用 design 的 `base_commit..HEAD` 锚定并按当前 sprint 过滤未跟踪项。归切片 9。

## 切片 3 遗留，指名切片 5 承接 (2026-09-20)

- **移除 sprint 范围的门禁字节断言**：`test_review_binding_gate_export_diff_is_sprint_scoped_and_pi_matches_cc` 硬编码 `0ca066c`，用来把切片 3 对 `delivery-gate` 的改动面钉死为「仅两个导出名」。切片 5 合法改门禁的那一刻它必然失败，原计划由切片 5 删除。**2026-09-20 更正：实施顺序令切片 4 先合法改 gate，该断言已由切片 4（AC6）删除并以 Pi 同源函数文本相等断言（PiSameSourceParity）+ 独立的 Pi `_review-binding`==CC 测试承接**。该义务此前只写在测试注释与 design 里，未进 roadmap（切片 3 implementation review P2-4 指出），现按切片 4 review P1-1 落实更正。
- **消除 `governance` 的路径解析复写**：CC 端 `gateRepoRoot`/`gateAiState`（`_review-binding.cjs:275,284`）是门禁 `tryRepoRoot`/`findAiState` 的 20 行副本，因切片 3 只获准导出两个名字而无法 import；CX 端已是 import。副本经两轮逐行核实为忠实，但其中最易漂移的 `.git` 边界停止那行**无测试覆盖**。切片 5 既然要动门禁，顺带导出这两个 helper 并删除副本，与 CX 对齐。
- 另记两条已知非阻塞差异，切片 5 动门禁时留意：两端 `findAiState` 的 `.git` 边界语义不同；两端 `parseFrontmatter` 对畸形行一个跳过一个抛错。

## 切片 8 记账（2026-09-20，AC6，归切片 9）

- CC/CX pre-bash-guard 危险清单既有差异：CX 多 mariadb（DB_CLIENTS）、dash/ksh（SHELLS）与 fork-bomb 检测（`pre-bash-guard.py:37-38,282`），CC 无。三端判定面统一由切片 9 发行一致性裁量。
- `scan()` 语义面微扩（窄形 quoted 正文并入 segment 后 classify_validation 可能在解释器源码文本命中验证模式）：方向多记不少记，POLICY_MATRIX 零变化，观察项。

## 切片 7 记账（2026-09-20，AC6，归切片 9）

- Pi `plugin/skills/athena-runtime-verify/references/playbook.md:13-14` 悬空引用：指向 Pi 包内不存在的 `athena-vm/scripts/runtime-run.py`。切片 7 不修不造（Pi 无该机制，不伪造对称）；切片 9 发行一致性时处置。
- CX `evidence-collector.py:32-42` 同族脱敏正则（仅脱敏非阻断，CX 独有）未纳入占位符谓词，切片 9 裁量。

## 新发现缺陷（2026-09-20 切片 7 返工期根因定位，独立条目待排期）

- `codex/9.9.9/.codex/skills/athena-init/scripts/init-platforms.py:100` 用 `'.claude' in script.parts` 判端：路径含 `.claude/worktrees/` 的 CX 脚本被误判为 CC 去找不存在的 commit-index.cjs → worktree 内跑安装类测试恒 8 FAIL（本会话多次目击的幽灵失败根因）。对照实验证实纯路径诱发。归切片 9 或单开 Bugfix。
- 切片 7 impl review P2-3 余项：test_secret_placeholder.py:145 端到端 cli 单 runner（已注明由字节相等覆盖）。
- 切片 7 复核记账两条（归切片 9）：①C 侧 shape 分支被包裹引号击穿（带引号引用形态 THROW，基线同判 fail-closed 方向）；②design:50 残余理由句未覆盖人选口令短段形态，补半句文字精确性。

## 切片 4 遗留观察（2026-09-20，implementation review P2 记录，非阻塞）

- bullet 形态纯反引号包裹的 AC 标签（`- \`ACn\`: …`）会从强制集静默剔除且无诊断（表格形态不受影响）；属可选补强（span 恰为 ACn 时不置空或显式报错），归切片 9 发行收口时裁量。
- packet「有小节但 0 条有效条目」仍落 AC set mismatch，与 design 侧两层诊断不对称；可选补强，同归切片 9 裁量。
- TDD/mismatch 类报错含可变数据，Stop 断路器 reason_sha1 计数对同根因可能永不升级（先例既有，方向少升级非放行）；归切片 6（ship 会话语义）顺带评估。
