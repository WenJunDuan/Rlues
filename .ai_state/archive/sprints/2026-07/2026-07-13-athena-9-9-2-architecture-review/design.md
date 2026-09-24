# Athena 9.9.2 architecture implementation contract

> Status: authoritative review input for Fable5 implementation.
> Baseline: committed Athena 9.9.1 packages plus the untracked 9.9.2 draft/package trees present on 2026-07-13.
> Version decision: user explicitly approves structural changes under the release name `9.9.2`; do not re-route to `9.10.0` solely for version-number semantics.

## 1. Authority and scope

Athena 9.9.2 is a **System-level overall upgrade**, not a patch-only cleanup. The implementation must land all of the following as one coherent release:

1. `pace + .ai_state` dual core.
2. Four primitives: Workflow, SubAgent, Skill, MCP.
3. Feature+ spec-gate that prevents implementation before intent is testable.
4. Two-tier memory with `_index.md` as the persistent retrieval router.
5. Plugin/official-skill/MCP capability arbitration around the core.
6. CC/CX semantic parity without inventing symmetric runtime tools.
7. Install, migration, validation, runtime evidence, review and release documentation for 9.9.2.

The existing `vibeCoding/claude/9.9.2-DRAFT-architecture.md` is design input, not the final source of truth. This file plus the latest numeric review pass define the implementation contract.

## 2. Target architecture

### 2.1 Dual core

| Core | Responsibility | Must not own |
|---|---|---|
| `PACE` | Control plane: route, stage transitions, actor selection, gates and recovery | Durable project facts or runtime secrets |
| `.ai_state` | Data plane: durable requirements, design, state, evidence, review, architecture and decisions | Tool invocation mechanics or platform-specific orchestration APIs |

`PACE` decides **how work advances**. `.ai_state` records **what is true**. Neither plugin state nor conversation memory may replace either core.

### 2.2 Four primitives

The four primitives are peer concepts in the Athena execution model, but have distinct responsibilities:

| Primitive | Question answered | Contract |
|---|---|---|
| Workflow | How does work advance? | PACE owns route/stage/gate sequencing and remains the only workflow authority |
| SubAgent | Who performs an isolated bounded task? | Executes delegated work under red/yellow/green boundaries; lifecycle evidence is fail-closed where required |
| Skill | What reusable method or domain knowledge applies? | Provides workflow fragments, references, scripts and acceptance guidance; cannot start a second top-level workflow |
| MCP | What external system can the agent reach? | Provides tools/data/actions from external systems; does not own route, stage, actor selection or acceptance policy |

This resolves the current draft's duplicated placement of MCP. MCP is a primitive in the **execution model** and simultaneously implemented through the **external capability layer**; the diagram must distinguish conceptual role from deployment location instead of drawing MCP twice without explanation.

Official product framing supports these boundaries: Codex describes skills as reusable workflows, MCP as access to external systems, and subagents as delegated execution; Claude Code describes MCP as connection to external tools/data and plugins as distributable bundles of skills, agents, hooks and MCP servers.

### 2.3 Capability layer

Plugins, official skills, CLIs, browser tools and MCP servers are replaceable capability providers. They may implement or enrich a primitive, but never become a second workflow authority.

Precedence:

1. User instruction and project policy.
2. PACE stage/gate contract.
3. Athena skill contract.
4. External capability provider.

All retained outputs must be normalized into `.ai_state`; ephemeral exploration may remain in the conversation only when it is not used as delivery evidence or a future decision source.

## 3. PACE convergence

### 3.1 Single route source

- `athena-dev/SKILL.md` is the sole detailed source for route deliberation, confidence thresholds, route-note format and re-route protocol.
- `pace/SKILL.md` keeps the path/stage state machine, hard floors, write-zone routing and pointers to detailed references.
- CC and CX copies must be semantically equivalent; platform mechanics remain platform-specific.
- Validators must detect duplicated normative route-threshold blocks reintroduced into `pace/SKILL.md`.

### 3.2 Stage model

Athena continues to expose nine named stages:

- Core: plan, impl, review, ship.
- Conditional: brainstorm, roadmap, design, runtime-verify, polish.

“Core” means every non-hotfix normal delivery is organized around those checkpoints; it does not mean conditional stages are optional when their path requires them.

