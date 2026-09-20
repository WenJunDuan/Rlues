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
| 8 | heredoc-aware-shell-guard | 14 | 无 | quoted heredoc 正文不误拦，delimiter/命令位置的真实危险命令仍拦截 |
| 9 | package-parity-and-release-regressions | 13、15、18 记录及全量收口 | 1–8 | 仅同步适用平台，完整 validator 通过，外部项明确不纳入修复 |

切片 1–4、7、8 在文件写集互斥时可并行设计，但 System 实现按红区规则隔离；切片 5、6 因共享门禁且合同相关，按依赖串行。第 9 项只做发行一致性与全量回归，不重新实现第 13、15、18 条。

## 发布判据

- 每个 A 类问题都有先红后绿的行为测试；B/C 类问题有明确 no-change 证据。
- CC、CX、Pi 的差异按真实能力记录，不以文件数量制造“同步完成”。
- 完整 9.9.9 validator 与目标行为测试全绿；与本批无关的基线异常单列处理。
- 最终 architecture、review、runtime evidence 与交付 commit 同一绑定链。

## 切片顺序补充 (2026-09-20)

切片 8 `heredoc-aware-shell-guard` 现排在切片 2 之后：切片 2 新增的 `_shell-lex` 只服务证据策略，`pre-bash-guard` 字节未改；切片 8 为 heredoc 重写 guard scanner 时，负责把两个 scanner 收敛到同一模块。

## 切片 2 遗留，指名切片 8 承接 (2026-09-20)

- **CX 4000 字符决策截断**：`codex/9.9.9/.codex/hooks/evidence-collector.py:117` 在分类与策略调用**之前**把 command 截到 4000 字符，与切片 2 刚在 CC 端修掉的是同一缺陷类，只是阈值高一个数量级。实测 4518 字符的被掩盖管道：CC 记 `unknown`，CX 记 `pass`。修法与 CC 相同一行：决策用 `command_of(payload)`，只在 `:153` 落盘处截断。切片 2 未修，因为改动会使已绑定的 implementation review PASS 失效而需重开一轮；独立 reviewer 评为 P2 可延后（4000 字符的验证命令不现实，且该上限早于本切片存在）。
- **`_shell-lex` 不在 `setup-athena.py` 的 `REQUIRED_ASSETS`**：既有 9.9.9 home 若拿到新 `_input-binding` 而缺 lexer，`managed_complete()` 仍判其完整，此后验证全记 `unknown`。方向是永久卡住交付而非假通过。归切片 9（发行一致性）。
