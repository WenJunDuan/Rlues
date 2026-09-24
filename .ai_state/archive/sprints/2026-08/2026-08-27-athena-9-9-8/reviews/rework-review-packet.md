---
schema_version: 1
sprint_slug: "2026-08-27-athena-9-9-8"
mode: "implementation-rework"
scope: "targeted (AC4); not a third full review"
generated_from: "reviews/implementation-review.md CONCERNS F1–F8 + remaining AC9/AC11/install"
created: "2026-08-27"
author_does_not_review: true
implementer: "grok"
reviewer_constraint: "must not be implementer session"
output: "reviews/rework-review.md"
parent_review: "reviews/implementation-review.md"
---

# Targeted re-review packet — 9.9.8 F1–F7 + leftover AC9/AC11/install

Do **not** re-read design or reopen the first implementation review. Look only at the increment below. Same-cause new P0 ×2 → return to user (AC4).

## What to inspect

1. **Hash / untracked (F1–F2)** — `delivery-gate.cjs` `sourceDiffSha256` and `delivery-gate.py` `source_diff_sha256`: `git ls-files -c -o --exclude-standard`, `.ai_state/` excluded, empty live hash fail-closed. Validator parity fixture includes an untracked file.
2. **Gate runtime fixtures (F3)** — `validate-athena-9.9.8.py` `check_998_gate_runtime`: stale design hash, missing/extra AC, missing `implementation-review.md`, missing `native_output_ref` path, diff-hash mismatch; both CC and CX processes.
3. **Quote fixture (F5)** — CC `pre-bash-guard.cjs` via `node -e`; CX already imported. Quoted `$(` not a substitution; bare `$(` still is.
4. **Evidence (F4/F7)** — `python3 vibeCoding/scripts/validate-athena-9.9.8.py` last clean run **106/0/0** then this increment adds bounds/AC11 checks. Package must have no `__pycache__`. Validator loads hooks via `exec`, not `py_compile`.
5. **Telemetry / migrate (F6)** — six sprint token-usage/tool-trace `git rm --cached` (local copies kept); `.ai_state/.runtime/` gitignored; `AI-MIGRATION-GUIDE.md` + `athena-migrate` skill at 9.9.8.
6. **AC9 160B** — `_index-bounds.cjs` / `_index_bounds.py`; overflow to `sprints/{slug}/index-overflow.md`. Live `_index.md` after enforce: file ≤12KiB, `route_history` ≤10 and ≤160B/item, 当前状态 ≤10 and ≤160B/item. Full text in overflow, not dropped.
7. **AC11** — `eval-ac11.md` + `.ai_state/.runtime/baseline/baseline-9.9.6-tokens.json` classified rollup. Source sha256 matched freeze. Median control-plane drop 100% on labeled fable/review subset; 9.9.8 projected share 0. Ceremony table covers Quick/Bugfix/Feature (no token files). Do not treat unlabeled `impl` opus mix as split.
8. **Install** — `deployment.md`. Backup `~/.athena/backups/athena-9.9.8-20260827T063329Z`. Preserved CC `model=opus[1m]` / `effortLevel=xhigh`; CX `openai_base_url` + `model_reasoning_effort=xhigh`. Version markers 9.9.8. Histories/sessions not copied.

## Out of scope

Design challenge, first implementation review findings already folded, model default bake-off (AC10: defaults not changed).

## Output

Write `reviews/rework-review.md` with frontmatter (`verdict`, `finding_counts`, `review_run_id`, `native_output_ref`). Last line `VERDICT: PASS|CONCERNS|REWORK|FAIL`.