### 3.3 Re-route

- Mechanical file/module thresholds remain fail-closed triggers.
- Semantic triggers remain mandatory agent self-checks and produce a route reassessment; they are not silently downgraded to informational prose.
- Mechanical evidence is stronger than self-assessment, but lack of a mechanical signal is not evidence that scope has not expanded.
- Re-route remains upgrade-only unless the user explicitly authorizes a downgrade.

## 4. Spec-gate contract

### 4.1 Purpose

The spec-gate prevents implementation of a Feature/Refactor/System task while intent is not testable. A ship-only gate cannot satisfy this purpose.

### 4.2 Primary gate location

The primary spec-gate runs at the transition into `impl`:

| Path | Minimum requirement before impl |
|---|---|
| Feature | Current sprint `design.md` contains acceptance criteria, or a linked requirements artifact supplies them |
| Refactor | Design defines preserved behavior, changed boundaries, migration/rollback and acceptance criteria |
| System | Requirements + design define affected modules, contracts, non-goals, failure modes and measurable acceptance criteria |

Quick/Bugfix/Hotfix use their existing lighter contracts and are not forced through the Feature+ gate.

### 4.3 Semantic validation

File existence alone is insufficient. The gate must verify a machine-recognizable contract, for example:

- a non-empty `## Acceptance Criteria` section with numbered or checkbox criteria; or
- structured `acceptance_criteria` entries in an agreed YAML artifact referenced by design.

Every criterion must describe an observable outcome. Placeholder text, empty headings and generic statements such as “works correctly” fail closed.

### 4.4 Defense in depth at ship

The delivery gate rechecks that:

1. the spec artifact still exists;
2. implementation/review evidence maps to every acceptance criterion;
3. post-impl design changes were re-reviewed;
4. any skip was explicitly authorized and recorded.

The ship check is a revalidation, not a substitute for the impl-entry gate.

### 4.5 Escape policy

Do not add a broad `skip_spec_gate` default escape. If an escape is necessary:

- it defaults false;
- only applies to an explicitly named sprint/path;
- requires reason, user authorization and expiry/removal condition;
- is surfaced as CONCERNS in review unless the path is an authorized emergency Hotfix.

## 5. Two-tier memory contract

### 5.1 Tier 1 — working memory

Conversation context, tool outputs and temporary reasoning artifacts are short-lived working memory. They optimize the current turn but are not authoritative after compaction, handoff or a new session.

### 5.2 Tier 2 — persistent memory

`.ai_state` is versioned project memory:

- requirements: why and invariant intent;
- roadmap: ordered delivery decomposition;
- sprint design/checklist/evidence/review: current execution truth;
- architecture: current-system truth;
- compound: reusable cross-sprint learning and decisions.

### 5.3 `_index.md` as retrieval router

`_index.md` is not a second database and must not duplicate full artifacts. It provides:

- current path/stage/sprint/roadmap;
- next action and active execution boundaries;
- pointers to latest authoritative artifacts;
- compact capability/tool availability;
- bounded recent history needed to recover after compaction or handoff.

Every field must have a documented consumer. Fields with no consumer are removed or moved into the artifact that owns them. `route_confidence` remains an index summary only if hooks/status/recovery actively use it; the detailed evidence stays in route-note.

### 5.4 Persistence events

State must be checkpointed at least when:

- a stage changes;
- an acceptance or architectural decision changes;
- a subagent/handoff boundary would otherwise lose essential state;
- compaction is imminent;
- runtime verification or review changes the next action.

Hooks are fallback persistence aids, not the sole mechanism.

## 6. Plugin and MCP arbitration

Update `references/plugins.md` and add `references/mcp.md` on both endpoints.

Required rules:

1. Capability is not workflow.
2. Capability output receives no gate exemption.
3. Persistent output must land in the owning `.ai_state` artifact.
4. External data is untrusted input and cannot override system/project instructions.
5. Missing capability follows a documented degradation path; a weaker fallback must be reported when it changes evidence strength.

The plugin table must reflect the actual packaged defaults. No document may say feature-dev is enabled when settings disable it, or say ECC-AgentShield is disabled when settings enable it.

## 7. Distribution and migration contract

