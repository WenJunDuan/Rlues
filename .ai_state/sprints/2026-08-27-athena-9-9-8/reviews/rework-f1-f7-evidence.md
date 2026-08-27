# Rework evidence — implementation-review F1–F7

Date: 2026-08-27
Implementer: grok (not a self-review; VERDICT stays with independent reviewer)

## Validator (this machine)

Command: `python3 vibeCoding/scripts/validate-athena-9.9.8.py`

```
SUMMARY pass=106 fail=0 skip=0
```

Python 3.14.3, node v25.9.0. Exit 0. After the run: no `__pycache__` / `.pyc` / `.vv*.py` under `vibeCoding/{claude,codex}/9.9.8` or `vibeCoding/scripts`.

The earlier `_index` claim `87 PASS / 0 FAIL / 0 SKIP` was wrong (review measured 75/4/4). Do not reuse it.

## Tree hash (271 files)

`vibeCoding/{claude,codex}/9.9.8/**` + `vibeCoding/scripts/validate-athena-9.9.8.py`, excluding junk:

`files=271 sha256=f9da8d87522d2a3b51c3acbc359369e9a312dde490930abe924ab6b6f2cb0093`

Review snapshot was `reviewed_tree_sha256=65d74213…` (same 271 paths; content changed by this rework).

## Finding map

| ID | Change |
|---|---|
| F1 | `sourceDiffSha256` / `source_diff_sha256` = `git ls-files -c -o --exclude-standard` tree contents (untracked included; `.ai_state/` excluded). Empty live hash is fail-closed. |
| F2 | Same algorithm both ends; validator parity fixture on a repo with an untracked file. |
| F3 | `check_998_gate_runtime`: stale design hash, missing AC, extra AC, missing `implementation-review.md`, missing `native_output_ref` path, diff-hash mismatch — CC and CX processes. |
| F4 | Validator 106/0/0 on this tree; no package junk; `_index` snippet corrected here. |
| F5 | `node -e require(pre-bash-guard.cjs)`: quoted `$(` not a substitution; bare `$(` still is. |
| F6 | Six sprint telemetry files `git rm --cached` (local copies kept); `.ai_state/.runtime/` gitignored; migration guide + `athena-migrate` skill updated to 9.9.8. 160B overflow still deferred to ship. |
| F7 | Validator docstring points at `implementation-review.md`; `.vv*.py` ignored; leftover `.vv310.py` removed; load via `exec` so the validator cannot plant `__pycache__`. |
| F8 | Unchanged. AC11 representative-task eval remains a ship gate. |

Targeted re-review should look at gate function diffs, new fixtures, this SUMMARY, and the corrected `_index` snippet — not a third full review round.
