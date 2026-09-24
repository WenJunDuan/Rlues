# Athena 10.1 state migration (dry-run)

- project: Rlues
- date: 2026-09-24

## _index

- v1 size 9639 B → v2 fields: path, stage, next_action, sprint, roadmap, route
- to .runtime/probe.json: platform_features, tools_available, cc_version, cx_version, ag_callable, platforms_enabled
- dropped: breadcrumb, skip_polish, skip_architecture_check, skip_runtime_verify, route_confidence, plan_model, counts, pointers, last_subagent, last_subagent_at, active_worktrees, harness_target_outside_repo, last_critic_round, design_changed_after_impl, plan_critique_max_rounds, plan_critique_min_rounds, plan_critique_disabled, skip_impl_subagent_check, network_in_polish, fingerprint

## Files (move 52, pause 7, keep 1, untrack 1)

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
| pause | sprints/2026-09-06-athena-next-version | sprints/2026-09-06-athena-next-version | not shipped → design status: paused (resume_when to be written by a human) |
| pause | sprints/2026-09-07-pace-task-triage-hotfix | sprints/2026-09-07-pace-task-triage-hotfix | not shipped → design status: paused (resume_when to be written by a human) |
| pause | sprints/2026-09-13-pi-agent-9-10 | sprints/2026-09-13-pi-agent-9-10 | not shipped → design status: paused (resume_when to be written by a human) |
| pause | sprints/2026-09-13-telegram-style-hotfix | sprints/2026-09-13-telegram-style-hotfix | not shipped → design status: paused (resume_when to be written by a human) |
| pause | sprints/2026-09-14-athena-9-9-9-local-hotfix | sprints/2026-09-14-athena-9-9-9-local-hotfix | not shipped → design status: paused (resume_when to be written by a human) |
| pause | sprints/2026-09-16-cc-agent-turn-cap | sprints/2026-09-16-cc-agent-turn-cap | not shipped → design status: paused (resume_when to be written by a human) |
| move | sprints/2026-09-20-contract-parser-diagnostics | archive/sprints/2026-09/2026-09-20-contract-parser-diagnostics | shipped (items.yaml done) |
| move | sprints/2026-09-20-evidence-pipeline-integrity | archive/sprints/2026-09/2026-09-20-evidence-pipeline-integrity | shipped (items.yaml done) |
| move | sprints/2026-09-20-heredoc-aware-shell-guard | archive/sprints/2026-09/2026-09-20-heredoc-aware-shell-guard | shipped (items.yaml done) |
| move | sprints/2026-09-20-index-overflow-root-transaction | archive/sprints/2026-09/2026-09-20-index-overflow-root-transaction | shipped (items.yaml done) |
| move | sprints/2026-09-20-review-binding-preflight | archive/sprints/2026-09/2026-09-20-review-binding-preflight | shipped (items.yaml done) |
| move | sprints/2026-09-20-runtime-secret-false-positive | archive/sprints/2026-09/2026-09-20-runtime-secret-false-positive | shipped (items.yaml done) |
| pause | sprints/2026-09-21-writer-provenance-and-repo-boundary | sprints/2026-09-21-writer-provenance-and-repo-boundary | not shipped → design status: paused (resume_when to be written by a human) |
| move | sprints/2026-09-24-s0-gate-hotfix-9-9-9-p1 | archive/sprints/2026-09/2026-09-24-s0-gate-hotfix-9-9-9-p1 | shipped (items.yaml done) |
| move | sprints/2026-09-24-s1-single-source-build | archive/sprints/2026-09/2026-09-24-s1-single-source-build | shipped (items.yaml done) |
| move | sprints/2026-09-24-s2-gate-core | archive/sprints/2026-09/2026-09-24-s2-gate-core | shipped (items.yaml done) |
| keep | sprints/2026-09-24-s4-state-v2 | sprints/2026-09-24-s4-state-v2 | current sprint |
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

## Untracked/ignored files that move but stay untracked (32; a rollback leaves them at the new path; months holding them are not packed)

