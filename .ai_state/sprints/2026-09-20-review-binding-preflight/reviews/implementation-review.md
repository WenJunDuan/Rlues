---
schema_version: 1
mode: "implementation"
review_run_id: "cdfb7313-3b66-4914-a1a3-9d81353dc08f"
reviewer_target: "ad2b07493d2c787aa"
packet_sha256: "ecf568bb53e225169bb87b6e86f928e95e7f98d512fc3429f6f91b93b35b8b0c"
input_manifest_sha256: "75b178243a9a1a4d636aa34656ba8e4b7d23dbd5ca72f3c47c437c397178de43"
native_output_ref: "reviews/_native/cdfb7313-3b66-4914-a1a3-9d81353dc08f-result.json"
verdict: "PASS"
---

## Native review output

---
schema_version: 1
mode: implementation
packet_sha256: "ecf568bb53e225169bb87b6e86f928e95e7f98d512fc3429f6f91b93b35b8b0c"
reviewed_diff_sha256: "96947974df4ed69211d667ef16faf19f141392fc2b09f4448cb979fa3073107f"
review_run_id: "cdfb7313-3b66-4914-a1a3-9d81353dc08f"
native_output_ref: "reviews/_native/cdfb7313-3b66-4914-a1a3-9d81353dc08f-result.json"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 5}
dimensions: [spec, correctness, security, tests, overengineering, evidence]
---

# Implementation Review — 2026-09-20-review-binding-preflight

Packet hash recomputed and matches. Diff hash from the gate's own `sourceDiffSha256`: `96947974df4ed69211d667ef16faf19f141392fc2b09f4448cb979fa3073107f`.

## Spec coverage

AC1-AC5 all present. No MISSING.

**AC1 verified.** `partitionInputs` (`_review-binding.cjs:83`) excludes exactly the three paths the CLI writes. Cross-checked the write set against the actual writes: `:50` session-log, `:219`/`:245` `_index.md`, `:242` `reviews/<mode>-review.md` where `doc` at `:233` is mode-derived, so the exclusion list matches the mode-derived name rather than a hardcoded one. `reviews/_native/<run>-<kind>.json` (`:207`) is genuinely unreachable at prepare because the filename embeds the not-yet-issued run id. Exclusion is applied to `kept` which becomes the stored `input_paths` (`:180`), which is what `liveInput` re-reads at bind/accept/ship — the correct fix, not the hash-only one. Zero-input prepare stays legal: the guard is `if (inputs.length && !kept.length)`.

**AC2 verified.** `input_hashes` persists the entire `inputs` map (`:95`), which for implementation mode is declared paths plus `Object.assign(inputs, input.snapshot(root,sprint))`, so all three snapshot axes are present and AC2's aggregate clause can name the axis. `input.canonical` recurses and sorts keys, so the nested object serialises deterministically into the session-log row.

**AC3 verified.** `manifestCommit` (`:150`) reads only, is root-level-scoped, returns empty for absent/non-40-hex, and prepare only throws when recorded differs from head. No write path touches the manifest.

**AC4 — DEVIATED (accepted).** The AC reads "importing the gate's own function and its `_index.md` resolution rule". The hash function is imported on both ends; the resolution rule is imported on CX (`_review_binding.py:366-369` calls `gate.git_root` / `gate.find_ai_state`) but re-implemented on CC (`:275`, `:284`). Rated P2, not a spec failure, because AC5 forbids the third and fourth export names an import would need.

**AC5 verified independently.** `git diff 0ca066c` on both `delivery-gate.cjs` copies is exactly one line each, adding exactly the two names. `delivery-gate.py` has no diff at all. CC and Pi `_review-binding.cjs` are byte-identical. Diffing the Pi base against the CC base confirmed the Pi copy really was the stale pre-dedup variant, missing both the `let` binding and the dedup, so the re-sync is a defect repair as claimed.

**EXTRA, accepted.** The three `gate-contracts.md` clauses go beyond the design's File Structure Plan by also documenting prepare's self-exclusion. This is correct: AC1 introduces two operator-visible behaviours that a contract-only reader could not otherwise predict. All three clauses verified accurate against shipped behaviour, including the mode restriction and both skip claims.

## The referred judgement call — re-derived, not accepted

Compared the copy line by line against the originals rather than trusting `cleanup-pass.md`.

`gateRepoRoot` vs `delivery-gate.cjs:434` `tryRepoRoot`: same probe, same basename test, same dirname result, same fallback, same non-throwing options down to the timeout and stdio. Sole difference is empty-string versus null, both falsy and only consumed as a truth value.

`gateAiState` vs `delivery-gate.cjs:28` `findAiState`: same depth bound, same directory test, same parent walk with the same break — and it does carry the 2026-09-07 `.git`-boundary stop, the line easiest to drop. Only addition is an empty-start guard, load-bearing because `gateRepoRoot` can return empty and resolving null would throw.

Composition is equivalent given that the helper returns empty for an empty start.

Empirically confirmed: CC `governance`, CX `governance` and the gate's own `indexGovernanceSha256` all return `c092c4881d38bf1227fa0a36ac42d4758db9d701a4d1b3b4083cd70a5f051f78`, byte-identical JSON across both platforms.

**Verdict on the call: the copy is faithful, and I accept it for this slice, but the duplication remains a defect on principle** — recorded as P2-1 rather than P1 because it is bounded, documented with resync line numbers, forced by a constraint that is itself a blast-radius guard, and asymmetric only because CX could import while CC could not. The irony is real but does not reach the slice's premise: the authoritative governance hash algorithm is imported on both ends, which is what "do not re-implement" was protecting.

