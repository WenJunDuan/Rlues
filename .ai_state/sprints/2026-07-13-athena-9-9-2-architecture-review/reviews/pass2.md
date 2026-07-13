# Review Pass 2 — Athena 9.9.2 post-rework release audit

Date: 2026-07-13
Path: System
Review mode: native 2 + 1; reviewer and spec-compliance results merged before evaluator.

## Scope and provenance

- Contract: `design.md` AC1–AC13 and non-goals.
- Baseline: `origin/main` / `1a4dfd1`; implementation commit `d578c4e` plus current sprint runtime/evidence/architecture updates.
- reviewer: `019f5ac8-5f52-7011-a507-7fc5aabc2591`, read-only, schema-v1 Start → assignment → BOUND → Stop.
- spec-compliance: `019f5aca-3af7-7393-8b53-61d0ee606e84`, read-only, schema-v1 Start → assignment → BOUND → Stop.
- Host evidence supplied to both roles: Python 3.14.3; validator 169/0/0; CX runtime 41/41; CC runtime 85/0/0.

## Reviewer Findings

### P0 — Release blockers

#### P0-1 — AC6 evidence mapping remains fail-open

`validate_ac_mapping` only checks whether an `ACn` token appears anywhere in `checklist.yaml` or `evidence.yaml`; it does not require that the matching evidence record has `result: pass`. `validate_evidence` permits unknown records when one unrelated record passes.

The current sprint demonstrates the bypass: AC7, AC11 and AC12 are mapped to `result: unknown`, while the validator record supplies the unrelated global pass. The CX implementation searches labels in `delivery-gate.py` around `validate_ac_mapping`; CC has the same label-only behavior in `delivery-gate.cjs`.

Required: each labeled AC must map to explicit passing evidence or an accepted review result. Add negative tests proving `unknown` or checklist-only mentions cannot satisfy an AC.

#### P0-2 — P1-3 / AC7 is still explicitly incomplete

`rework-notes.md` records two-tier memory as only “部分 / 深化待续”, and current evidence leaves AC7 unknown. Explicit Tier1/Tier2 semantics exist in the `_index` template, but the required consumer surfaces remain inconsistent:

- CC/CX init retain stale 9.9.1/v9.6.4 identities and examples.
- Both init skills populate nonexistent `cx_goal_default_on` instead of the current template field.
- CC init contains an invalid `cat > .ai_state/compound/` directory target.
- status/checkpoint/session-start do not consistently state the retrieval-router and working-versus-persistent memory contract.
- No validator/runtime test covers the required AC7 consumer matrix.

Required: finish AC7 across template, init, checkpoint, session-start and status on both endpoints, and add focused contract tests.

#### P0-3 — The current sprint is guaranteed to fail its own System ship gate

Both delivery gates require at least two `Critic Findings` occurrences for System when critique is enabled. `design.md` contains zero such headings, while `_index.plan_critique_disabled=false` and `plan_critique_min_rounds=0` select the System default of two.

Required: reconcile/document the real critique rounds inside authoritative `design.md` before the final review. Any post-review design update requires another review.

### P1 — Must fix before another review

#### P1-1 — Pass1 P1-5 release documentation was not fixed

- CX `RELEASE.md` presents Claude Code 2.1.203/2.1.206 as Codex compatibility versions.
- It invokes a Python runtime file with `node`.
- It reports stale 83/0/2, 73/0/0 and 33/33 results rather than 169/0/0, 41/41 and 85/0/0.
- Both CHANGELOGs still say Python 3.11 validation is pending.
- Both RELEASE files still say the formal 2+1 review is pending.

#### P1-2 — AI migration guide gives an incorrect CX fresh-install destination

The guide says to copy the CX `.codex` package into `~/.agents`. The actual contract installs CX config/hooks/agents under `~/.codex`; only skills belong under `~/.agents/skills`. All four byte-identical guide copies inherit the defect.

#### P1-3 — Spec-gate exception authorization and ship behavior remain under-constrained

`spec_gate_exception_authorized_by` accepts arbitrary non-empty text. An active exception returns an empty criteria list, so ship skips AC mapping. The executable gate does not require the non-emergency exception to surface as a review concern or be cleared before ship as required by design §4.5.

#### P1-4 — Active workflow documentation still contradicts PASS-only shipping

CX `pace/references/stages.md` still routes CONCERNS toward polish/ship while the executable delivery gate requires final PASS. Some CHANGELOG wording still describes prompt-entry/ship-only spec-gate behavior after the machine impl-entry rework.

### P2 — Quality and evidence clarity

- The three runtime commands are genuinely green, but the validator has no AC7 consumer tests and no negative test for unknown evidence satisfying an AC.
- `tool-trace.jsonl` records validation calls as unknown/exit null; manual-observation fallback evidence should explicitly include observer, exit code and output summary.
- `_index.pointers.latest_cleanup` still points to the 9.9.1 sprint; System polish must refresh it after a successful final review.

### Reviewer recommendation

