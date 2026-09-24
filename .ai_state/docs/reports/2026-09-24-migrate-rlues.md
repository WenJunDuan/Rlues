# Athena 10.1 state migration

- project: Rlues
- date: 2026-09-24

## _index

- v1 size 9682 B → v2 fields: path, stage, next_action, sprint, roadmap, route
- to .runtime/probe.json: platform_features, tools_available, cc_version, cx_version, ag_callable, platforms_enabled
- dropped: breadcrumb, skip_polish, skip_architecture_check, skip_runtime_verify, route_confidence, plan_model, counts, pointers, last_subagent, last_subagent_at, active_worktrees, harness_target_outside_repo, last_critic_round, design_changed_after_impl, plan_critique_max_rounds, plan_critique_min_rounds, plan_critique_disabled, skip_impl_subagent_check, network_in_polish, fingerprint

## Files (move 63, untrack 1)

| kind | from | to | note |
|---|---|---|---|
| move | requirements/athena-10-1.md | docs/requirements/athena-10-1.md |  |
| move | requirements/fullstack-delivery-pack.md | docs/requirements/fullstack-delivery-pack.md |  |
| move | compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md | decisions/2026-07-08-decision-token-usage-null-and-subagent-stop.md |  |
| move | compound/2026-07-08-learning-hook-order-and-worktree-counts.md | archive/compound/2026-07-08-learning-hook-order-and-worktree-counts.md |  |
| move | compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md | archive/compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md |  |
| move | compound/2026-07-11-learning-worktree-generator-ledger-gap.md | archive/compound/2026-07-11-learning-worktree-generator-ledger-gap.md |  |
| move | compound/2026-07-13-decision-index-field-audit.md | decisions/2026-07-13-decision-index-field-audit.md |  |
| move | compound/2026-07-13-decision-quantum-7-to-2-consolidation.md | decisions/2026-07-13-decision-quantum-7-to-2-consolidation.md |  |
| move | compound/2026-07-14-learning-canonical-install-path-runtime.md | archive/compound/2026-07-14-learning-canonical-install-path-runtime.md |  |
| move | compound/2026-07-25-explore-prompt-harness-convergence.md | docs/research/2026-07-25-explore-prompt-harness-convergence.md |  |
| move | compound/2026-07-28-decision-close-prompt-engineering-direction.md | decisions/2026-07-28-decision-close-prompt-engineering-direction.md |  |
| move | compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md | archive/compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md |  |
| move | compound/2026-08-27-decision-retire-local-telemetry-collection.md | decisions/2026-08-27-decision-retire-local-telemetry-collection.md |  |
| move | compound/2026-08-27-explore-athena-9-9-8-post-ship-directions.md | docs/research/2026-08-27-explore-athena-9-9-8-post-ship-directions.md |  |
| move | compound/2026-09-20-learning-cross-port-divergence-needs-cmp.md | archive/compound/2026-09-20-learning-cross-port-divergence-needs-cmp.md |  |
| move | compound/2026-09-20-learning-self-mutating-regression-test.md | archive/compound/2026-09-20-learning-self-mutating-regression-test.md |  |
| move | compound/2026-09-20-learning-single-source-error-strings.md | archive/compound/2026-09-20-learning-single-source-error-strings.md |  |
| move | compound/README.md | archive/compound/README.md |  |
| move | sprints/2026-08-27-athena-9-9-8 | archive/sprints/2026-08/2026-08-27-athena-9-9-8 | shipped (items.yaml done) |
| move | sprints/2026-09-06-athena-9-9-9 | archive/sprints/2026-09/2026-09-06-athena-9-9-9 | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-06-athena-next-version | archive/sprints/2026-09/2026-09-06-athena-next-version | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-07-pace-task-triage-hotfix | archive/sprints/2026-09/2026-09-07-pace-task-triage-hotfix | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-13-pi-agent-9-10 | archive/sprints/2026-09/2026-09-13-pi-agent-9-10 | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-13-telegram-style-hotfix | archive/sprints/2026-09/2026-09-13-telegram-style-hotfix | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-14-athena-9-9-9-local-hotfix | archive/sprints/2026-09/2026-09-14-athena-9-9-9-local-hotfix | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-16-cc-agent-turn-cap | archive/sprints/2026-09/2026-09-16-cc-agent-turn-cap | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-20-contract-parser-diagnostics | archive/sprints/2026-09/2026-09-20-contract-parser-diagnostics | shipped (items.yaml done) |
| move | sprints/2026-09-20-evidence-pipeline-integrity | archive/sprints/2026-09/2026-09-20-evidence-pipeline-integrity | shipped (items.yaml done) |
| move | sprints/2026-09-20-heredoc-aware-shell-guard | archive/sprints/2026-09/2026-09-20-heredoc-aware-shell-guard | shipped (items.yaml done) |
| move | sprints/2026-09-20-index-overflow-root-transaction | archive/sprints/2026-09/2026-09-20-index-overflow-root-transaction | shipped (items.yaml done) |
| move | sprints/2026-09-20-review-binding-preflight | archive/sprints/2026-09/2026-09-20-review-binding-preflight | shipped (items.yaml done) |
| move | sprints/2026-09-20-runtime-secret-false-positive | archive/sprints/2026-09/2026-09-20-runtime-secret-false-positive | shipped (items.yaml done) |
| move | sprints/2026-09-21-writer-provenance-and-repo-boundary | archive/sprints/2026-09/2026-09-21-writer-provenance-and-repo-boundary | shipped (PASS review / ship recorded) |
| move | sprints/2026-09-24-s0-gate-hotfix-9-9-9-p1 | archive/sprints/2026-09/2026-09-24-s0-gate-hotfix-9-9-9-p1 | shipped (items.yaml done) |
| move | sprints/2026-09-24-s1-single-source-build | archive/sprints/2026-09/2026-09-24-s1-single-source-build | shipped (items.yaml done) |
| move | sprints/2026-09-24-s2-gate-core | archive/sprints/2026-09/2026-09-24-s2-gate-core | shipped (items.yaml done) |
| move | sprints/2026-09-24-s3-review-cli | archive/sprints/2026-09/2026-09-24-s3-review-cli | shipped (items.yaml done) |
| move | sprints/2026-09-24-s4-state-v2 | archive/sprints/2026-09/2026-09-24-s4-state-v2 | shipped (items.yaml done) |
| move | sprints/2026-09-24-s5-prompts-v2 | archive/sprints/2026-09/2026-09-24-s5-prompts-v2 | shipped (items.yaml done) |
| move | sprints/2026-09-24-s6-install-doctor | archive/sprints/2026-09/2026-09-24-s6-install-doctor | shipped (items.yaml done) |
| move | sprints/archive/2026/2026-07-07-f1-orchestrator-framework-design | archive/sprints/2026-07/2026-07-07-f1-orchestrator-framework-design | cold |
| move | sprints/archive/2026/2026-07-08-f2-scaffold-page-gen | archive/sprints/2026-07/2026-07-08-f2-scaffold-page-gen | cold |
| move | sprints/archive/2026/2026-07-08-f3-db-and-unit-test-gen | archive/sprints/2026-07/2026-07-08-f3-db-and-unit-test-gen | cold |
| move | sprints/archive/2026/2026-07-08-f4-security-and-e2e | archive/sprints/2026-07/2026-07-08-f4-security-and-e2e | cold |
| move | sprints/archive/2026/2026-07-08-f5-biz-delivery-loop | archive/sprints/2026-07/2026-07-08-f5-biz-delivery-loop | cold |
| move | sprints/archive/2026/2026-07-08-f6-end-to-end-drill | archive/sprints/2026-07/2026-07-08-f6-end-to-end-drill | cold |
| move | sprints/archive/2026/2026-07-10-athena-9-9-1-agent-skill | archive/sprints/2026-07/2026-07-10-athena-9-9-1-agent-skill | cold |
| move | sprints/archive/2026/2026-07-10-athena-9-9-1-cx-runtime | archive/sprints/2026-07/2026-07-10-athena-9-9-1-cx-runtime | cold |
| move | sprints/archive/2026/2026-07-10-athena-9-9-1-installer | archive/sprints/2026-07/2026-07-10-athena-9-9-1-installer | cold |
| move | sprints/archive/2026/2026-07-10-athena-9-9-1-release | archive/sprints/2026-07/2026-07-10-athena-9-9-1-release | cold |
| move | sprints/archive/2026/2026-07-10-athena-9-9-1-validation | archive/sprints/2026-07/2026-07-10-athena-9-9-1-validation | cold |
| move | sprints/archive/2026/2026-07-10-claude-code-9-9-1-design | archive/sprints/2026-07/2026-07-10-claude-code-9-9-1-design | cold |
| move | sprints/archive/2026/2026-07-10-claude-code-9-9-1-impl | archive/sprints/2026-07/2026-07-10-claude-code-9-9-1-impl | cold |
| move | sprints/archive/2026/2026-07-13-athena-9-9-2-architecture-review | archive/sprints/2026-07/2026-07-13-athena-9-9-2-architecture-review | cold |
| move | sprints/archive/2026/2026-07-14-athena-9-9-3-review-fixes | archive/sprints/2026-07/2026-07-14-athena-9-9-3-review-fixes | cold |
| move | sprints/archive/2026/2026-07-21-merge-branches-tun-tailscale | archive/sprints/2026-07/2026-07-21-merge-branches-tun-tailscale | cold |
| move | sprints/archive/2026/2026-07-25-athena-9-9-6-prompt-engineering | archive/sprints/2026-07/2026-07-25-athena-9-9-6-prompt-engineering | cold |
| move | sprints/archive/2026/2026-07-25-harness-gate-p1-p4 | archive/sprints/2026-07/2026-07-25-harness-gate-p1-p4 | cold |
| move | sprints/archive/2026/2026-07-28-gate-descaling | archive/sprints/2026-07/2026-07-28-gate-descaling | cold |
| move | sprints/archive/2026/2026-07-28-installation-sync-w31-w34 | archive/sprints/2026-07/2026-07-28-installation-sync-w31-w34 | cold |
| move | sprints/archive/2026/2026-07-29-athena-9-9-6-hotfix2 | archive/sprints/2026-07/2026-07-29-athena-9-9-6-hotfix2 | cold |
| untrack | .snapshots | .runtime/snapshots | git rm --cached; files kept under .runtime |
| move | index-overflow.md | archive/legacy/index-overflow.md | retired in 10.1 |
| move | harness-patches.md | archive/legacy/harness-patches.md | retired in 10.1 |

