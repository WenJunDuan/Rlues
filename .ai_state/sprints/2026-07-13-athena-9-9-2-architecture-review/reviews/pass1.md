# Review Pass 1 — Athena 9.9.2 overall architecture upgrade

Date: 2026-07-13
Path: System
Review mode: native 2 + 1; this file contains the merged reviewer and spec-compliance results. Evaluator result is appended after merge.

## Scope

- Authoritative contract: `design.md` AC1–AC12.
- Sprint evidence: `checklist.yaml`, `implementation-plan.md`, `runtime-verify.md`, `cleanup-pass.md`, `review-validation.md`.
- Implementation: `vibeCoding/claude/9.9.2/**`, `vibeCoding/codex/9.9.2/**`, `vibeCoding/scripts/**`.
- Baseline: committed 9.9.1 package trees.
- Release claims: both 9.9.2 CHANGELOG/RELEASE files.

## Review provenance

- reviewer: `019f5a51-ac49-7423-b5bd-c4e690a9fda9`, read-only, bound through schema-v1 raw event + assignment handshake.
- spec-compliance: `019f5a55-5b4a-7423-8b11-1a248a67e950`, read-only, bound through schema-v1 raw event + assignment handshake.
- Both agents returned findings without modifying files.
- Main thread independently reran host validation and reproduced gate/config failures before merging.

## Executed evidence

| Command/check | Actual result |
|---|---|
| `python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py` | **33/33 PASS** |
| `node vibeCoding/scripts/test-athena-claude-9.9.2-runtime.cjs` | **73 PASS / 0 FAIL / 0 SKIP**, including live temp-HOME Claude Code 2.1.203 and 2.1.206 loads |
| `python3 vibeCoding/scripts/validate-athena-9.9.2.py` | **123 PASS / 10 FAIL** |
| Temporary-HOME 9.9.2 setup | PASS; CC/CX asset verification 0 drift |
| Temp-HOME `codex --strict-config doctor --json` | FAIL: `config.load=fail` |
| Temp-HOME `codex debug prompt-input` | FAIL: `Model provider custom-openai not found` |
| Official quick_validate rerun | **52 skills / 0 individual failures**; validator's expected total 62 is stale |
| Actual sprint checklist validator | BLOCK: all 16 statuses are `done`, gate requires `completed` |
| Actual sprint evidence validator | BLOCK: missing `evidence.yaml` |
| Relocated F-series scripts | 6 deterministic failures from `vibeCoding/vibeCoding/...` path construction; end-to-end drill alone passed |
| `git diff --check` | PASS |

Official Codex configuration contract: `model_provider` must equal an id under `model_providers.<id>`; see https://developers.openai.com/codex/config-reference#configtoml . The package selects `custom-openai` but defines `model_providers.custom_openai`.

## Reviewer Findings

### P0 — Release blockers

#### P0-1 — No contract-compliant `9.9.1 → 9.9.2` migration

Design §7.2 and AC3 require a targeted transactional migration with dry-run, rollback, idempotence and preservation of user-owned provider/MCP/plugin/trust/permission/unknown fields. Implementation deletes the executable migrator/tests and replaces them with `AI-MIGRATION-GUIDE.md` prose.

This is a behavioral contract replacement, not an implementation detail:

- setup refuses old endpoints and routes them to `/athena-migrate`;
- the installed 9.9.1 migrate skill cannot know the new 9.9.2 guide;
- the guide lives outside the hidden package manifest and is not installed by setup;
- no executable transaction, dry-run, fault-injection rollback, idempotence or preservation fixture remains;
- validator/runtime only search for guide strings.

Evidence:

- `design.md` §7.2 / AC3;
- `vibeCoding/codex/9.9.2/AI-MIGRATION-GUIDE.md:3-7`;
- `vibeCoding/codex/9.9.2/.codex/skills/athena-migrate/SKILL.md:9-20`;
- `vibeCoding/codex/9.9.2/.codex/skills/athena-setup/scripts/setup-athena.py:325-329`;
- `vibeCoding/scripts/validate-athena-9.9.2.py:418-422`.

Required: restore an executable, tested `9.9.1 → 9.9.2` transactional migration or explicitly revise the authoritative design with user approval and re-review before implementation. Current evidence cannot satisfy AC3.