**REWORK.** The host matrix closes P1-2’s execution uncertainty and the provider, Chinese-heading and quantum regressions appear fixed. It does not close AC6, AC7, current ship-gate viability or release-document correctness. Do not push `main` yet.

## Spec Compliance

**Overall: 9 SATISFIED / 2 DEVIATED / 2 MISSING. Pass2 cannot reach spec PASS as-is.**

| AC | Result | Evidence summary |
|---|---|---|
| AC1 — active 9.9.2 identity | **DEVIATED** | Core package/setup/template/validator markers are 9.9.2, but init/status/live-index/release docs retain stale identities, commands and evidence. |
| AC2 — fresh and same-version setup | **SATISFIED** | Host validator 169/0/0 includes fresh temp-HOME setup, same-version verification, strict Codex doctor and prompt-input. |
| AC3 — AI-guided migration | **SATISFIED** | Four guide copies are byte-identical; setup/migrate route correctly and document backup, preservation, rollback and no-secret red lines. The CX destination wording remains a release-doc defect. |
| AC4 — four primitives | **SATISFIED** | CC/CX entry prompts and MCP references consistently define Workflow, SubAgent, Skill and MCP ownership. |
| AC5 — impl-entry spec-gate | **SATISFIED** | Both executable gates enforce Feature+ criteria at impl with positive/negative runtime coverage. |
| AC6 — ship spec/evidence revalidation | **SATISFIED with reviewer blocker** | Spec role confirmed the intended ship recheck exists; reviewer found its label-only evidence mapping is fail-open and must be fixed before release. |
| AC7 — two-tier memory | **DEVIATED** | Tier semantics mainly exist in templates; init/checkpoint/session-start/status/live index and tests do not consistently implement the full contract. |
| AC8 — single route source | **SATISFIED** | `athena-dev` owns thresholds and validator drift checks prevent duplication in pace. |
| AC9 — plugin/MCP arbitration | **SATISFIED** | Five arbitration/degradation rules match endpoint defaults. |
| AC10 — zero-failure package/runtime validation | **SATISFIED** | Validator 169/0/0; CX 41/41; CC 85/0/0. |
| AC11 — formal 2+1 PASS | **MISSING** | Pass2 has material blockers and cannot be PASS. |
| AC12 — complete release-state evidence | **MISSING** | Final review/ship evidence is absent, pointers are stale and critic-round gate cannot pass. |
| AC13 — quantum 7→2 | **SATISFIED** | Both hubs, CX registration, migration removal and relocated regressions are complete. |

### Non-goals and EXTRA

No unapproved EXTRA remains. Quantum 7→2 is reconciled by design §13/AC13. No violation was found in user-config preservation, optional external capability boundaries, platform asymmetry or the user-approved 9.9.2 name.

## Evidence Cross-Check

### Reconciled evidence

- Host runtime verification is green and closes the Python 3.11+ uncertainty: Python 3.14.3, validator 169/0/0, CX runtime 41/41, CC runtime 85/0/0.
- Reviewer/spec lifecycle provenance is valid: distinct schema-v1 Start → assignment → Stop records, with both results merged before evaluator.
- Checklist completion is not acceptance completion: I5 is completed while rework/evidence say AC7 is partial/unknown; I7 is completed while release docs and AC11/AC12 remain pending.
- The observed host outputs support runtime PASS, but the hook trace records those Bash calls as unknown/exit null. Evidence should explicitly record manual observer, exit code and output summary rather than appear hook-confirmed.

### Reviewer/spec contradiction resolution

- **AC6 resolves to DEVIATED.** Both gates perform label-only AC mapping; `validate_evidence` requires one global pass while allowing other AC records to remain unknown. Per-criterion passing evidence is therefore not enforced.
- **AC7 remains DEVIATED.** Consumer surfaces and focused tests are incomplete.
- **AC1 remains DEVIATED.** Active init/status/release/changelog surfaces retain stale identities, commands or pending results.
- Reconciled result: **8 SATISFIED / 3 DEVIATED / 2 MISSING**; AC11 and AC12 are missing.

### Ship-gate readiness

The release is not ship-ready:

1. `design.md` has zero `Critic Findings`; System requires two.
2. AC6 evidence mapping is fail-open for unknown/checklist-only mappings.
3. AC7 is incomplete despite checklist I5 being completed.
4. Release/migration docs contain stale or incorrect commands, results and CX destination wording.
5. Exception authorization/ship behavior is under-constrained.
6. State pointers still reference pass1/9.9.1 cleanup.
7. System polish must occur after a successful final review.

VERDICT: REWORK

## next_action

`rework_impl`

Required before pass3:

1. Require explicit passing evidence or an accepted review result for every labeled AC; add unknown/checklist-only negative tests.
2. Complete AC7 across both endpoints and add consumer-matrix tests.
3. Add real critic-round records to `design.md`, then run a fresh 2+1 because design changes after pass2.
4. Correct RELEASE/CHANGELOG, migration-guide copies, CX workflow wording and exception behavior.
5. Refresh evidence provenance, rerun host suites, execute pass3, then polish/delivery-gate. Do not push until final PASS.
