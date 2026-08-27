---
schema_version: 1
mode: implementation-rework
packet_sha256: "0a9b6694da7dde81178f380b0609380ef456ebdfd1413051352bd8bb19f08258"
reviewed_diff_sha256: "bc586e11e99fbf097db84ba2fa9e3e197375c9da70b5a11d1e3c0184ebbca7a7"
review_run_id: "impl-rev-20260827-targeted-rework-01"
native_output_ref: "direct"
reviewer: "independent reviewer subagent (not implementer)"
implementer: "grok"
parent_review: "reviews/implementation-review-20260827-concerns.md"
review_date: "2026-08-27"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 2}
dimensions: [spec, correctness, security, tests, overengineering, evidence]
---

# Targeted re-review — F1–F7 + AC9/AC11/install

Independent of the implementer session. Scope is the increment in `reviews/rework-review-packet.md`. Live tree hash recomputed: `source_diff_sha256` = `bc586e11e99fbf097db84ba2fa9e3e197375c9da70b5a11d1e3c0184ebbca7a7` (4433 files; `.ai_state/` excluded). Validator this run: `SUMMARY pass=120 fail=0 skip=0`.

## F1–F8 disposition (closed)

- **F1 closed.** CC/CX hash is `git ls-files -z -c -o --exclude-standard`, skip `.ai_state/`, `path\0contents\n`. Untracked extra file changes the digest (fixture). CC computation failure returns `""` and `validateReview` blocks.
- **F2 closed.** Same algorithm both ends. Fixture: CC `sourceDiffSha256` == CX `source_diff_sha256` on a repo that includes an untracked file.
- **F3 closed.** `check_998_gate_runtime` drives CC and CX processes: stale design hash, missing AC, extra AC, missing `implementation-review.md`, missing `native_output_ref` path, diff-hash mismatch — all fail-closed.
- **F4 closed.** No `__pycache__` / `.pyc` under canonical 9.9.8 packages after validator (`exec` load + `dont_write_bytecode`). Live SUMMARY 120/0/0, not the retracted 87/0/0.
- **F5 closed.** `node -e require(pre-bash-guard.cjs)`: `rg 'foo$(rm -rf /)bar'` → no substitution; bare `$(...)` still detected. CX import fixture still green.
- **F6 closed.** Sprint `token-usage.yaml` / `tool-trace.jsonl` absent from git index; local copies kept. `.ai_state/.runtime/` gitignored. `AI-MIGRATION-GUIDE.md` + `athena-migrate` are 9.9.8 (passN → implementation-review, stubs, telemetry).
- **F7 closed.** Validator docstring points at `reviews/implementation-review.md`. `.vv*.py` gitignored; no leftover `.vv310.py` in `scripts/`.
- **F8 / AC11 closed.** `eval-ac11.md` + classified rollup. Source sha256 of the four frozen token files match. Median control-plane drop 100%; 9.9.8 projected share 0. Unlabeled `impl` opus mix is not split (documented residual, not a miss).

## AC9 / install (packet leftover)

- Live `_index.md` 10088 B ≤ 12 KiB. `route_history` 10× ≤160 B. `当前状态` 10× ≤160 B. Overflow file keeps full text (`index-overflow.md#st-*` / `rh-*`). Bounds modules are wired into CC/CX `index-updater`.
- Install: CC `model=opus[1m]` `effortLevel=xhigh` `VIBECODING_ATHENA_VERSION=9.9.8`; CX `gpt-5.6-sol` `model_reasoning_effort=xhigh` + `openai_base_url`; `VIBECODING_VERSION=9.9.8`. Installed delivery-gate / bounds / pre-bash-guard hashes match canonical 9.9.8. `~/.claude/REVIEW.md` present. History fingerprints unchanged vs redeploy record (CC `history.jsonl` 350165 B `a4335c62fab8…`; CX 37162 B `d9fe194b5a5f…`; projects 695 / sessions 476 / archived 45).

## Residual findings

### F9 [P2] CX git-failure path hashes the empty tree instead of returning empty live hash
- AC: packet F1 “empty live hash fail-closed”
- Location: `codex/9.9.8/.codex/hooks/delivery-gate.py` `list_source_files` (`returncode != 0` → `[]`) then `source_diff_sha256` returns `e3b0c442…`
- Fact: CC `sourceDiffSha256` on a non-git dir returns `""` (fail-closed in `validateReview`). CX returns the empty hasher digest. On this repo a real review binds `bc586e11…`, so a later git failure still mismatches and blocks. Residual is degraded-mode parity, not the original untracked hole.

### F10 [P2] Packet-cited first backup directory is gone
- Packet named `~/.athena/backups/athena-9.9.8-20260827T063329Z`. That path is absent. Redeploy backup `athena-9.9.8-redeploy-20260827T110206Z` exists; live config + history fingerprints above still hold the install AC.

No new P0. Same-cause P0 ×2 did not recur.

VERDICT: PASS