#### P0-2 — The primary impl-entry spec-gate is prompt-only

Design §4.2 and AC5 say Feature/Refactor/System **cannot enter impl** without machine-recognizable acceptance criteria. The implementation adds a PACE reminder, while both executable gates return immediately until `stage == ship`.

Evidence:

- CC `skills/pace/SKILL.md:81` and CX `:83`: prompt instruction only;
- CC `hooks/delivery-gate.cjs:430-445`;
- CX `hooks/delivery-gate.py:605-625`;
- no test attempts a plan/design → impl transition.

Required: add an executable transition enforcement point and positive/negative tests on both endpoints. Ship-time validation remains defense in depth, not the primary gate.

#### P0-3 — CC rejects the Chinese acceptance heading emitted by its own template

CC uses:

```js
/^#{2,3}\s*\**\s*(?:acceptance criteria|验收标准)\b/i
```

JavaScript `\b` does not create the expected boundary after Chinese characters. Reproduction:

```text
"## 验收标准" false
"## 验收标准 (acceptance criteria)" false
"## Acceptance Criteria" true
```

The packaged CC design template emits `## 验收标准 (acceptance criteria)`, so a normal generated sprint is blocked at ship. Current CC tests use only the English heading.

Evidence: CC `hooks/delivery-gate.cjs:350`, CC design template `skills/pace/templates/sprints/design.md:30`, CC runtime fixture `test-athena-claude-9.9.2-runtime.cjs:190`.

#### P0-4 — Fresh Codex installation produces an unloadable configuration

The package selects:

```toml
model_provider = "custom-openai"
[model_providers.custom_openai]
```

The selected provider id does not match the registered id. A temporary-HOME install succeeds at file-copy/hash validation, then current Codex 0.144.1 reports:

```text
config.load: fail
Error: Model provider `custom-openai` not found
```

Official reference: https://developers.openai.com/codex/config-reference#configtoml (`model_provider` is a provider id from `model_providers`).

Required: align the selected provider with a valid registered/built-in provider and keep strict-config doctor + prompt-input in the release gate.

#### P0-5 — Current sprint cannot pass its own delivery gate

- `checklist.yaml` uses `status: done` for all 16 tasks; both gates require the exact canonical value `completed`.
- `evidence.yaml` is absent.
- I1–I8 contain `design_ref` but no executable evidence mapping.
- generator implementation lifecycle evidence is absent from the sprint ledger; current ledger only contains review agents.

Direct invocation produced:

```text
checklist BLOCK: statuses=['done', ...]
evidence BLOCK: missing evidence.yaml
```

Required: normalize task status, add evidence records with explicit pass/fail results and actual tool IDs, and provide truthful implementation lifecycle evidence. Do not synthesize old events.

#### P0-6 — Quantum 7→2 consolidation broke executable regression scripts and retained deleted-skill routing

Six scripts moved from `scripts/` to `vibeCoding/scripts/` but retain `ROOT = Path(__file__).resolve().parents[1]`. They now construct paths under `.../vibeCoding/vibeCoding/...` and fail. Executed failures include:

- `test-scaffold-page-gen.py`;
- `test-db-unit-gen.py`;
- `test-security-e2e.py`;
- `test-biz-delivery-loop.py`;
- `test-delivery-gate.py`;
- `test-token-usage-collector.py`.

The release validator does not execute these scripts.

Additionally, `quantum-codegen` playbooks still instruct agents to invoke removed skills such as `project-data-reader`, `unit-test-gen`, `playwright-e2e` and `security-test`. The CHANGELOG claim of zero active old-name residue is false.

Required: decide whether this EXTRA scope remains. If retained, add a design addendum/ACs, fix paths, update all progressive-disclosure references, and run the complete historical regression chain against the new modes.

### P1 — Must fix before the next review

#### P1-1 — Spec-gate authorization and requirement linkage are weaker than design

- `spec_gate_exception == current_sprint_slug` bypasses without reason, user authorization or expiry.
- Any `.ai_state/requirements/*.md` containing a matching section can satisfy any sprint; no current-design link is required.
- placeholder rejection is exact-string-only, so `TODO: define later` and `works correctly.` can pass.
- ship checks existence of one criterion, not AC-by-AC mapping to checklist/evidence/review.

