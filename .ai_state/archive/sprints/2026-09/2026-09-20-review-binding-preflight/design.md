---
sprint_slug: "2026-09-20-review-binding-preflight"
path: "System"
stage: "design"
author: "cc-main (revised after design review 208cfc50 REWORK)"
base_commit: "0ca066c"
---

# Review binding preflight

## WHY

The review binding CLI is the only supported way to dispatch and accept an independent review. The failure modes below each cost a round, and the first three were hit live in this project.

**The ledger it writes can be one of the inputs it hashes.** `prepare` computes `input_manifest_sha256` over `input_paths` in `liveInput` (`_review-binding.cjs:120`), then `append` writes the `athena-review` marker into `session-log.md` (`:44-51`). Declare the session log as an input and the hash is stale the instant prepare returns. The same hole exists for two more paths the four steps write: `.ai_state/_index.md` (`:156` in bind, `:182-186` in accept) and the previous round's `reviews/<mode>-review.md` (`:170,179`). The review-doc case is the nastiest: accept writes *after* its own `assertLive`, so prepare, bind and accept all pass and the failure only lands at ship, where `validateCurrent` re-runs `assertLive` (`:189-192`, called from `delivery-gate.cjs:381`). `reviews/_native/*.json` needs no handling — it does not exist at prepare, so `fileRefs` (`:61-62`) throws on it before the containment check, which is already fail-closed.

**Drift is reported by field name only.** `assertLive` (`:85-89`) throws `review input changed: packet_sha256` with no path, no expected value, no live value; for `evidence_ids` it does not even name the missing id. With several documents bound, locating the culprit means reading hook source. That happened twice in one session here.

**Manifest staleness surfaces at ship, far from its cause.** `accept` freezes `prepared.base_commit` as `Reviewed implementation commit` (`:177`); `validateReviewBinding` later demands it equal the manifest's `implementation_commit` (`delivery-gate.cjs:540-542`). Nothing in prepare, bind or accept ever reads that field. A manifest left at an older commit passes all four steps and blocks only at ship, naming neither side as stale. Note the manifest *bytes* are already bound as an `evidence_doc` (`:116` + `:87`), so post-prepare tampering is already caught; the unchecked thing is specifically the commit value against HEAD.

**The governance hash has no CLI on CC.** `indexGovernanceSha256` (`delivery-gate.cjs:508-512`) hashes nine protected `_index` fields in sorted order with a specific string coercion, and is absent from `module.exports` (`:1434`). Writing a `review-manifest.yaml` therefore means reimplementing the algorithm by hand — which is exactly how a wrong hash definition wasted a review round in this project. CX differs: `_review_binding.py:25-28` loads `delivery-gate.py` by path and every module-level name is reachable, so CX lacks a CLI verb, not access.

**Pi's copy is stale and would break ship.** `pi-agent/plugin/extensions/cc-core/_review-binding.cjs` predates the binding-line dedup (commit `4894588`): it has no strip at all, so a reviewer who supplies `Reviewed …` lines gets them duplicated, and `delivery-gate.cjs:525-527` blocks on the exactly-one rule. This is a live latent defect, not a cosmetic drift.

## HOW

### Self-exclusion over operator discipline

`prepare` removes every path the four steps write from `input_paths` before hashing: the sprint `session-log.md`, `reviews/<mode>-review.md` for the mode being prepared, and `.ai_state/_index.md`. Exclusion applies to the **stored** `input_paths`, not only to the hash input, because `liveInput` re-reads `prepared.input_paths` at bind, accept and ship (`:75`); storing the unfiltered list would reproduce the bug one step later. The removed entries are recorded in the prepared row as `excluded_inputs` so the omission is auditable rather than invisible. If exclusion would empty the input set, prepare fails rather than binding nothing.

The operator cannot be expected to know which files the CLI writes. The CLI already knows.

### Drift diagnostics, split by what the data can support

Two distinct cases, because they have different evidence available:

