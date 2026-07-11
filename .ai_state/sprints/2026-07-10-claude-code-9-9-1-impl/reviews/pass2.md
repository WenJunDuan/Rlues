# Review Pass 2 — CC Athena 9.9.1 (rework 复审)

- Sprint: 2026-07-10-claude-code-9-9-1-impl
- 对象: worktree `/Users/mi_manchi/workspace/Rlues-cc-9.9.1-impl` (base daf591f, 未 commit), pass1 REWORK 后 generator rework 增量
- 主 agent 实证: validator `144/0` · runtime `66/0/1` · migration `11/11 OK` · `git diff --check` clean; guard 探针 (stage=review): 裸 push / `$(git push ...)` / 反引号 push 全 block, 单引号字面量与 `$((1+2))` 放行; `rm -rf /*`、`$(rm -rf /)`、双引号内替换全 block
- 复审: reviewer (ad294068033c90937) + spec-compliance (ae966da51be9cd01d) 并行

## Reviewer (代码层 findings)

### pass1 findings 关闭状态

| # | Finding | 状态 | 证据 |
|---|---|---|---|
| P0-1 finalVerdict 模板 | CLOSED | delivery-gate.cjs:249 剥全部行内 `*`; 真实粗体模板驱动测试 (PASS+REWORK 两向); 列表/散文行不误判 (锚定 ^…$) |
| P0-2 命令替换绕过 | CLOSED | findSubstitutions 状态机 + 递归 analyze; 嵌套/反引号/双引号内替换 block, 单引号/算术放行; 6 用例 |
| P0-3 rm glob 变体 | CLOSED | normalizeTarget 折叠 `//`、剥 `/*`,`/.`,`/**`; 4 用例 |
| P0-4 PreCompact matcher | CLOSED | settings.json:267 `manual\|auto`; 真实 payload 驱动 compact-snapshot 测试; design §7 已同步 |
| P1-1 env 前缀漏收 | CLOSED | envPrefix 正则; 多前缀命中, 嵌入 `=` 不误判 |
| P1-2 gitLines fail-open | CLOSED | {ok,lines} + 全失败返回 Infinity 恒触发架构门禁; PATH="" 实测 block |
| P1-3 xargs/eval | CLOSED (静态边界内) | unwrap 转发; `eval "rm -rf /"` block, `xargs ls`/`eval echo hi` 无误报 |
| P1-4 迁移测试 | CLOSED | +3 测试对应 allowlist union / owned-group / 用户 permission 保留 |
| P2-1 版本注释 | CLOSED | session-start.cjs:3 → v9.9.1 |

### 新发现 (均 P2, 不阻断)

1. guard 不识别 shell `#` 注释 → `git push ... # $(rm -rf /)` 误报 block (方向保守, 噪音非绕过)。
2. `eval $VAR` 变量间接不被静态展开 → 放行 (静态分析结构性边界, 建议记入已知限制或下轮保守拒绝)。
3. `<(...)`/`>(...)` 进程替换不在 findSubstitutions 覆盖 → `diff <(git push ...) /dev/null` 放行 (同上, 下轮补)。
4. INFO: validate-athena-9.9.1.py check_fresh_codex_runtime 在 macOS/Python3.14 偶发 tempdir 清理竞态 OSError (未改动代码, 环境噪音; 放宽 cleanup 后 144/0 确认; 建议 follow-up 加 ignore_cleanup_errors)。

VERDICT: PASS

## Spec Compliance (spec-compliance, 2026-07-10)

### pass1 → pass2 变化

- MISSING [AC21/T8]: CLOSED — pass1+rework+pass2 构成完整 2+1 闭环, 4 P0 全部代码级修复且各配失败驱动测试。
- MISSING [T7]: CLOSED — test_migrate_991.py +98 行 / 3 新测试, 对应 migrate 脚本真实新分支, 11/11。
- MISSING [worktree E2E]: REMAINING, 已声明 known gap (需真实账号, 本地不可达), 可接受。
- DEVIATED [AC1 hash]: RESOLVED — pass1 为误报; 实测 daf591f 与 HEAD 的 9.9.0/.claude 子树均为 `eb1ab06...`, 与 design §2 记录一致。
- DEVIATED [AC2 staging tree]: 已在 design.md Round 3 记录为接受的偏离 (原地增量编辑 + 全量 diff 审计背书)。
- DEVIATED [evidence kind/file 不对称]: REMAINING — §18 决策 4 仍 open, 非阻断, 移交 ship 前用户裁决。

### AC 重判 (受影响项)

AC10 PASS · AC15 PASS (含负例无过度阻断) · AC20 PASS (validator 偶发环境竞态非回归) · AC21 PASS。范围复核: 9.9.0/codex 零触碰; enabledPlugins 按授权未动待裁决; RELEASE.md 已记录 CX delivery-gate 同构缺陷 known-issue 移交。

### 总评

PASS — 遗留 2 项非阻断: evidence schema 决策 (§18-4) 与 validator 环境竞态 follow-up。

## Evidence Cross-Check

| Claim | Evidence | Status |
|---|---|---|
| 4 P0 修复 | 各配失败驱动测试 (红→绿), 主 agent 独立探针复证 | PASS |
| 3+1 P1 修复 | +16 runtime 用例 + 3 migration 用例, 全绿 | PASS |
| 全量重验 | 144/0 · 66/0/1 · 11/11 · diff clean (主 agent 亲跑) | PASS |
| 范围隔离 | diff --name-only 无 9.9.0/codex 路径 | PASS |
| 9.9.0 基线 | tree `eb1ab06...` base=HEAD 一致 | PASS |

## Evaluator Verdict (evaluator, 2026-07-10)

### 判定依据

pass1 (REWORK: 4 P0 + 5 P1 + 2 P2) → pass2: 4 P0 + 4 P1 + P2-1 全部 CLOSED, 每项配失败驱动测试 (红→绿) + 主 agent 独立探针交叉复证 (非 subagent 自证); 全量重验 144/0 · 66/0/1 · 11/11 · clean; 双 subagent 独立结论收敛。改善判定真实, 非旧 PASS 掩盖新 REWORK。U3 cross-check: checklist 8/8 completed 均有证据, done_without_evidence = 0。

新增 3 P2 (guard `#` 注释误报 / `eval $VAR` 间接 / `<(...)` 进程替换) 属静态分析边界或保守噪音, 非本轮引入回归, 可推后。

### 可推后项 (polish / 下轮 / 用户裁决)

1. guard `#` 注释误报 — polish 小修或记已知限制
2. `eval $VAR` 与进程替换放行 — 记已知限制, 下轮加固
3. validator macOS/Py3.14 tempdir 竞态 — follow-up 加 ignore_cleanup_errors
4. evidence schema §18-4 强约束与否 — ship 前用户裁决
5. worktree 真实账号 E2E — 已声明 known gap
6. §18 决策 1-3/5-9 + enabledPlugins 清单 — 用户裁决

### next_action

polish — path=System, 铁律[Polish 强制]: cleanup-pass.md + architecture/ 更新后方可 ship; ship 前 delivery-gate 另验 open decisions 收敛。

VERDICT: PASS