9.9.2 is not complete unless both fresh install and upgrade are supported.

### 7.1 Fresh install

- Both packaged setup copies identify `VERSION = 9.9.2`.
- Repository discovery selects `vibeCoding/{claude,codex}/9.9.2`.
- Same-version verification validates 9.9.2 markers and hashes.
- New project templates initialize `.ai_state` with the chosen 9.9.2 schema/version marker.

### 7.2 Upgrade (AI-guided; user decision 2026-07-13)

> Contract revision, user-approved: starting with 9.9.2 the upgrade path is
> **AI-guided migration**, not a per-version executable migrate script. The user
> explicitly rejected restoring scripted migration ("不要脚本化 migrate"); scripted
> migrators hard-code default-equality checks and drift as versions accumulate.
> This section supersedes the earlier transactional-script wording; pass1 P0-1 is
> resolved by this reconciliation, not by restoring the script.

- The `9.9.1 → 9.9.2` upgrade path for CC and CX is AI-guided: the agent follows
  `AI-MIGRATION-GUIDE.md`, reading the target CHANGELOG plus an old-vs-new package
  diff, and applies changes item by item.
- `AI-MIGRATION-GUIDE.md` ships at both package roots **and** inside
  `skills/athena-migrate/references/`, so it is installed into the user HOME by
  setup along with the skill; the two copies must stay byte-identical
  (validator-enforced).
- `athena-migrate` (SKILL.md) is the AI entry point and must point at the
  installed guide; `athena-setup` refuses old endpoints and routes them to
  `/athena-migrate`.
- Invariants preserved from the old contract (now guide red lines, checked by the
  release validator as documented invariants): timestamped backup before any
  irreversible step; preserve private hooks, custom providers, MCP servers,
  plugins, permissions, trust state, unknown fields and secret values; update
  only release-owned assets and defaults that still equal the 9.9.1 baseline;
  on failure restore the backup (no half-migrated state); never print secrets.
- Post-migration verification runs the 9.9.2 validator/runtime suites; a
  same-version re-run is read-only.
- Historical `9.9.0 → 9.9.1` scripted migration remains historical and must not
  be presented as the 9.9.2 migration.

### 7.3 Release identity

Update all active release identities, commands and examples. Historical changelog sections may retain historical version numbers. Validators must distinguish historical references from active 9.9.2 drift.

## 8. TDD and validation requirements

Fable5 must add failing tests before implementing each behavioral change.

Minimum suites:

1. 9.9.2 release validator covering both package roots.
2. Fresh install + same-version verification for CC-only, CX-only and both.
3. 9.9.1 → 9.9.2 AI-guided migration (per §7.2): guide present at package root and installed via `athena-migrate/references/`, both copies identical, red-line invariants (backup/preserve/rollback/no-secrets) documented, and `athena-migrate`/`athena-setup` route to the AI flow.
4. Spec-gate behavior: valid criteria, missing criteria, placeholder criteria, linked requirements, path exemptions and authorized escape.
5. Route-source drift test preventing normative threshold duplication.
6. Two-tier memory template/status/session-start contract tests.
7. Plugin/default documentation consistency checks.
8. JSON/TOML/YAML/frontmatter/Node/Python syntax checks.
9. CC/CX semantic parity checks with explicit allowed asymmetries.

Existing 9.9.1 validators do not count as 9.9.2 evidence unless parameterized to target 9.9.2 and demonstrated by output.

## 9. Acceptance criteria