This violates design §§4.3–4.5 and AC6.

#### P1-2 — The 9.9.2 validator is an incomplete/broken fork

Deterministic validator defects:

- baseline uses old commit/tree constants and compares the wrong history;
- “future version” rejects every target `9.9.2` marker because the ceiling remains 9.9.1;
- quick_validate expects 62 although 26 × 2 = 52, while all 52 individually pass;
- AI guide presence is checked under `.codex/AI-MIGRATION-GUIDE.md` although the file is at package root;
- config expectation says built-in `openai`, while package config selects a broken custom id;
- no route-source drift test;
- migration checks were reduced to prose markers;
- it does not execute the relocated F-series regressions.

Actual result: **123 PASS / 10 FAIL**. AC10 is not met.

#### P1-3 — Two-tier memory implementation is incomplete

Explicit Tier1/Tier2 and retrieval-router language appears only in the `_index` templates. Required init/checkpoint/session-start/status behavior was not implemented; several active init/status identities still name older versions. AC7 is not met.

#### P1-4 — Architecture/current-state truth is stale

- `.ai_state/architecture/ARCHITECTURE.md` still identifies 9.9.1 as current and does not index `athena-9.9.2.md`.
- `_index.pointers.latest_architecture_update` still points to the old 9.9.1 update.
- `blockers-and-roadmap.md` retains older three-primitive/patch framing.

Adding a subsystem file without updating the architecture entrypoint does not satisfy the System-path architecture gate.

#### P1-5 — Release evidence and documentation are stale or platform-wrong

- `runtime-verify.md` and both RELEASE files report `71/0/2`; host evidence is now `73/0/0`.
- CX RELEASE uses Claude Code versions 2.1.203/2.1.206 as Codex compatibility levels.
- CX RELEASE tells users to execute a `.py` file with `node` and attributes CC totals to it.
- CX RELEASE describes CC plugin defaults and links only Claude docs.
- CHANGELOG simultaneously says semantic re-route remains mandatory and is downgraded to a prompt.
- `review-validation.md` still describes the pre-implementation state and seven tasks.

#### P1-6 — Cleanup claim is false

`vibeCoding/codex/9.9.2/.codex/hooks/__pycache__/` contains eleven `cpython-310.pyc` files, while `cleanup-pass.md` and CHANGELOG claim bytecode was removed. The release validator correctly treats these as forbidden, although it also creates/observes them inconsistently.

### P2 — Quality

- Several active init/status headings still carry 9.9.1 or earlier identities.
- Setup tests retain `test_setup_991.py` names, obscuring active release coverage.
- RELEASE cites broad secondary trend claims where product behavior should cite official platform contracts.

## Spec Compliance

**Overall: 3 SATISFIED / 8 DEVIATED / 1 MISSING.**

| AC | Result | Summary |
|---|---|---|
| AC1 — active 9.9.2 identity | DEVIATED | package identity mostly updated; init docs/validator still reject or announce older versions |
| AC2 — fresh/same-version setup | SATISFIED | setup file/hash transaction and second-run verification pass; runtime Codex config still fails under P0-4 |
| AC3 — transactional upgrade | DEVIATED | executable migration replaced by uninstalled/unverified AI prose |
| AC4 — four primitives | SATISFIED | CC/CX entry prompts and MCP references are consistent |
| AC5 — impl-entry spec gate | DEVIATED | prompt-only; executable gate runs only at ship |
| AC6 — ship spec/evidence revalidation | DEVIATED | no AC mapping; under-scoped exception and unrelated-requirement bypass |
| AC7 — two-tier memory | DEVIATED | template prose only; required consumer surfaces incomplete |
| AC8 — single route source + drift test | DEVIATED | pace delegation is correct; validator drift test missing |
| AC9 — plugin/MCP arbitration | SATISFIED | five rules and degradation reporting present |
| AC10 — zero-failure validation | DEVIATED | validator 123/10; moved regressions fail; fresh Codex config invalid |
| AC11 — formal 2+1 PASS | MISSING | pass1 is the first formal review and is REWORK |
| AC12 — complete state evidence | DEVIATED | missing evidence.yaml/evaluator/ship evidence; gate-incompatible statuses and stale architecture entrypoint |