- sprints/2026-08-27-athena-9-9-8: 2 file(s), e.g. .ai_state/sprints/2026-08-27-athena-9-9-8/stop-failures.jsonl
- sprints/2026-09-06-athena-9-9-9: 2 file(s), e.g. .ai_state/sprints/2026-09-06-athena-9-9-9/.DS_Store
- sprints/2026-09-20-contract-parser-diagnostics: 2 file(s), e.g. .ai_state/sprints/2026-09-20-contract-parser-diagnostics/stop-failures.jsonl
- sprints/2026-09-20-evidence-pipeline-integrity: 2 file(s), e.g. .ai_state/sprints/2026-09-20-evidence-pipeline-integrity/stop-failures.jsonl
- sprints/2026-09-20-heredoc-aware-shell-guard: 2 file(s), e.g. .ai_state/sprints/2026-09-20-heredoc-aware-shell-guard/stop-failures.jsonl
- sprints/2026-09-20-index-overflow-root-transaction: 2 file(s), e.g. .ai_state/sprints/2026-09-20-index-overflow-root-transaction/stop-failures.jsonl
- sprints/2026-09-20-review-binding-preflight: 2 file(s), e.g. .ai_state/sprints/2026-09-20-review-binding-preflight/stop-failures.jsonl
- sprints/archive/2026/2026-07-14-athena-9-9-3-review-fixes: 4 file(s), e.g. .ai_state/sprints/archive/2026/2026-07-14-athena-9-9-3-review-fixes/token-usage.yaml
- sprints/archive/2026/2026-07-25-athena-9-9-6-prompt-engineering: 4 file(s), e.g. .ai_state/sprints/archive/2026/2026-07-25-athena-9-9-6-prompt-engineering/token-usage.yaml
- sprints/archive/2026/2026-07-25-harness-gate-p1-p4: 4 file(s), e.g. .ai_state/sprints/archive/2026/2026-07-25-harness-gate-p1-p4/token-usage.yaml
- sprints/archive/2026/2026-07-28-installation-sync-w31-w34: 2 file(s), e.g. .ai_state/sprints/archive/2026/2026-07-28-installation-sync-w31-w34/tool-trace.jsonl
- sprints/archive/2026/2026-07-29-athena-9-9-6-hotfix2: 4 file(s), e.g. .ai_state/sprints/archive/2026/2026-07-29-athena-9-9-6-hotfix2/token-usage.yaml

## Blockers (56)