- [ ] AC1: The release is consistently named 9.9.2 in active package identity, setup, templates, docs and validators.
- [ ] AC2: Fresh 9.9.2 install succeeds and a second same-version run is read-only and passes.
- [ ] AC3: An existing 9.9.1 CC/CX installation can migrate to 9.9.2 through the AI-guided flow (§7.2) without losing user-owned configuration: `AI-MIGRATION-GUIDE.md` is installed with the package, `athena-migrate`/`athena-setup` route to it, and its red lines mandate backup, user-ownership preservation and rollback-on-failure.
- [ ] AC4: Four primitives are documented consistently in CC/CX entry prompts and references, with no duplicated or conflicting ownership.
- [ ] AC5: Feature/Refactor/System cannot enter impl without machine-recognizable observable acceptance criteria.
- [ ] AC6: Ship revalidates spec-to-evidence mapping and post-impl design changes.
- [ ] AC7: Two-tier memory and `_index` retrieval-router semantics are reflected in templates, init, checkpoint, session-start and status documentation.
- [ ] AC8: `athena-dev` is the single detailed route source and validators detect future drift.
- [ ] AC9: Plugin/MCP arbitration docs reflect actual defaults and document evidence-strength degradation.
- [ ] AC10: CC/CX package validation and runtime suites pass with zero unreviewed failures.
- [ ] AC11: A formal 2+1 review reaches PASS after implementation; all P0/P1 findings are fixed and revalidated.
- [ ] AC12: `.ai_state` contains route, design, checklist, runtime verification, review, polish/architecture and ship evidence for the 9.9.2 release sprint.
- [ ] AC13: The quantum 7→2 consolidation (§13) is complete on both endpoints: the two hub skills expose all seven legacy capabilities as modes, no active caller/reference invokes a deleted skill name, CX registration lists exactly the two hubs, the AI migration guide covers removing the seven legacy skill directories, and the relocated F-series regression scripts execute against repository-root paths.

## 10. Non-goals

- Do not weaken generator lifecycle or design-change fail-closed protections.
- Do not make plugins, MCP servers or external services mandatory for core PACE operation.
- Do not overwrite user-owned provider/plugin/MCP/trust/permission configuration.
- Do not force byte-identical CC/CX implementations where platform mechanics differ.
- Do not reopen the user-approved `9.9.2` release name during implementation.

## 11. Official references

- Codex customization layers: https://developers.openai.com/codex/concepts/customization
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code settings: https://code.claude.com/docs/en/settings
- Codex configuration: https://developers.openai.com/codex/config-reference

## 13. Appendix — quantum skill consolidation 7→2 (user-approved EXTRA scope)

> Added post-pass1 to reconcile the EXTRA finding. The user approved this scope
> and the hub naming; it stays in 9.9.2. Decision artifact:
> `.ai_state/compound/2026-07-13-decision-quantum-7-to-2-consolidation.md`.

### 13.1 Scope

- Seven public fullstack-delivery skills are consolidated into two hubs on both
  endpoints: `scaffold-page-gen`, `scaffold-module-gen`, `db-schema-gen`,
  `unit-test-gen`, `security-test`, `playwright-e2e` → **quantum-codegen**
  (`mode=page|module|db|unit|security|e2e`, hot-path hub + progressive-disclosure
  playbooks under `references/`); `project-data-reader` → **quantum-data**.
- Skill count changes 31 → 26 per endpoint; CX `config.toml` registers the two
  hubs instead of the seven legacy names.

### 13.2 Compatibility and migration policy

- The seven legacy skill names are retired, not aliased. Historical annotations
  ("前身"), CHANGELOG history and migration instructions may reference them;
  active routing/caller text must not.
- Upgrade behavior is owned by the AI-guided migration (§7.2): remove the seven
  legacy skill directories from the user HOME, install the two hubs, and update
  CX `config.toml` registration.
- `.ai_state` data produced by the legacy skills (sprints, evidence, compound)
  is untouched; capability contracts (Convention Pack, Capability Manifest)
  keep their existing schemas under the new hub references.

### 13.3 Test matrix (AC13)

| Check | Vehicle |
|---|---|
| Hub SKILL/playbook routing has zero active legacy-name residue | release validator residue scan (annotation lines excluded) |
| Convention-pack validators still pass under hubs | `check_frontend_pack.py` / `check_backend_pack.py` / `check_security_e2e_pack.py` / `check_capability_manifest.py` |
| Historical F-series regressions run from `vibeCoding/scripts/` | `test-scaffold-page-gen.py`, `test-db-unit-gen.py`, `test-security-e2e.py`, `test-biz-delivery-loop.py`, `test-delivery-gate.py`, `test-token-usage-collector.py` (external `workspace/quantum` fixtures required by three of them are environment-dependent and reported, not silently skipped) |
| Delivery-loop callers reference only hub names | `check_delivery_loop_contract.py` SKILL_MARKERS + runtime harnesses |
| CX registration = exactly `quantum-codegen` + `quantum-data` | release validator config check |