- **Declared input paths.** `prepare` persists `input_hashes` alongside the folded `input_manifest_sha256`. `input_hashes` stores the **entire** `inputs` map that `liveInput` builds at `:75-77` — every declared path *and* the snapshot axes — because the aggregate case below needs expected values that are otherwise discarded at `:79`. `assertLive` recomputes and reports only the entries that differ, each with path, expected and live hash. A prepared row written before this change has no `input_hashes`; that case keeps today's field-name-only message plus an explicit note that per-entry attribution is unavailable for rows prepared by an older CLI. `assertLive` already holds the row, so the fallback is a presence check.
- **Aggregate axes.** `packet_sha256`, `design_sha256`, `source_sha256` and `environment_sha256` are whole-tree or canonicalised digests (`_input-binding.cjs:40-58`, `:59-76`) with no per-file decomposition. For these the message names the axis, both hashes, and the recovery action. It does not claim to name a file, because it cannot.
- **Per-entry maps that already exist.** `evidence_docs` (`:87`) and `evidence_ids` (`:88-89`) carry per-entry data today yet still throw a bare field name; `evidence_docs` is the likeliest real drift, since `review-manifest.yaml` is one of its members (`:116`) and is edited during ship preparation. Both report the specific differing document or the specific missing id. This is a filter over data already in hand, not new persistence.

Every message ends with the concrete next action: re-run `prepare` for a new run, or restore the input. Drift still fails closed in every case; this slice makes the failure legible, not tolerable.

### Manifest preflight, narrow by design

When mode is `implementation` and `review-manifest.yaml` exists, `prepare` scans it for a root-level `implementation_commit` line carrying a 40-hex value and compares it against the HEAD it is about to record.

- Present and different from HEAD → fail, printing both values and stating which is stale.
- Absent, or not 40-hex → **skip the preflight**. Prepare must not newly hard-fail a manifest that is legitimately incomplete mid-sprint; the existing fixture at `test_state_review.py:579` writes `schema_version: 1` alone and prepare accepts it today. The gate still validates the manifest in full at ship.

The check deliberately does not use the gate's `parseReviewManifest` (`delivery-gate.cjs:464-499`): that is a whole-file validator which also needs a `pathType` prepare does not have (`input.context` reads only `current_sprint_slug`). A narrow single-field scan is not the drift hazard a second full parser would be.

Prepare-time is the only safe point, and it is sufficient. `accept` freezes `prepared.base_commit`, so comparing against HEAD at prepare compares against exactly the value accept writes and the gate demands. The preflight adds no runtime `base_commit` comparison, so the deliberate tolerance at `:84` — ship bookkeeping commits moving HEAD after prepare must not void a review — is untouched.

The manifest is never rewritten. It is a human-authored declaration, and silently correcting it would destroy the evidence that the review was prepared against different code.

### `governance` subcommand

`review-binding governance --cwd <dir>` prints the governance hash plus the field/value pairs it covers, and writes nothing. It branches before the `--run` requirement in the option chain (`:214`, `:219`).

**It must resolve `_index.md` by the gate's rule, not the CLI's.** Every existing verb goes through `input.context`, which uses `git rev-parse --show-toplevel` (`_input-binding.cjs:34`) — inside a linked worktree that is the worktree root. The consumer of this hash resolves through `tryRepoRoot` → `--git-common-dir` (`delivery-gate.cjs:444-446`) plus `findAiState`, i.e. the main repository. Measured in this project's own worktree, the two resolve to different directories and their two `.ai_state/_index.md` files already differ, so using `input.context` would print a hash for a file the gate never reads — precisely the wrong-hash round this verb exists to prevent. The verb therefore uses the gate's resolution and the gate's already-exported `parseFrontmatter`, and requires no active sprint, since the governance hash is a pure function of `_index.md` frontmatter and `input.context` would otherwise throw `current sprint unavailable` (`_input-binding.cjs:37`).

It computes nothing itself. On CC it imports `indexGovernanceSha256` and `INDEX_GOVERNANCE_FIELDS` from the gate, which requires adding those two names to `module.exports` — the one permitted gate edit, scoped by AC5. On CX it calls the already-reachable `index_governance_sha256`. Each side prints using its own gate's coercion, which differ in source (`delivery-gate.cjs:510` uses `String(fm[key] || "")`, `delivery-gate.py:1142` uses `fm.get(key, "")`); the test diffs the two outputs rather than assuming they agree.

Reimplementing the hash instead of importing it would recreate exactly the drift this subcommand exists to eliminate.

### Scope boundaries

`accept`'s removal of reviewer-supplied `Reviewed …` lines (`:176`) is **left alone**. It is a deliberate dedup that guarantees the gate's exactly-one rule (`delivery-gate.cjs:525-527`) and is covered by `test_accept_deduplicates_reviewed_binding_lines` (`test_state_review.py:576-590`). An earlier draft of this design called it a defect; that was wrong.