- sprints/2026-08-27-athena-9-9-8 is read by vibeCoding/scripts/validate-athena-9.9.8.py:731:    eval_path = ROOT / ".ai_state/sprints/2026-08-27-athena-9-9-8/eval-ac11.md"
- sprints/2026-09-20-contract-parser-diagnostics is read by vibeCoding/scripts/tests/athena999/test_heredoc_guard.py:55:POSITIVE_TEE_TRUNCATE = ("tee .ai_state/sprints/2026-09-20-contract-parser-diagnostics/cleanup-pass.md "
- sprints/2026-09-20-review-binding-preflight is read by vibeCoding/scripts/tests/athena999/test_heredoc_guard.py:53:POSITIVE_TEE = ("tee -a .ai_state/sprints/2026-09-20-review-binding-preflight/session-log.md "
- index-overflow.md is read by vibeCoding/athena/adapters/cc/package/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/athena/adapters/cc/package/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/athena/adapters/cx/package/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/athena/adapters/cx/package/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/athena/adapters/pi/top/plugin/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/athena/adapters/pi/top/plugin/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/claude/9.9.9/.claude/hooks/_index-bounds.cjs:4: * Overflow is copied to .ai_state/index-overflow.md, never dropped.
- index-overflow.md is read by vibeCoding/claude/9.9.9/.claude/hooks/_index-bounds.cjs:84:    pointer(id) { return `.ai_state/index-overflow.md#${id}`; },
- index-overflow.md is read by vibeCoding/claude/9.9.9/.claude/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/claude/9.9.9/.claude/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/codex/9.9.9/.codex/hooks/_index_bounds.py:3:Overflow is copied to .ai_state/index-overflow.md, never dropped.
- index-overflow.md is read by vibeCoding/codex/9.9.9/.codex/hooks/_index_bounds.py:99:        return f".ai_state/index-overflow.md#{ident}"
- index-overflow.md is read by vibeCoding/codex/9.9.9/.codex/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/codex/9.9.9/.codex/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/pi-agent/plugin/skills/pace/templates/_index.md:18:route_history: []                 # re-route 记录, 最多 10 条、单条 ≤160B; 溢出进 .ai_state/index-overflow.md
- index-overflow.md is read by vibeCoding/pi-agent/plugin/skills/pace/templates/_index.md:109:[由主 agent 在 stage 切换时简短追加; 最多 10 条、单条 ≤160B; 溢出由 index-updater 搬进 .ai_state/index-overflow.md]
- index-overflow.md is read by vibeCoding/scripts/tests/athena999/test_state_review.py:296:            self.assertIn('.ai_state/index-overflow.md', text, template)
- index-overflow.md is read by vibeCoding/scripts/tests/athena999/test_state_review.py:307:             '.ai_state/index-overflow.md'],
- index-overflow.md is read by vibeCoding/scripts/tests/athena999/test_state_review.py:314:             '.ai_state/index-overflow.md'],
- harness-patches.md is read by vibeCoding/athena/evals/fixtures/test_state_regressions.py:215:        (root / 'old.js').write_text('// see .ai_state/harness-patches.md\n')
- harness-patches.md is read by vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs:174:    // P2 fix (2026-07-25, .ai_state/proposals.md P2; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs:310: * P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs:343:// 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"收
- harness-patches.md is read by vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs:482:    // 9.9.3 已修 → 9.9.6 升级回归 → 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs:490:    ".ai_state/harness-patches.md", ".ai_state/proposals.md",
- harness-patches.md is read by vibeCoding/claude/9.9.6/LOCAL-PATCHES.md:21:逐条跑消费侧项目 `.ai_state/harness-patches.md` 里的复核命令; 命中"已被覆盖"的, 从本目录
- harness-patches.md is read by vibeCoding/claude/9.9.8/.claude/hooks/delivery-gate.cjs:174:    // P2 fix (2026-07-25, .ai_state/proposals.md P2; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.8/.claude/hooks/delivery-gate.cjs:396: * P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.8/.claude/hooks/delivery-gate.cjs:429:// 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"收
- harness-patches.md is read by vibeCoding/claude/9.9.8/.claude/hooks/delivery-gate.cjs:568:    // 9.9.3 已修 → 9.9.6 升级回归 → 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/claude/9.9.8/.claude/hooks/delivery-gate.cjs:576:    ".ai_state/harness-patches.md", ".ai_state/proposals.md",
- harness-patches.md is read by vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs:190:    // P2 fix (2026-07-25, .ai_state/proposals.md P2; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs:638: * P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs:671:// 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"收
- harness-patches.md is read by vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs:811:    // 9.9.3 已修 → 9.9.6 升级回归 → 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs:819:    ".ai_state/harness-patches.md", ".ai_state/proposals.md",
- harness-patches.md is read by vibeCoding/codex/9.9.6/.codex/hooks/delivery-gate.py:938:# 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"
- harness-patches.md is read by vibeCoding/codex/9.9.6/.codex/hooks/delivery-gate.py:1113:        # 9.9.3 已修 -> 9.9.6 升级回归 -> 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/codex/9.9.6/.codex/hooks/delivery-gate.py:1123:        ".ai_state/harness-patches.md",
- harness-patches.md is read by vibeCoding/codex/9.9.6/.codex/hooks/delivery-gate.py:1257:    P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/codex/9.9.8/.codex/hooks/delivery-gate.py:1013:# 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"
- harness-patches.md is read by vibeCoding/codex/9.9.8/.codex/hooks/delivery-gate.py:1188:        # 9.9.3 已修 -> 9.9.6 升级回归 -> 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/codex/9.9.8/.codex/hooks/delivery-gate.py:1198:        ".ai_state/harness-patches.md",
- harness-patches.md is read by vibeCoding/codex/9.9.8/.codex/hooks/delivery-gate.py:1332:    P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py:1388:# 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"
- harness-patches.md is read by vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py:1567:        # 9.9.3 已修 -> 9.9.6 升级回归 -> 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py:1577:        ".ai_state/harness-patches.md",
- harness-patches.md is read by vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py:1781:    P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs:190:    // P2 fix (2026-07-25, .ai_state/proposals.md P2; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs:595: * P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
- harness-patches.md is read by vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs:628:// 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"收
- harness-patches.md is read by vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs:767:    // 9.9.3 已修 → 9.9.6 升级回归 → 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
- harness-patches.md is read by vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs:775:    ".ai_state/harness-patches.md", ".ai_state/proposals.md",

## Rollback

`git reset --hard pre-athena-10.1-state` (real run only). It restores tracked files only: afterwards move the untracked/ignored files listed above back to their old paths (or delete them) and remove `.ai_state/.runtime/{probe.json,_index.v1.md,snapshots/}` — the restored .gitignore no longer hides them, so a later `git add -A` would commit them.