## Round 1 · Critic Findings

The independent critic returned `NEEDS_REVISION` on the pass2 rework contract:

1. Per-AC evidence was under-specified: label presence, checklist text or an unrelated global PASS must never satisfy an AC whose own evidence is unknown/skip/fail.
2. Exception authorization lacked a structured user-authorization contract and conflicted with PASS-only shipping.
3. AC7 lacked a normative producer/consumer matrix for template, init, checkpoint, session-start/recovery, status and hooks.
4. AC12 mixed pre-ship readiness evidence with the post-push synchronization receipt.
5. Endpoint install destinations and active identity surfaces needed exact mappings; AC2/AC6/AC7/AC10/AC11 required more observable wording.

## Round 1 · Design Revision (normative addendum)

This addendum supersedes any weaker wording in §§4–9 for the final 9.9.2 rework.

### A. Per-AC evidence schema and gate

Every labeled acceptance criterion `ACn` must have at least one admissible evidence record in `evidence.yaml` with:

```yaml
- tool_use_id: stable-nonempty-id
  ac_id: ACn
  result: pass
  source: command | artifact | review
  command_or_artifact: "rerunnable command or sprint-relative existing file"
  observed_at: "UTC ISO-8601"
  summary: "actual observable result"
```

- `covers: [AC1, AC2]` remains allowed only when the same explicit `pass` record truthfully covers every listed AC; it is normalized as one passing mapping per label.
- `unknown`, `skip`, `fail`, checklist-only/design-only mentions, missing source artifacts and stale review references do not satisfy an AC.
- A global unrelated PASS cannot satisfy another AC.
- `source: review` is admissible only when `command_or_artifact` is the latest numeric `reviews/passN.md`, the file contains Spec Compliance + Evidence Cross-Check and its final evaluator verdict is PASS.
- Ship fails when any labeled AC lacks an admissible pass mapping. Required negative tests: unknown-only, checklist-only, mixed global-pass+unknown-AC, missing artifact and stale/non-PASS review.

### B. Spec-gate exception schema

An impl-entry exception is valid only when all fields are present and non-placeholder:

```yaml
spec_gate_exception: "<current sprint slug>"
spec_gate_exception_path: "Feature|Refactor|System"
spec_gate_exception_reason: "<specific reason>"
spec_gate_exception_authorized_by: "user:<stable user label>"
spec_gate_exception_authorized_at: "<UTC ISO-8601>"
spec_gate_exception_expiry: "<UTC ISO-8601>"
spec_gate_exception_removal_condition: "<observable condition>"
spec_gate_exception_emergency_hotfix: false
```

- Self/agent authorization, generic `user`, placeholders, mismatched path/sprint and expired records fail closed.
- For Feature/Refactor/System, an active exception may unblock the impl-entry check but **must block ship** until removed and normal acceptance/evidence mappings exist.
- Hotfix retains its separate emergency path; no Feature+ exception makes CONCERNS shippable. Final ship remains PASS-only.

### C. AC7 two-tier memory consumer matrix

| Surface | Required observable behavior (both endpoints) |
|---|---|
| `_index` template | Declare Tier1 as non-authoritative working context, Tier2 `.ai_state` as persistent truth, and `_index` as bounded retrieval router rather than a second database. |
| `athena-init` | Create the 9.9.2 Tier2 directories/schema from the current template; populate only fields present in that template; output active 9.9.2 identity. |
| `athena-checkpoint` | Persist stage, next_action, current sprint, authoritative pointers and bounded handoff history; session-log owns detailed turn history. |
| `session-start` / recovery | Read `_index` first, inject routed state/pointers, warn on missing pointed artifacts, and never elevate Tier1 conversation context over Tier2 truth. |
| `athena-status` | Report routed state from `_index`, resolve current authoritative pointers and flag missing/stale pointer targets. |
| hooks | Provide fallback snapshots/index updates only; hooks are not the sole producer of durable decisions or completion evidence. |

Validator/runtime tests must cover positive behavior plus missing/stale-pointer negatives for both endpoints. Fields named by init/status/recovery must exist in the 9.9.2 template; removed fields such as `cx_goal_default_on` are forbidden active references.

### D. Exact endpoint destinations and active identity surfaces