## EXTRA scope

Quantum 7→2 consolidation deletes seven public skills, adds two hubs, changes CX registration and multiple delivery-loop callers. It is absent from authoritative `design.md` and lacks dedicated compatibility/migration ACs. Checklist I8 references only “fable5 合并方案 + user 确认命名”; no linked decision artifact establishes scope or acceptance.

This work may remain only after a design addendum records the authorized scope, compatibility policy, migration behavior and test matrix, followed by re-review.

## Evidence Cross-Check

| Claim/task group | Claimed evidence | Cross-check | Result |
|---|---|---|---|
| I0–I8 all done | checklist statuses | statuses are `done`, which both gates reject | FAIL |
| Implementation evidence complete | sprint directory | `evidence.yaml` absent; I1–I8 have no evidence fields | FAIL |
| runtime verify complete | `runtime-verify.md` | host rerun changes CC result to 73/0/0; validator is red | FAIL |
| cleanup complete | `cleanup-pass.md` | packaged `__pycache__/*.pyc` exists | FAIL |
| 9.9.2 validator complete | validator | 123 pass / 10 fail; internal fork defects | FAIL |
| old F tests preserved after move | CHANGELOG | six scripts fail from wrong root and removed-skill targets | FAIL |
| quantum callers migrated | CHANGELOG | playbooks retain deleted skill names | FAIL |
| architecture updated | subsystem doc | `ARCHITECTURE.md` entrypoint remains 9.9.1 | FAIL |
| four primitives | package prompts/references | direct textual parity and reference checks pass | PASS |
| fresh file install | setup tests/temp HOME | copy/hash verification passes | PASS |

`done_without_evidence`: at least I1–I8 (8 tasks). There is no `evidence.yaml` to map tool calls/results to any implementation task. Evidence Cross-Check therefore independently caps the review below PASS; the verified P0 defects require REWORK.

## Merged reviewer recommendation

**REWORK.** Fix P0-1 through P0-6, then rerun the complete validator/runtime/regression matrix, refresh `.ai_state` evidence and architecture truth, and generate `pass2.md` through a new formal 2+1 review.

## Evaluator Appendix

Evaluator: `019f5a6d-7ef1-7cd1-a49b-0391ef8422fc`
Mode: read-only, post-merge evidence evaluation

### Evidence Cross-Check Assessment

The evaluator independently confirmed:

- checklist completion is unsupported because `done` is rejected by both gates;
- implementation evidence is unsupported because `evidence.yaml` is absent and I1–I8 lack executable mapping;
- AC3 migration, AC5 impl-entry gate, CC Chinese-heading parsing, fresh Codex configuration, validation, runtime freshness, cleanup and architecture-entrypoint defects are supported by source and command evidence;
- four primitives, plugin/MCP arbitration and narrow file-copy/hash setup behavior are supported;
- at least I1–I8 are `done_without_evidence`.

### Contradictions confirmed

1. Transactional migration in design versus AI-guided prose in implementation.
2. Mechanical impl-entry spec-gate in design versus prompt-only entry behavior.
3. “已验证” release claims versus validator/regression/config failures.
4. I0–I8 “done” versus gate-incompatible status vocabulary and absent evidence.
5. Cleanup claims versus packaged bytecode.
6. 9.9.2 subsystem claim versus 9.9.1 architecture entrypoint/pointer.
7. Quantum 7→2 release-significant EXTRA scope without authoritative design addendum/ACs.

## VERDICT

REWORK

## next_action

Return to `impl`. Resolve P0-1 through P0-6, formally reconcile migration strategy and quantum 7→2 scope with the authoritative design, restore gate-compatible checklist/evidence and architecture state, rerun the complete validator/runtime/regression/config matrix to zero unreviewed failures, refresh all release evidence, then create `reviews/pass2.md` through a new bound 2+1 review.

### Evaluator rationale

Core architectural documentation for four primitives and MCP arbitration is present, but executable behavior, migration safety, package validity, evidence integrity and release documentation materially contradict the approved System contract. AC3, AC5, AC6, AC7, AC8, AC10, AC11 and AC12 remain unmet; shipping 9.9.2 from this state would be fail-open.