## Lessons to triage (8; learning/trick → AGENTS.md rule, skill 坑 or drop — decided by a human/agent, never automatic)

- compound/2026-07-08-learning-hook-order-and-worktree-counts.md
- compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md
- compound/2026-07-11-learning-worktree-generator-ledger-gap.md
- compound/2026-07-14-learning-canonical-install-path-runtime.md
- compound/2026-07-28-learning-reserved-ac-labels-silent-exemption.md
- compound/2026-09-20-learning-cross-port-divergence-needs-cmp.md
- compound/2026-09-20-learning-self-mutating-regression-test.md
- compound/2026-09-20-learning-single-source-error-strings.md

## issues.md draft (13 rows → issues.draft.md; replace proposals/vm-pending after confirmation)

- debt: P13 · 已完成 sprint 的 review 绑定与台账更新存在时序陷阱 (2026-07-28, R6-F5 critic 核出) (proposals.md:26)
- debt: P1 · delivery-gate 与 token-usage hook 的文件名/易变性错位 (2026-07-24, batch1 ship 实测死结) (proposals.md:33)
- debt: P2 · generator 生命周期 "恰一次 Start/Stop" 与断点续跑不兼容 (2026-07-24, batch1 实测) (proposals.md:44)
- debt: P3 · delivery-gate 按 shell cwd 解析 .ai_state, worktree 内误拦 (2026-07-24, batch2 实测) (proposals.md:54)
- debt: P4 · polish_worker 的 Edit/Write 被硬隔离在自有 worktree, 无法履行"唯一写者"职责 (2026-07-24, batch2 实测) (proposals.md:63)
- debt: P10 · critic 轮次判据是全文字面计数, 讨论该契约的 design 会虚增轮次 (2026-07-28, 撰写 §12 时自检抓获) (proposals.md:72)
- debt: P11 · 机器契约双写必漂: 模板注记块与 gate 源码无单一真相源 (2026-07-28, §12 设计时识别) (proposals.md:86)
- debt: P12 · 派工时序无机械强制, 只落约定 (2026-07-28, 消费侧 ledger-debt-batch 实测起因) (proposals.md:99)
- debt: P13 · destructive cleanup command rejected by executor (2026-07-29) (proposals.md:111)
- debt: P14 · worktree 强制检查三次撞上: 审"未提交增量"的 reviewer 也被拦 (2026-08-27, 实测撞上; P9 第三形态) (proposals.md:117)
- debt: P15 · `_index-bounds` 溢出搬运不在锁内, spill 全文曾静默丢失 (2026-08-27, tidy 复核实测) (proposals.md:123)
- debt: P16 · `_index-bounds.flush()` 零溢出也无条件写, idle 态在 .ai_state 根反复重建空 stub (2026-08-27, tidy 复核实测) (proposals.md:130)
- debt: P17 · ship 的 architecture 检查看不见已提交在默认分支上的改动, 且把别的 sprint 的遗留算作本次变更集 (2026-09-20, slice 2 ship 实测撞上) (proposals.md:135)

## Untracked/ignored files that move but stay untracked (0; a rollback leaves them at the new path; months holding them are not packed)


> runtime-read check waived: 命中项均为冻结的 9.9.x 发行包、9.9.9 回归测试与 9.9.8 验证脚本里的字面路径，不是运行时读取

## Blockers (0)


## Rollback

`git reset --hard pre-athena-10.1-state` (real run only). It restores tracked files only: afterwards move the untracked/ignored files listed above back to their old paths (or delete them) and remove `.ai_state/.runtime/{probe.json,_index.v1.md,snapshots/}` — the restored .gitignore no longer hides them, so a later `git add -A` would commit them.
