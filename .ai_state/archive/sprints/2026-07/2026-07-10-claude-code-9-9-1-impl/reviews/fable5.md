# Fable5 Review — CC Athena 9.9.1

VERDICT: PASS (pass2, rework 后; pass1=REWORK 见下)

Executed: 2026-07-10, Fable5 会话内 2+1 交叉审查 (主 agent 初查 + reviewer + spec-compliance 并行 + evaluator 综合)。完整 findings 见同目录 `pass1.md`。此前 headless `--model fable` PENDING 占位已由本轮取代。

## P0

1. `delivery-gate.cjs:243-253` finalVerdict 解析不了 `agents/evaluator.md` 自身模板 `**判定**: PASS` (行内 `**` 不被剥离) → 合法 PASS 被永久 block。CX `delivery-gate.py:328` 同构。
2. `pre-bash-guard.cjs:8-37,104-143` 不解析 `$(...)`/反引号命令替换 → `echo $(git push origin main)` 绕过 stage 门禁实际 push; `$(rm -rf /)` 绕检。
3. `pre-bash-guard.cjs:104-106` dangerousTarget 仅匹配字面 `/`,`~`,`$HOME` → `rm -rf /*`、`//`、`/.` 放行。
4. `settings.json:265-300` PreCompact matcher 误用 `agent_needs_input|agent_completed` (官方取值 manual|auto, 与 Notification 语义互换) → compact-snapshot 永不触发。设计 §7 表自身同错, 需一并修。

## P1

1. `evidence-collector.cjs:54-57` isValidationCommand 漏收 `ENV=val cmd` 前缀命令 (真实验证命令正是此形式) → evidence.yaml 漏 pass 记录, gate 反向误 block; fixture 刻意避开该形式 = 测试假绿。
2. `delivery-gate.cjs:291-311` gitLines 静默吞错 → changedFiles 低估 <5 → architecture 门禁 fail-open。CX 同构。
3. `pre-bash-guard.cjs:66-85` xargs/eval 转发执行不在 unwrap 递归清单。
4. migrate-9.9.0-to-9.9.1.py 新增三方合并逻辑但 test_migrate_991.py 零改动, 新分支无新增断言。
5. settings.json 默认内置 8 个第三方 enabledPlugins + extraKnownMarketplaces — 设计 §12 未授权, 待用户裁决。

## P2

1. session-start.cjs 头注释版本号陈旧 (v9.8.0/v9.7.0)。
2. subagent-worktree-check.cjs worktreeCount 失败 fail-open, 与 guard fail-closed 立场不一致。

## Fixes Applied

rework_impl (generator, worktree 内, 未 commit): 4 P0 + P1-1/2/3/4 + P2-1 全部修复, 每项配失败驱动用例 (红→绿)。P1-5 (enabledPlugins) 按授权未动待用户裁决。关闭证据与新增 3 项 P2 边界 (guard `#` 注释误报 / `eval $VAR` 间接 / 进程替换) 见 `pass2.md`。CX delivery-gate 同构缺陷已记入 RELEASE.md known-issue 移交。

## Test Evidence

- pass1 复跑: `143/0` · `50/0/1` · `8/8` · clean — 全绿但 4 P0 均未被捕获 (fixture 系统性避开触发场景)。
- rework 后复跑 (主 agent 亲跑): `144/0` · `66/0/1` (+16 用例) · `11/11` (+3 用例) · clean; guard 探针独立复证 (push-in-substitution block / 单引号与算术放行 / rm 变体 block)。

## Remaining Runtime Gaps

- 真实 Claude 账号的 agent model/effort/background 观测与 `Agent isolation: worktree` E2E (runtime-verify.md 已声明)。
- AC2 "干净 staging tree 重建" 无操作证据, 实为候选目录原地编辑, 需确认无残留。

## Final Scope Decision

pass2 = PASS → 进入 polish (铁律[Polish 强制])。仍不允许 merge/release: ship 前需 (1) polish 完成 (cleanup-pass + architecture), (2) 用户裁决 enabledPlugins 清单与 design §18 开放决策 (含 evidence schema §18-4)。CX 端 finalVerdict/gitLines 同构缺陷移交下一 CX patch。
