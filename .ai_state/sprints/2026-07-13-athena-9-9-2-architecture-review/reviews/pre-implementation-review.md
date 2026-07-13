# Pre-Implementation Review — Athena 9.9.2 overall architecture upgrade

> Reviewer: root Codex main thread.
> Scope: current untracked `vibeCoding/claude/9.9.2`, `vibeCoding/codex/9.9.2`, `vibeCoding/claude/9.9.2-DRAFT-architecture.md`, and the authoritative sprint `design.md`.
> Provenance note: formal Athena 2+1 review was attempted, but the native `SubagentStart` event was not persisted to the current sprint ledger. The reviewer was stopped before reading files, per fail-closed binding rules. This document is therefore an explicit main-thread implementation review, not a fabricated `pass1.md`.

## Verdict

**REWORK REQUIRED BEFORE IMPLEMENTATION CAN BE CALLED COMPLETE.**

The architecture direction is approved under the user-selected release name `9.9.2`. The current package is only an early partial implementation: route-source cleanup and some identity/plugin edits exist, while the defining structural work—four primitives, spec-gate, two-tier memory, 9.9.2 install/migration and 9.9.2 validation—remains missing or contradictory.

Fable5 may start implementation from the accompanying authoritative `design.md` and `fable5-implementation-brief.md`. It must not treat the current CHANGELOG claim “已验证” as evidence.

## Evidence collected

### Current change surface

- CC 9.9.1 → 9.9.2: 9 changed/deleted paths.
- CX 9.9.1 → 9.9.2: 6 changed paths.
- No `references/mcp.md` exists on either endpoint.
- No spec-gate code or tests exist in either delivery gate.
- Existing validators are named and hard-coded for 9.9.1.

### Syntax evidence

- JSON parsed: 2 files, 0 errors.
- TOML parsed: 14 files, 0 errors.
- Python AST parsed: 33 files, 0 errors.
- All packaged CC `.cjs` files passed `node --check`.

Syntax health is good but does not validate release behavior.

### Installer reproduction

Installing the 9.9.2 package into a temporary HOME with the packaged setup script produced:

```text
setup failed; rollback complete: post-install verification failed
CC: verify v9.9.1 ... drifted=1
drift: <temporary-home>/.claude/settings.json
exit=2
```

Root cause: packaged setup still declares `VERSION = "9.9.1"`, while copied settings correctly declare 9.9.2.

### Review orchestration reproduction

The current local Codex hooks register `SubagentStart`, and `subagent-tracker.py` claims support for the event. A native `spawn_agent` was started with a wait-for-BOUND instruction, but no current-sprint `subagent-events.jsonl` was created. The agent was stopped without reading files. This demonstrates that the lifecycle ledger contract is not proven on the current surfaced collaboration runtime.

## What is already good

1. **Dual-core framing is strong.** Treating PACE as control plane and `.ai_state` as durable data plane creates a clear separation between orchestration and truth.
2. **Route-source deduplication is correct.** Moving detailed deliberation thresholds to `athena-dev` and leaving `pace` as the state-machine/router overview reduces normative duplication.
3. **Stage naming is clearer.** “4 core + 5 conditional” explains actual usage without deleting the nine-stage vocabulary.
4. **feature-dev default was corrected.** Disabling its complete workflow avoids a second plan/impl authority.
5. **ECC-AgentShield is enabled.** This preserves the automated security capability while keeping it outside the core gate dependency.
6. **Dead unregistered permission-retry code was removed.** No registration reference was found in the 9.9.1 settings baseline.

## Findings

### P0-1 — 9.9.2 cannot be installed

Both packaged setup scripts still use `VERSION = "9.9.1"`. Fresh installation copies 9.9.2 assets, then verifies them against 9.9.1 and rolls back.

Required fix:

- add a 9.9.2 setup implementation or parameterize the installer safely;
- update package discovery, help text, verification markers and tests;
- prove fresh CC-only, CX-only and both-endpoint installs;
- prove a second same-version run is read-only and succeeds.

### P0-2 — Existing 9.9.1 users have no supported upgrade path