- CC runtime assets/config: `~/.claude`; installed guide: `~/.claude/skills/athena-migrate/references/AI-MIGRATION-GUIDE.md`.
- CX config/hooks/agents: `~/.codex`; CX skills and installed guide: `~/.agents/skills/{name}` and `~/.agents/skills/athena-migrate/references/AI-MIGRATION-GUIDE.md`.
- Package-root and installed-skill guide copies remain byte-identical per endpoint.
- Active identity checks include entry prompt, setup/init/status/checkpoint/session-start docs, package RELEASE current section, template header and validator/runtime commands. Historical CHANGELOG sections may retain historical numbers only when clearly historical.

### E. Refined acceptance semantics

- AC2 read-only same-version verification means no content/hash/mtime change to existing release-owned or user-owned target files.
- AC6 inherits section A and the latest-review freshness requirement.
- AC7 is satisfied only by the observable matrix in section C, not prose mention alone.
- AC10 requires every mandatory suite exit 0 with exact reported counts; skips are allowed only when explicitly reviewed and must not hide a mandatory environment check. Final host release evidence requires zero skips.
- AC11 requires the latest numeric passN artifact, valid bound reviewer/spec/evaluator lifecycles, Spec Compliance, Evidence Cross-Check and final evaluator PASS.

### F. AC12 pre-ship versus post-push sequence

- Pre-ship AC12 readiness requires route, authoritative design, completed checklist, per-AC passing evidence, runtime PASS, latest final review PASS, polish PASS and current architecture documentation.
- After the release commit is pushed, the main agent writes a ship receipt containing release commit, push result and fetched `main...origin/main = 0 0`; that receipt is committed and pushed as a final state-only commit, followed by a second `0 0` verification.

## Round 2 · Critic Findings

Round 2 confirmed the evidence schema, AC7 matrix, endpoint destinations and AC12 sequence, but returned `NEEDS_REVISION` for two remaining issues:

1. The latest PASS review needed a machine-verifiable binding to the current design and implementation rather than numeric ordering alone.
2. `authorized_by: user:*` alone could still be self-filled; an exception needed a stable sprint-local authorization record with matching fields.

## Round 2 · Design Revision (normative addendum)

### G. Review freshness binding

The final numeric review artifact must contain:

```text
Reviewed design sha256: <64 lowercase hex>
Reviewed implementation commit: <40 lowercase git commit>
```

- Ship recomputes SHA-256 of the authoritative current `design.md`; mismatch blocks.
- Ship verifies the reviewed implementation commit exists and is an ancestor of `HEAD`.
- Any path outside `.ai_state/**` changed after that commit blocks as unreviewed implementation drift. Subsequent review/polish/ship-receipt state changes may modify `.ai_state/**`; polish that changes packaged implementation requires a new review and new binding.
- `design_changed_after_impl=true`, a newer design mtime, missing/malformed bindings or a non-PASS latest review also block.
- Required negative tests: design content changed after review, implementation file changed after reviewed commit, malformed/missing commit and state-only post-review changes (allowed).

### H. User authorization record for a spec exception

The frontmatter exception must additionally include:

```yaml
spec_gate_exception_authorization_ref: "user-authorizations/<id>.yaml"
```

The referenced file is resolved under the current sprint and must exist with:

```yaml
schema_version: 1
kind: spec_gate_exception_authorization
sprint_slug: "<exact current sprint>"
path: "<exact Feature|Refactor|System>"
reason: "<exact exception reason>"
decision: approve
authorization_source: user_prompt
authorized_by: "user:<stable label>"
authorized_at: "<same UTC ISO-8601 as frontmatter>"
expiry: "<same UTC ISO-8601 as frontmatter>"
removal_condition: "<same observable condition>"
```

- The gate validates exact field equality, allowed values, timestamps and expiry. A `user:*` string without this record, mismatched data, placeholder values or an authorization record outside the current sprint fails closed.
- This record is governance evidence, not a cryptographic proof of human identity; Athena must not claim stronger provenance than the platform exposes.
- Feature/Refactor/System still cannot ship with an active exception, even when the authorization record is valid.

## Round 3 · Critic Findings

