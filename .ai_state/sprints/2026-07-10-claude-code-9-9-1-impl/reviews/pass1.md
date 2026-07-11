# Review Pass 1 — CC Athena 9.9.1 (Fable5 post-implementation review)

- Sprint: 2026-07-10-claude-code-9-9-1-impl
- 对象: worktree `/Users/mi_manchi/workspace/Rlues-cc-9.9.1-impl` (branch codex/cc-9.9.1-impl, base daf591f)
- 复跑证据: validate-athena-9.9.1.py `143/0` · test-athena-claude-9.9.1-runtime.cjs `50/0/1` · test_migrate_991.py `8/8 OK` · `git diff --check` clean
- 审查方式: 主 agent (Fable5) 初查 settings.json + 4 核心 hooks → reviewer subagent (ae05258382c31e3e3) + spec-compliance subagent (aa8b975facc207225) 并行交叉验证

## Reviewer (代码层 findings)

### P0

1. **finalVerdict 解析不了 evaluator 自身模板** — `delivery-gate.cjs:243-253` vs `agents/evaluator.md:41-43`。模板输出 `**判定**: PASS`; strip 只剥行首尾 `*`, 剩 `判定**: PASS`, 两条正则均不匹配 → `has no explicit VERDICT line` → 合法 PASS 被永久 block。测试 6 处 VERDICT 用例全部只用干净 `VERDICT: PASS` 文本, 从未联调模板格式。修法: 规范化模板为纯文本 `VERDICT: PASS`, 或 finalVerdict 先剥行内 `*`; CX `delivery-gate.py:328` 同构问题同步修; 补真实模板驱动的 gate 测试。
2. **pre-bash-guard 不解析 `$(...)`/反引号命令替换** — `pre-bash-guard.cjs:8-37,104-143`。`echo $(git push origin main)` 整段解析为 name=echo, git push 分支恒假 → 非 ship 阶段可实际完成 push; `$(rm -rf /)` 同理绕过危险命令检测。测试只覆盖 quoted 文本与裸 push, 无命令替换用例。修法: tokenize 检测未被单引号保护的 `$(`/`` ` ``, 递归 analyze 或保守 fail-closed 阻断; 补三种替换形式测试。
3. **`rm -rf /*` 绕过 dangerousTarget** — `pre-bash-guard.cjs:104-106`。仅精确匹配 `/`,`~`,`$HOME`,`${HOME}`; `/*`、`//`、`/.` 等价变体全放行。修法: 覆盖 glob 变体 + path.normalize 等价判断; 补用例。
4. **PreCompact/Notification matcher 语义互换** — `settings.json:265-300`。PreCompact matcher 写成 `agent_needs_input|agent_completed` (官方取值 manual|auto), 真实 PreCompact 永不匹配 → compact-snapshot.cjs 永不触发, 快照兜底名存实亡; Notification 反而 matcher ""。设计 §7 表自身亦有此错位, 实现照抄。修法: PreCompact 改 `manual|auto`; 补 `hook_event_name=PreCompact, trigger=auto` payload 驱动测试。

### P1

1. **isValidationCommand 漏收 env-var 前缀命令** — `evidence-collector.cjs:54-57`。正则要求命令在 `^` 或 `[;&|]` 后; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest` 不命中 → 真实验证命令 (runtime-verify.md 记录的正是此形式) 不进 evidence.yaml → gate 反向误 block。fixture `posttool-success.json:6` 刻意用无前缀形式, 测试因此假绿。修法: 正则前缀容忍 `(?:KEY=VAL\s+)*` 或复用 guard 的 tokenizer; fixture 改为真实前缀形式。
2. **gitLines 静默吞错 → architecture 门禁 fail-open** — `delivery-gate.cjs:291-311`。git 全失败时 changedFiles 低估 <5 → Refactor/System 绕过 ARCHITECTURE.md 强制。CX `delivery-gate.py:370-378` 同构。修法: git 失败按"无法确认=触发门禁"处理 + stderr 日志, 两端同步。
3. **xargs/eval 等转发执行不在 unwrap 递归清单** — `pre-bash-guard.cjs:66-85`。`xargs rm -rf /`、`eval "rm -rf /"` 绕过。修法: 扩展清单或对不可静态展开形式保守拒绝。

### P2

1. `session-start.cjs:3,13-14` 头注释仍写 v9.8.0/v9.7.0, 未更新 9.9.1。
2. (INFO) `subagent-worktree-check.cjs:59-65` worktreeCount 失败返回 1 (fail-open) 与 pre-bash-guard 顶层 fail-closed 立场不一致, 建议下轮统一"未知即最严格"。

### 疑点复核结论

| 主 agent 疑点 | 结论 |
|---|---|
| PreCompact matcher 错位 | CONFIRMED → P0-4 |
| evidence env-var 前缀漏收 | CONFIRMED → P1-1 |
| evidence.yaml 缺 kind/file 破坏 CX 互解析 | REFUTED — 两端 gate 只锚定 tool_use_id/result, 互解析无碍 |
| subagent-tracker 并发/跨 sprint 反例 | REFUTED — 冻结/回写/握手链成立, 16 并发追加测试通过 |
| delivery-gate 其他绕过 | selectLatestReview/validateEvidence 无新绕过; finalVerdict 与 gitLines 见 P0-1/P1-2 |
| quoted "git push" 误拦 | REFUTED — 分词正确, 有测试覆盖 |
| agents frontmatter vs 设计 §9 | CONFIRMED 一致 (7 角色逐项匹配, read-only 均 permissionMode: plan + disallowedTools) |
| migration 三方合并安全 | CONFIRMED 安全 — 精确旧默认才替换, private/plugins/secrets 保留, 幂等+4 断点回滚测试扎实 |

VERDICT: REWORK

## Spec Compliance (spec-compliance, 2026-07-10)

### MISSING (做少了)

- [AC21/T8] Fable5 review 此前仅 PENDING 占位 (headless `--model fable` Not logged in, 零调用); T8 "产出 review 包"≠"review 完成"。本 pass1 即该 review 的落地, 但 findings 合并前 AC21 仍未满足。
- [T7] migrate-9.9.0-to-9.9.1.py 新增大量三方合并/allowlist/原子写逻辑, 但 test_migrate_991.py / test_setup_991.py 不在 worktree diff 中 — 新逻辑分支是否被旧测试覆盖存疑, 无新增断言证据。
- [§10/§15] 真实 `Agent isolation: worktree` E2E 与 worktree 生命周期审计缺 (runtime-verify.md 自认未覆盖)。

### EXTRA (做多了)

- 合理 refactor: RELEASE.md; subagent-retry/notification-router/pace-continuator 适配性微调; config-change-audit.cjs (对应 §7 表, §17 清单自身滞后)。
- scope creep 候选: settings.json 默认内置 `extraKnownMarketplaces` + 8 个 `enabledPlugins` — 设计 §12 只说"保留用户选择", 未授权默认包内置第三方插件启用清单, 需用户确认。

### DEVIATED (做偏了)

- [§6] CC evidence.yaml 不写 kind/file, CX 写 — gate 层互解析无碍, 但属未记录为决策的静默字段不对称, 应在 §18 决策 4 或 CHANGELOG 补记。
- [AC2/T1] 设计要求"从 9.9.0 干净 staging tree 重建", 实际是对候选 9.9.1 目录原地增量编辑; 最终态等价性需确认无候选残留。
- [AC1 备注] design.md 记录的 9.9.0 tree hash `eb1ab06...` 与仓库实测 hash 不符 (实测 base 与 HEAD 一致为 `2eb0c321...`, 子树路径口径差异); AC1 实质 (9.9.0 零改动) 成立, 文档 hash 记录应修正口径。

### AC 逐条判定

AC1 PASS · AC2 PARTIAL · AC3 PASS · AC4 PASS · AC5 PASS · AC6 PASS · AC7 PASS · AC8 PASS · AC9 PASS · AC10 PASS · AC11 PARTIAL · AC12 PASS · AC13 PASS · AC14 PASS · AC15 PASS(但见 Reviewer P0-2/P0-3 绕过面) · AC16 PASS · AC17 代码支持未实跑复核 · AC18 PASS · AC19 PASS · AC20 PARTIAL · AC21 FAIL(本 review 落地后待 findings 合并) · AC22 PASS

### 总评

REWORK — AC21 未闭环 + MISSING 3 项 + scope creep 候选 1 项。

## Evidence Cross-Check

| Claim (checklist) | Evidence | Status |
|---|---|---|
| T1 staging tree | AC1 tree 一致实测; 但"干净重建"无操作证据 (DEVIATED) | PARTIAL |
| T2/T3 hook contract + fail-closed gate | 复跑 50/0/1; gate 代码审查 fail-closed 成立; 但 4 P0 揭示契约/绕过缺口 | PARTIAL |
| T4 worktree/角色/review 2+1 | agents frontmatter 逐项符合 §9; settings 无 WorktreeCreate override | PASS |
| T5 settings/安全/Prompt | effortLevel=xhigh, 无 SUBAGENT_MODEL; 但 PreCompact matcher 错位 (P0-4) + plugins 清单未授权 | PARTIAL |
| T6 migration | 8/8 OK + 代码审查; 但测试文件零改动 (MISSING) | PARTIAL |
| T7 验证矩阵 | 143/0 + 50/0/1 复跑成立; 但 4 P0 全部未被套件捕获 (fixture 避开真实场景) | PARTIAL |
| T8 review 包 | fable5-post-impl-review-brief.md 存在; review 本身此前 PENDING | PARTIAL |

补充 (evaluator U3): T8 标 completed 但对应 evidence (`cc6705`) 是 "blocked: not logged in; zero model tokens" — done_without_evidence 边界案例, 由本 pass1 补齐, checklist 文档口径滞后。

## Evaluator Verdict (evaluator, 2026-07-10)

### 判定依据

| Finding | 严重度 | 对应 AC | 影响 |
|---|---|---|---|
| P0-1 finalVerdict 解析不了自身模板 | P0 | AC10 | 合法 PASS 被 gate 永久 block, gate 自证闭环失败 |
| P0-2 `$(...)`/反引号绕过 pre-bash-guard | P0 | AC15 直接证伪 | 非 ship 阶段可实际 push / `$(rm -rf /)` 绕检 |
| P0-3 `rm -rf /*` 变体绕过 | P0 | AC15 证伪 | 危险命令检测覆盖不足 |
| P0-4 PreCompact matcher 语义互换 | P0 | §7 (设计自身亦错) | compact-snapshot 永不触发, 快照兜底失效 |
| AC21 FAIL | 硬性 AC | §16 | Fable5 review 此前仅 PENDING, findings 未合并 |
| MISSING T7 / scope creep 插件清单 | P1 | AC17/§12 | 迁移新逻辑无新断言; 默认启用 8 个第三方插件未经批准 |

非 FAIL 理由: 实现隔离在 worktree, 未 commit/merge 进 main, 无生产暴露。

### next_action

rework_impl — 4 P0 + AC21 未闭环, 先在 worktree 修复并补失败用例, 重跑 143/0 + 50/0/1 全绿后进入 pass2。

### rework 优先级

1. P0-2 命令替换绕过 (最高, 真实可利用) — 补 `echo $(git push ...)`、反引号、`bash -c '$(rm -rf /)'` 失败用例
2. P0-3 `rm -rf /*` 变体 — 与 P0-2 同批, 补 `/*`、`//`、`/.` 三用例
3. P0-1 finalVerdict — 用 evaluator.md 真实模板 (`**判定**: PASS`) 驱动 gate 测试; CX delivery-gate.py:328 同步修
4. P0-4 matcher 互换 — PreCompact 改 `manual|auto`, 同步修 design.md §7; 补 `trigger=auto` payload 驱动测试
5. AC21 闭环 — findings 修复合并后产出 pass2
6. P1 同批: evidence env-var 前缀、gitLines fail-open、xargs/eval、T7 迁移测试断言、插件清单待用户确认

VERDICT: REWORK
