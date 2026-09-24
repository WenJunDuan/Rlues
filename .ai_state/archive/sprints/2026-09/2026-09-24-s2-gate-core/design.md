---
sprint_slug: "2026-09-24-s2-gate-core"
path: "System"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s2-gate-core"
branch: "athena-10.1"
base_commit: "e9abec6"
---

# Design — S2 · 门禁核（单一 JS 核 + cc/cx/pi 适配）

> 设计真相：`roadmap/athena-10-1/design.md` §5、§8、§11.2；D1/D2/D4/D5/D9 已拍板。本片只写增量与偏差。

## 背景 (context)

9.9.9 门禁 = CC cjs 4,844 行 + CX py 5,554 行 + Pi 分叉，协议相同却三处维护；5 个死 hook；review/证据绑定输入清单导致一串门禁坑（design §6 表）。

## 方案

- `vibeCoding/athena/gate/`：`hook.cjs`（`node hook.cjs <event> --platform cc|cx|pi`，也导出 `run()` 供 Pi 进程内调用）→ `platform/<p>.cjs` 归一为 AthenaEvent → `core.cjs` 分发 → 规则 → `platform.render()`。
- `lib/`：context（findAiState 止于 git 边界；主仓优先；_index v1/v2 双读）、frontmatter（YAML 子集）、tree-sha（临时 index + `git write-tree`，排除 `.ai_state` 与 `review_ignore`）、shell-lex / shell-words（移植 `_shell-lex.cjs` + pre-bash-guard 词法）、git-project（推送目标 / sameProject，含 S0 全部逻辑）、evidence（分类、可证性、脱敏、主仓 `.runtime/evidence/<sprint>.jsonl`）、ledger（熔断 + issues.md 自动行 + advisories 队列）、exemptions。
- `rules/`：`h1-design`…`h5-shell` 硬门；`advisory.cjs` A1–A10。
- `cli.cjs`：`athena run [--covers ACn] -- <cmd…>`（S3/S4 在此挂子命令）。
- 适配：CC `settings.json` / CX `hooks.json` 全部改为 `node ~/.athena/current/hook.cjs <event> --platform <p>`；Pi `extensions/athena-gates.ts` 进程内 `require` vendored `plugin/core/gate/hook.cjs`。
- build：`platform.json` 新增 `gate_root`；新增 `adapters/core`（dist 目录 `athena`，→ `~/.athena/<ver>/`）；Pi 以 `plugin/core/gate` vendored 同字节。
- 删：CC/CX 全部旧 hooks（含 5 个死 hook 与全部 py hook）、Pi `extensions/cc-core/`。

### 与 10.1 设计的偏差（已裁量）

