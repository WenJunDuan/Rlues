# Fable5 Implementation Brief — Athena 9.9.2 overall upgrade

## Mission

Implement the complete Athena 9.9.2 System upgrade in `/Users/mi_manchi/workspace/Rlues`.

The user explicitly chose the release name `9.9.2` for this structural upgrade. Do not rename or defer it to 9.10.0. The mandatory scope is:

- pace + `.ai_state` dual core;
- four primitives: Workflow / SubAgent / Skill / MCP;
- Feature+ spec-gate before impl plus ship revalidation;
- two-tier memory with `_index.md` as retrieval router;
- plugin/MCP capability arbitration;
- CC/CX setup, 9.9.1 migration, tests, runtime verification and release closure.

## Read first

1. `/Users/mi_manchi/workspace/Rlues/.ai_state/_index.md`
2. `/Users/mi_manchi/workspace/Rlues/.ai_state/sprints/2026-07-13-athena-9-9-2-architecture-review/design.md`
3. `/Users/mi_manchi/workspace/Rlues/.ai_state/sprints/2026-07-13-athena-9-9-2-architecture-review/reviews/pre-implementation-review.md`
4. `/Users/mi_manchi/workspace/Rlues/vibeCoding/claude/9.9.2-DRAFT-architecture.md` as non-authoritative input
5. committed 9.9.1 package trees as the behavioral baseline

The sprint `design.md` is authoritative when the older draft conflicts with it.

## Execution boundary

Path: `System`.

Before changing package code:

1. Create an isolated worktree/branch from the current repository state while preserving the user's untracked 9.9.2 draft/package inputs. If the platform cannot include untracked inputs automatically, copy them into the worktree with hashes recorded before modification; do not delete or overwrite the originals.
2. Record the absolute worktree path in `.ai_state`.
3. Restore/verify fail-closed subagent binding. Never guess an agent ID or fabricate lifecycle evidence.
4. Use TDD: add a failing test for each behavioral change before implementation.

Allowed implementation surfaces:

- `vibeCoding/claude/9.9.2/**`
- `vibeCoding/codex/9.9.2/**`
- `vibeCoding/scripts/**` for 9.9.2 validators/fixtures
- the linked 9.9.2 implementation sprint under `.ai_state/**`
- `.ai_state/architecture/**` during polish/ship

Do not modify committed 9.9.0 or 9.9.1 package baselines except adding non-invasive tests that reference them. Preserve unrelated dirty files.

## Non-negotiable architecture

### Dual core

- PACE is the control plane.
- `.ai_state` is the durable data plane.
- Conversation/plugin state cannot replace either.

### Four primitives

- Workflow: PACE route/stage/gate authority.
- SubAgent: bounded delegated execution.
- Skill: reusable method/domain knowledge.
- MCP: external reach/data/action.

MCP is conceptually a primitive and operationally supplied by the external capability layer. It never owns workflow sequencing or gate policy.

### Spec-gate

- Applies to Feature, Refactor and System before entering impl.
- Requires machine-recognizable, observable acceptance criteria.
- File existence and placeholder headings are insufficient.
- Ship rechecks criterion-to-evidence mapping and post-impl design changes.
- Any escape is scoped, explicit, recorded and user-authorized.

### Two-tier memory

- Tier 1: transient conversation/tool context.
- Tier 2: versioned `.ai_state` truth.
- `_index.md`: bounded retrieval router, not duplicated storage.
- Define persistence events and consumers for retained index fields.

## Mandatory RED tests

Write failing tests first for at least:

1. 9.9.2 package identity and active-version drift.
2. Fresh CC/CX/both install and same-version verification.
3. 9.9.1 → 9.9.2 migration, idempotence and rollback injection.
4. Spec-gate valid/missing/placeholder/linked-requirements/path-exemption cases.
5. Ship spec-to-evidence revalidation.
6. Route-source duplication detection.
7. Four-primitives CC/CX semantic parity.
8. MCP/plugin defaults versus documentation consistency.
9. Two-tier memory template/init/checkpoint/session-start/status behavior.
10. Native collaboration lifecycle event persistence and binding.

Existing 9.9.1 test totals are baseline evidence only, never 9.9.2 completion evidence.

## Implementation sequence

### Phase 1 — Release harness and identity

- Add/parameterize a 9.9.2 release validator.
- Make current incomplete package fail RED for the expected reasons.
- Update active identity, setup discovery, templates, status/init output, RELEASE and commands.

### Phase 2 — Distribution

- Repair fresh install.
- Implement 9.9.1 → 9.9.2 targeted migration.
- Preserve user-owned config and transactional guarantees.

### Phase 3 — Four primitives and capability layer

- Update CC `CLAUDE.md` and CX `AGENTS.md`.
- Update pace/orchestration/plugins references.
- Add `references/mcp.md` to both endpoints.
- Keep platform-specific mechanics honest.

### Phase 4 — Spec-gate

- Implement semantic acceptance-criteria parser/validator.
- Wire the primary gate before impl.
- Add ship defense-in-depth criterion/evidence mapping.
- Update templates and stage docs.

### Phase 5 — Two-tier memory

- Update `_index` template/semantics.
- Audit field consumers.
- Update init/checkpoint/session-start/status and compaction/handoff recovery.

### Phase 6 — Integration and validation

- Refresh plugin defaults and degradation semantics.
- Prove lifecycle ledger behavior on the surfaced runtime.
- Run all syntax/unit/migration/runtime/temp-HOME tests.
- Produce `runtime-verify.md` with commands and outputs.

### Phase 7 — Review and release

- Run formal reviewer + spec-compliance in parallel, then evaluator.
- Fix all P0/P1 findings and repeat until PASS.
- Run polish, update architecture current-state docs and release evidence.
- Only then commit/merge/push/ship when the user requests it.

## Acceptance

All AC1–AC12 in the authoritative design must be checked with reproducible evidence. Completion requires:

- zero unresolved P0/P1;
- 9.9.2 fresh install and 9.9.1 migration success;
- behavioral spec-gate evidence;
- lifecycle binding evidence without fabricated ledgers;
- formal PASS review;
- current `.ai_state` and architecture records.

## Required response format from Fable5

Return:

1. worktree/branch and exact changed-file list;
2. RED tests added before implementation;
3. implementation summary mapped to AC1–AC12;
4. commands and actual outputs for validation/runtime/migration;
5. remaining blockers or deviations;
6. next PACE action.