## Correctness

No P0/P1. Specifically checked whether anything became more permissive than `0ca066c`:

- `packet_sha256`: condition unchanged, message only.
- `input_manifest_sha256`: condition unchanged; legacy rows without `input_hashes` still throw, with an explicit degradation message.
- `evidence_docs`: old code compared canonical forms of the two maps; new code uses `mapDiffs`, reporting only keys whose values differ. Equivalent **only** because `fileRefs` throws on a missing file rather than returning empty, and because prepared and live are computed over the identical key set. Traced specifically because this is the classic place such a rewrite goes fail-open; it does not.
- `evidence_ids`: a literal transliteration.
- `accept` is untouched by the diff, so the dedup is byte-identical and the gate's exactly-one rule remains guaranteed.
- `partitionInputs` runs before `fileRefs`, so excluded paths never bypass the realpath worktree-escape check. No traversal surface added.

**P2-1 — duplicated path resolution has an untested branch.** `_review-binding.cjs:284-295`. The copy is faithful today, but no test exercises the `.git`-boundary line: both governance tests place `.ai_state` at depth 0, so the branch returns before it is consulted, and the worktree test would still pass with that line deleted. The most drift-prone line in the copy is unpinned. Suggested follow-up for slice 5, which is already permitted to edit the gate: export the two helpers and delete the copies, matching what CX already does.

**P2-2 — `manifestCommit` picks the first root-level key, the gate picks the last.** `_review-binding.cjs:150-164` returns on the first match; `delivery-gate.cjs:485` assigns on every match, so the last wins. With a duplicated root-level key the preflight would compare a different value than ship does. Direction is safe (ship still blocks; only the early catch is missed). Same shape on CX.

**P2-3 — CX `resolve_path` swallows more than CC's.** `_review_binding.py:122-126` catches `OSError` broadly; CC catches only ENOENT and re-throws every other errno, which is the fail-fast the iron law wants. The CX branch is near-dead anyway since `Path.resolve()` is non-strict and every caller passes an absolute path, making it the same class of edge-case defence the polish pass removed from `mapDiffs`.

## Security

Nothing found. All git invocations use array form with no shell and inherited timeouts. `governance` performs no writes; its test hashes every non-`.git` file before and after and asserts equality, which is the right assertion for a read-only claim. No secrets, no new network or subprocess surface, no new user-controlled path reaches a write. The worktree-escape guard is unchanged and still runs on every kept input.

## Test risk

Suite reproduced independently: 52 tests, OK, 23.5s.

**P2-4 — the AC5 pin binds the test suite to this checkout's git history.** `test_state_review.py:1019-1042` shells out to `git show 0ca066c:…` with `check=True`, so the suite fails hard in a shallow clone, an exported tarball, or any checkout where that object is unreachable — a portability cost the other 51 tests do not have. The test is also self-expiring: its comment and `design.md:78` both say slice 5 removes it, but the roadmap's slice-5 entry carries no such obligation. `cleanup-pass.md` flagged this as unverified; it is in fact not recorded. This repo already has the carry-forward pattern used for slice 2's leftovers; the same treatment is what is missing here, along with the P2-1 follow-up. Roadmap edits are outside this slice's allowed write set, so this belongs to ship bookkeeping, not to rework.

**P2-5 — the cross-platform governance equality test cannot detect a resolution-rule divergence.** The tests compare against a hardcoded main-repo expectation rather than against the gate's own resolution. Combined with the pre-existing `findAiState` asymmetry that `cleanup-pass.md` correctly identifies, CC and CX governance will legitimately disagree in any layout where the nearest `.ai_state` lies above a git boundary, and AC4's equality test would not catch it. I agree with the shipped choice and agree it is pre-existing and out of scope; the finding is that the suite does not know the limit of its own equality claim.

Positives worth recording: the new tests run every scenario on both platforms, assert on stderr content rather than just exit codes, restore mutated fixtures and supersede each pending run so scenarios do not leak, and the legacy-row test constructs a genuine old row by rewriting persisted JSON rather than by mocking.

## Over-engineering

Clean. No new config option, flag, parameter or extension point in the whole slice; only the `governance` choice was added to the argument parsers. `excluded_inputs` has no machine consumer but is explicitly required by AC1 as the audit record, and the alternative is a silent hole. The `resolvePath` ENOENT catch on CC is load-bearing and re-throws every other errno. The dead guard the polish pass removed from `mapDiffs` was a correct removal: it guarded `Object.keys` against null while the next line dereferenced unguarded, so it could never have prevented the crash it appeared to prevent. Nothing meets the "delete it and tests stay green with no real caller" test except the items folded into P2-3.

## Evidence

`runtime-verify.md` binds a real run, base commit, input manifest, design contract, scenario and environment hashes, plus the PASS artifact path and sha256, with exit 0 and `blocks_delivery: false`. Eleven scenarios map onto AC1-AC5 with one honestly marked as source-workspace only — the AC5 `git show` assertion, which cannot run inside a `.git`-less bundle. Disclosed rather than papered over.

Independently reproduced the central runtime claim: `governance` returns the same hash from both platforms and equals the gate's own computation. Also confirmed the installed harness at `~/.claude` still lacks the `governance` verb, consistent with the design's stated Non-goal on installed-state sync — no evidence claim overreaches into installed state.

`cleanup-pass.md` is unusually honest for an author-side document: it hands the duplication question to review instead of self-clearing it, and its four residual risks are all real and correctly attributed to pre-existing gate behaviour. Of the four, item 4 is the one that needs action (P2-4); items 1-3 verified and agreed.

VERDICT: PASS