| 设计原文 | S2 做法 | 理由 |
|---|---|---|
| 切片分支 + worktree | 直接在 `athena-10.1` 单写者提交 | 本会话单写者串行，无并行写集 |
| AC6「athena999 全部 221 条迁入并参数化」 | 迁安全类 fixture（heredoc 32 反例 + 活样本、推送目标 34 例、数据消费者、脱敏/凭据语法、证据可证性、H1–H5 正负例）三端参数化；9.9.9 套件原地保留作冻结基线回归 | 其余测试族测的是 D1/D4/D5 删除的机制，逐条迁移=保留已删语义；见下表 |
| H2「测试类记录」 | provable（test/typecheck/build）+ exit 0 + tree_sha 当前 | §8 定义 provable 即此三类；纯 test 会误拦 Quick 构建修复 |
| H5「stage ∈ {impl, review} 拦推送」 | 只在 stage ∈ {idle, brainstorm, roadmap, ship} 放行；其余与未知/无法解析的状态一律拦 | 9.9.9「非 ship/idle 即拦」的最小放宽；未知值不放行（review r1 P2） |
| H5 危险表 | 9.9.9 CC∪CX 并集 + 新增：强推/删除 main·master（含检出 main 时 `push -f`）、`bash -ec`/`sh -xc` 类组合旗标、`rm -Rf`、timeout/nice/nohup/time/exec/stdbuf 包装、`( … )` 子 shell、shell 写 `.runtime/evidence` 或 `review.json` | review r1；逐条见 test_gate_shell/test_gate_regressions 的 declared additions |
| （未修，9.9.9 既有）| 非网络来源 `… \| bash`、`git -c alias.x=push x`、计算出的命令词（`$(echo rm) -rf /`、`eval "$(…)"`、`bash -c "$(curl …)"`、`rm -rf $(echo /)`、分支名来自 `$(…)` 的强推）不识别 | 静态分析无法判定运行期展开；留 issues |
| 证据/审查账本完整性 | 写工具写 `.runtime/evidence/**`、`sprints/*/review.json` 一律拦（H2 ledger，解析符号链接、大小写不敏感）；shell 的重定向/tee/cp·mv·install·ln·rsync 目标（含目录目标）/sed -i/dd of=/git checkout·restore/curl·wget 输出 拦；**已知缺口**：`node -e`/`python -c` 一行脚本、先 `cd` 进目录再相对写、tar/unzip 解包 | 防误写不防蓄意伪造；蓄意绕过属模型越权，由 review 与 issues 追责 |
| 推送目标中的 `cd` | 只有命令行开头连续的 shell 内建 `cd`（非 nohup/timeout/env/sudo/xargs 包装）能移动推送目标；子 shell、`\|\|`、控制字（if/then/while/do/!/{）或其他命令之后的 `cd` → 按会话 cwd 严格判 | review r2/r3：条件或作用域内的 cd 不一定执行 |
| 未知状态下的 Stop | 只警告（AC7）；`stage: "Ship"` 等拼写错误因此跳过 H2/H3 —— S4 `athena ship` 须严格重跑 H2/H3 | review r3 P3，S4 承接 |
| 证据可证性（续） | 另含 `function x`、`source`/`.`（`bin/activate` 除外）；分类认路径前缀工具（`.venv/bin/pytest`、`node_modules/.bin/jest`）与 `uv/poetry/pipenv/hatch run`；**已知缺口**：gitignored 工具被替换（如 `ln -sf /bin/true node_modules/.bin/jest`），因 gitignored 文件不入源码树 | review r3 |
| 证据可证性 | 9.9.9 规则 + `validation_may_not_run`（验证前 `\|\|`/exit/exec/return）+ `validation_shadowable`（trap/alias/函数定义/shopt/enable/hash/PATH 改写） | review r1/r2 |
| H4 CX 无定义的 `explorer` | 按名豁免（CX 内置 explorer 沙箱待验证，S7 探测） | review r2 P3，声明 |
| `review_ignore` 宽 glob（如 `src/**`） | 只剔除 match-all；证据与 review 记录 ignore 列表且须一致；S3 `review prepare` 须向 reviewer 展示该列表 | review r2 P3，S3 承接 |
| `athena run --kind` | 删除；kind 只按命令词判定，argv 以 shell 引号拼接后按段分类；argv[0] 为 shell/包装器、运行期间源码树变化、验证前有 `\|\|`/exit 均记 unprovable | review r1 P1/P2：防「凭空证据」 |
| hook 超时 | Stop 120 s、PostToolUse 60 s；tree-sha 每次 git 调用 ≤30 s，异常 = H2 硬错误 block | 平台对超时 hook 放行（fail-open）属平台行为，仅能靠预算规避 |
| H1 stage ∈ {design, impl} | 另含 `plan`（9.9.9 仍有 plan 阶段，S5 前 stages 不变） | 否则 plan 阶段写代码绕过 H1 |
| H4 `parallel_writers ≥ 2` | 同；不再按 `git worktree list` 计数 | Rlues 常驻额外 worktree，计数法对黄区单写者误拦 |
| Pi `agent_before_settle` 硬停 | S2 保持 `agent_end` followUp；硬停随 S7 探测落地 | 0.87 事件签名待验证 |
| session_start / prompt 注入 | 注入 `_index` 摘要 + 生效豁免 + 排队提示；S4 扩充 | v2 状态字段在 S4 |
| 状态读取 | `_index` 无法解析 / 缺 path+stage / 未知 stage·path = invalid（非 idle）：拦实现写入、推送、ship Stop；`.ai_state` 写入放行以便修复 | review r1 P1 |
| CX `workdir` | 项目与门禁以会话 cwd 为准；workdir 只解析相对路径并作推送的前导 `cd` | review r1 P1 |

### 9.9.9 测试族处置（AC6）

| 族 | 条数 | 处置 |
|---|---|---|
| test_heredoc_guard | 21 | 迁：全部命令样本 → `test_gate_shell.py`（三端） |
| test_gate_fixes_20260924 PushTarget/DataConsumers | 2 类 34+ 例 | 迁 → `test_gate_shell.py`；DesignChangeBaseline → A5；VmPendingPromises → A4；StaleFacts/InitPlatformDetection 留 9.9.9（非门禁） |
| test_secret_placeholder | 15 | 迁脱敏谓词 → `test_gate_evidence.py`；environment 凭据语法随 D5 删除（不再快照 runtime-env） |
| test_state_review EvidencePipelineIntegrity | ~10 | 迁可证性规则 → `test_gate_evidence.py`；Input/ReviewBinding、IndexUpdater、counts → D4/D5 删除；review 回归在 S3 |
| test_writer_provenance | 54 | D1：降为 A1 提示，3 条提示级 fixture；其余删除 |
| test_contract_parsers | 15 | AC 行解析 → H1 fixture；packet/tdd-evidence 删除 |
| test_gate_fixes_20260922 | 4 | ShipWriteOutsideRepo → H1 仓库外放行；RoadmapAllowlist/EvidenceFilterNames 删除（机制删） |
| test_claude_rework / test_vm_install / test_laav / test_fullstack_contract | 56 | 非门禁（skill/安装），留 athena999，S6/S8 处理 |

## 验收标准 (Done Contract)

- AC1: `gate/hook.cjs` 单入口，`platform/{cc,cx,pi}.cjs` 归一 payload 并渲染输出；CX apply_patch 的 Add/Update/Delete/Move 路径在 JS 中解析；同一 fixture 在三端得到同一裁决。
- AC2: H1–H5 按 design §5.3 实现，每条至少 1 正例 + 1 负例 fixture；硬门内部异常 = block。
- AC3: A1–A10 以 warn 输出且写入 `.runtime/advisories.jsonl`，提示规则内部异常 = allow + warn。
- AC4: 豁免 `{key,until,reason}` 过期即失效且不存在 H2/H3 豁免；Stop 同 reason 连续 3 次 block → 第 3 次放行并向 `issues.md` 追加 `gate` 行。
- AC5: `athena run -- <cmd>` 记录真实退出码、kind、provable、tree_sha 到主仓 `.ai_state/.runtime/evidence/<sprint>.jsonl`；post_tool 兜底采集器沿用 pipefail 可证性；脱敏覆盖 token/口令/URL 凭据；H2 只认 tree_sha 等于当前源码树的记录。
- AC6: 安全类 fixture 迁入 `evals/fixtures/test_gate_*.py` 并参数化 cc/cx/pi；上表列出每个 9.9.9 测试族的去向。
- AC7: writer-provenance 以 A1 提示保留（提示级 fixture）；只读 Stop 不拦（idle/非 ship）、A3 架构检查按 `base_commit..HEAD` 锚定。
- AC8: `gate/**/*.cjs` 合计 ≤3,000 行、单文件 ≤300 行（fixture 断言）。
- AC9: dist 中无 `.py` hook、无 5 个死 hook、无旧 cjs hook；CC/CX hook 配置只指向 `~/.athena/current/hook.cjs`；build 产出 `athena/10.1` 核心与 Pi vendored 同字节；S1 字节相等测试改为 declared-delta。

## 允许写集

`vibeCoding/athena/{gate,adapters,evals,core/pace/stages.yaml,build.mjs}/**`、本 sprint 文书、`_index.md`、`roadmap/athena-10-1/items.yaml`。不改 `claude/`、`codex/`、`pi-agent/`（冻结基线）。

## 不做

`athena review`（S3）、v2 状态 CLI 与迁移（S4）、宪法/skills 文案（S5，含 skills 中对旧 hook 名的引用）、install/doctor（S6）、Pi 硬停与平台探测（S7）。