`delivery-gate` logic is unchanged on every platform. The only permitted diff is the two-name `module.exports` addition on CC and on Pi's `cc-core` copy.

## Acceptance Criteria

- [ ] AC1: Declaring `session-log.md`, `reviews/<mode>-review.md` or `.ai_state/_index.md` as inputs to `prepare` no longer breaks the binding. Prepare succeeds, the stored `input_paths` no longer contains them, `excluded_inputs` records them, and a subsequent `bind`, `accept` and ship-time `validateCurrent` all succeed on unchanged inputs across CC and CX. Paths are matched after resolution, so a `./` prefix does not slip through. A prepare that declared inputs and has none left after exclusion fails; a prepare that declared none in the first place stays legal, as the existing suite relies on it.
- [ ] AC2: A drifted declared input path is reported with its path, expected hash and live hash, listing only entries that actually differ; a drifted aggregate axis is reported with the axis name and both hashes and makes no per-file claim; a drifted `evidence_docs` entry names the specific document and a missing `evidence_ids` entry names the specific id; a row prepared without `input_hashes` degrades to the field-name message with an explicit note. Every message states the recovery action, and every drift that blocked before still blocks.
- [ ] AC3: With `implementation_commit` present, 40-hex and different from HEAD, `prepare --mode implementation` fails naming both values and which is stale, and `review-manifest.yaml` is byte-identical afterwards. With that field absent or malformed, prepare succeeds exactly as today.
- [ ] AC4: `review-binding governance --cwd <dir>` prints the governance hash and its covered field/value pairs on both platforms, equal to the respective gate's own computation, with the two platforms' outputs diffed and equal in the test. Run from inside a linked worktree whose `.ai_state/_index.md` differs from the main repository's, it reports the hash of the file the gate reads, not the worktree copy. It succeeds with no active sprint, writes no file, and exits non-zero when `_index.md` is absent.
- [ ] AC5: `delivery-gate.{cjs,py}` differ from base commit `0ca066c` by nothing except adding `indexGovernanceSha256` and `INDEX_GOVERNANCE_FIELDS` to the CC and Pi `module.exports` lines, asserted line by line. That assertion is sprint-scoped: it pins this slice's blast radius, and slice 5 removes it when it begins editing the gate for real. `_review_binding.py` matches `_review-binding.cjs` behaviour across AC1-AC4; and Pi's `cc-core/_review-binding.cjs` becomes byte-identical to the CC original, repairing the missing dedup that would otherwise duplicate binding lines and block ship.

## File Structure Plan

- `vibeCoding/claude/9.9.9/.claude/hooks/_review-binding.cjs`: self-exclusion, `input_hashes`, drift diagnostics, manifest preflight, `governance` verb.
- `vibeCoding/codex/9.9.9/.codex/hooks/_review_binding.py`: Python equivalents.
- `vibeCoding/claude/9.9.9/.claude/hooks/delivery-gate.cjs`: add two names to `module.exports`; no other line changes.
- `vibeCoding/pi-agent/plugin/extensions/cc-core/_review-binding.cjs`: re-sync to byte-identical with CC (repairs the stale pre-dedup copy).
- `vibeCoding/pi-agent/plugin/extensions/cc-core/delivery-gate.cjs`: same two-name export addition.
- CC, CX and Pi `skills/pace/references/gate-contracts.md`: document the `governance` verb and the manifest preflight in the review-binding four-step section.
- `vibeCoding/scripts/tests/athena999/test_state_review.py`: behavioural coverage for AC1-AC5.
- `.ai_state/architecture/ARCHITECTURE.md`: review binding contract update at polish.

## Non-goals

- No change to `delivery-gate` logic anywhere; AC5 pins the permitted diff to two export names. Slices 5 and 6 own that file next and inherit the addition; the line-by-line assertion is theirs to retire.
- No change to `accept`'s binding-line dedup, which is correct and regression-tested.
- No new hash algorithm, and no change to what the governance hash covers.
- No automatic repair of a stale manifest or of drifted inputs. Both fail closed and stay the operator's decision.
- No change to the four-step prepare/dispatch/bind/accept order, and no second task store.
- No installation into `~/.claude` or `~/.codex` from inside this slice; the user authorized a separate sync step after ship.