Round 3 accepted the authorization record but returned `NEEDS_REVISION` because review freshness still treated a successfully re-reviewed design as permanently dirty, and implementation drift did not explicitly cover staged, unstaged and untracked files.

## Round 3 · Design Revision (normative addendum)

### I. Re-review closure and complete implementation drift

- Current design SHA-256 matching the latest final PASS review is the authoritative proof that a changed design was re-reviewed.
- `design_changed_after_impl=true` blocks only while no final PASS review is bound to the current design hash. After passN PASS, the main agent sets it false and may record `design_rereviewed_by: reviews/passN.md` in `_index`; an old hash still blocks.
- Design mtime is only a trigger to recompute/compare the hash binding. It cannot independently reject a matching fresh review.
- Implementation freshness checks all non-`.ai_state/**` drift:
  1. committed changes from the reviewed implementation commit to `HEAD`;
  2. staged/index changes;
  3. tracked working-tree changes;
  4. untracked release/package files.
- Any such implementation drift blocks ship and requires a new review binding. State-only `.ai_state/**` review/polish/receipt changes remain allowed.
- Required tests: changed design + old review fails; changed design + fresh hash-bound PASS succeeds; committed, staged, unstaged and untracked implementation drift each fail; state-only post-review changes succeed.

## Round 4 · Critic Findings

The final configured critic round returned `NEEDS_REVISION` for four precision gaps: review-critical `.ai_state` drift, command evidence without captured exit/output/hash, undefined AC7 pointer/history bounds, and unverifiable test-first ordering.

## Round 4 · Design Revision (final normative addendum)

### J. Review-critical state manifest

Before the final 2+1 review, the main agent creates `review-manifest.yaml` containing SHA-256 hashes for:

- authoritative `design.md`;
- `checklist.yaml`, `evidence.yaml`, `runtime-verify.md`, `rework-notes.md`, `cleanup-pass.md`;
- `.ai_state/architecture/ARCHITECTURE.md` and `architecture/athena-9.9.2.md`;
- the implementation commit from section G.

The final review records `Reviewed state manifest sha256: <64hex>`. Ship recomputes the manifest and blocks any mismatch. Post-review mutable allowlist is limited to:

- `_index.md`: `stage`, `next_action`, `pointers.latest_review`, `pointers.latest_cleanup`, `active_worktrees`, bounded current-state append;
- subagent lifecycle/token/tool-trace append-only records for the final review/polish;
- `ship-receipt.md` after the first release push.

Any other reviewed-state change requires regenerating the manifest and a new final review.

### K. Command evidence capture

`source: command` evidence additionally requires:

```yaml
exit_code: 0
output_artifact: "evidence/<name>.txt"
artifact_sha256: "<64 lowercase hex>"
implementation_commit: "<40 lowercase git commit>"
```

The output artifact must exist and contain the exact command, exit code and observed counts/summary. Ship verifies its hash and that the implementation commit matches the final review binding. An asserted summary without the artifact, nonzero/unknown exit, stale commit or hash mismatch fails.

### L. Deterministic AC7 router fields and bounds

- Required `_index.pointers` keys: `latest_design`, `latest_review`, `latest_cleanup`, `latest_requirement`; values may be empty only when no artifact of that kind exists, otherwise they are `.ai_state`-relative paths to existing files.
- `latest_architecture_update` is an ISO-8601 timestamp, not a file pointer; `ARCHITECTURE.md` is the architecture entry.
- `route_history` is capped at 10 entries. The human-readable `## 当前状态` recovery log is capped at the 10 newest entries; detailed older history belongs in sprint/session logs and git.
- status/session-start must flag any nonempty missing pointer, path escaping `.ai_state`, malformed history or over-bound history. Tests cover valid routing, missing target, escaping path and 11-entry overflow.

### M. TDD red-to-green evidence

Behavioral rework batches require `tdd-evidence.yaml` records containing test file, failing command/output summary observed before implementation edit, implementation files, later green command/output summary and timestamps. Reviewer validates the red timestamp precedes implementation/green evidence. This is process evidence, not inferred from final green tests alone; missing red evidence is a review blocker for behavioral changes.

The four-round configured critic budget is now exhausted. The final pass3 reviewer/spec/evaluator must judge this final addendum and implementation together; no critic PASS is claimed.