Setup is intentionally fresh-only. The packaged migrate skill and script still implement only `9.9.0 → 9.9.1`. Therefore a valid 9.9.1 installation can neither be set up nor migrated to 9.9.2.

Required fix:

- implement a transactional `9.9.1 → 9.9.2` migration;
- preserve the existing user-owned configuration guarantees;
- retain historical migration only as an explicitly historical/staged path;
- add rollback injection and idempotence tests.

### P0-3 — The defining 9.9.2 architecture is not implemented

The current package does not contain:

- four-primitive entry-prompt/reference updates;
- `references/mcp.md` on either endpoint;
- spec-gate logic or fixtures;
- two-tier-memory template/init/checkpoint/status changes;
- actual plugin/MCP R4 arbitration updates.

The CHANGELOG accurately lists these under “待落地”, but its header simultaneously calls the release a complete, verified structural upgrade. The package must remain DRAFT until the structural items and evidence exist.

### P0-4 — Formal review lifecycle evidence is currently not trustworthy

The review binding handshake could not observe a raw `SubagentStart` event despite the hook being registered. Because 9.9.2 continues to make lifecycle evidence a fail-closed delivery dependency, this must be resolved or explicitly adapted to the currently surfaced collaboration runtime.

Required fix:

- add a real integration probe for native collaboration start/stop events;
- distinguish “tool exists” from “hook event is delivered” in platform detection;
- ensure the tracker resolves the current sprint and persists schema-v1 events;
- test missing `agent_type`, missing `agent_id`, worktree execution and main-repo redirection;
- keep fail-closed assignment binding; do not guess IDs or backfill fake ledger entries.

### P1-1 — Spec-gate timing is contradictory

The draft architecture specifies Feature+ gating before `impl`; the CHANGELOG describes a ship-time gate. A ship-only check cannot prevent intent drift during implementation.

Required decision, now frozen in authoritative design:

- primary gate: transition into impl;
- defense-in-depth recheck: ship;
- validate semantic acceptance criteria, not file existence only.

### P1-2 — MCP has duplicate architectural ownership

The draft draws MCP in the outer capability layer and again as a middle-layer primitive without explaining conceptual versus deployment placement. It also mixes Workflow, actors, reusable instructions and integration protocol at one abstraction level.

Approved correction:

- keep four primitives as the user-selected Athena execution vocabulary;
- define MCP's primitive role as “reach/external action”;
- define MCP servers/plugins as capability-layer implementations of that role;
- state explicitly that PACE is the concrete Workflow authority and `.ai_state` is not a fifth primitive.

### P1-3 — Two-tier memory is described but has no executable contract

The current draft names RAM/disk tiers but does not define persistence events, field ownership, index consumers or stale-context recovery.

Required fix:

- document Tier 1/Tier 2 ownership;
- define `_index.md` as a bounded retrieval router rather than a duplicated database;
- identify a consumer for every retained field;
- update init/checkpoint/session-start/status/template behavior;
- add compaction/handoff recovery tests.

### P1-4 — Active project-state templates still identify 9.9.1

Both packaged `_index.md` templates declare version/schema 9.9.1. Athena status headings and init completion messages also retain old active identities. A new 9.9.2 project would start in immediate version drift even after setup is repaired.

Required fix:

- update active templates and commands to 9.9.2;
- retain historical version references only where they describe history;
- add a validator that classifies active versus historical version references.

### P1-5 — Plugin documentation contradicts packaged defaults

The draft says feature-dev is on and ECC-AgentShield is off; actual settings have feature-dev off and ECC-AgentShield on. `plugins.md` still routes brainstorm through superpowers even though the packaged default disables it and has not incorporated R4 MCP arbitration.

Required fix:

- choose package settings as the release source of truth;
- refresh both endpoint references;
- document enabled, disabled and fallback behavior explicitly;
- add a settings-to-document consistency test.

### P1-6 — 9.9.2 has no dedicated release harness

`validate-athena-9.9.1.py`, `test-athena-9.9.1-runtime.py` and `test-athena-claude-9.9.1-runtime.cjs` all target the previous package roots. RELEASE commands in the 9.9.2 directory also invoke 9.9.1 suites.

Required fix:

- create a 9.9.2 validator or parameterize the existing validator with explicit release roots/version;
- ensure the validator fails if pointed at 9.9.2 before implementation;
- cover the new structural behavior, not only syntax and string identity;
- never report 9.9.1 totals as 9.9.2 evidence.

### P1-7 — The 9.9.2 `.ai_state` history was missing

Before this review sprint, `_index.md` still pointed to the completed 9.9.1 ship sprint, and there was no route/design/checklist/review record for the 9.9.2 architecture. The untracked draft alone did not satisfy “document is truth”.

This sprint begins correcting that gap. Fable5 must continue using this sprint or create a clearly linked implementation sprint; it must not leave implementation state only in conversation or package CHANGELOG.

### P2-1 — Version cleanup claims are broader than the edits

The package changes sample output versions but leaves headings such as `athena-status v9.6.4/v9.7.0`, PACE titles marked v9.9.1 and multiple active initialization messages at 9.9.1. Some historical labels are legitimate; active labels are not.

Required fix: define an allowlist for historical references and make all other drift fail validation.

### P2-2 — Trend claims are stronger than their evidence

Claims such as “89%”, “2026 头号失败模式”, “4–7x token” and “3–5 并发甜点” are not necessary to justify the architecture and are sourced from secondary/marketing material rather than platform contracts.

Required fix:

- remove precise quantitative claims unless the primary source and methodology are captured;
- ground product behavior in official Codex/Claude/MCP documentation;
- present broader industry framing as motivation, not an architectural dependency.

## Spec compliance against the authoritative design

| Requirement | Current state | Classification |
|---|---|---|
| User-approved release name 9.9.2 | Package roots/entry identity partly updated | PARTIAL |
| Dual core | Drafted, not consistently wired into references/templates | PARTIAL |
| Four primitives | Not implemented | MISSING |
| MCP reference/arbitration | No `references/mcp.md` | MISSING |
| Impl-entry spec-gate | No gate code/tests | MISSING |
| Ship spec/evidence recheck | Existing gate does not implement new contract | MISSING |
| Two-tier memory | Draft prose only | MISSING |
| Route source single ownership | Main duplicate block removed from pace | SATISFIED WITH DRIFT |
| Actual plugin defaults documented | Draft/reference conflict with settings | DEVIATED |
| Fresh 9.9.2 install | Reproduced failure | FAIL |
| 9.9.1 → 9.9.2 migrate | No path | MISSING |
| 9.9.2 validation | No targeting harness | MISSING |
| Formal 2+1 review evidence | Binding event absent | BLOCKED |

## Required implementation order

1. Create/parameterize RED 9.9.2 validator and fixtures.
2. Fix active release identity, templates and setup; prove fresh/same-version behavior.
3. Implement transactional 9.9.1 → 9.9.2 migration.
4. Normalize four-primitives terminology and add MCP references.
5. Implement spec-gate tests, then CC/CX gates and stage wiring.
6. Implement two-tier-memory contracts across templates/init/checkpoint/session-start/status.
7. Refresh plugin/MCP arbitration and consistency checks.
8. Run syntax, unit, migration, runtime and temporary-HOME matrices.
9. Produce runtime-verify evidence.
10. Run formal reviewer + spec-compliance + evaluator after lifecycle tracking is proven.
11. Polish, update architecture/current-state records, then ship.

## Release gate

Fable5 implementation is acceptable for formal review only when:

- all AC1–AC12 in `design.md` have evidence;
- fresh install and 9.9.1 migration pass on both endpoints;
- spec-gate has behavioral tests for normal, boundary and failure cases;
- lifecycle binding works without guessed or manually invented events;
- no P0/P1 finding above remains open;
- the current sprint/checklist/evidence point to actual 9.9.2 outputs.

## Official sources

- Codex customization: https://developers.openai.com/codex/concepts/customization
- Codex configuration: https://developers.openai.com/codex/config-reference
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents

