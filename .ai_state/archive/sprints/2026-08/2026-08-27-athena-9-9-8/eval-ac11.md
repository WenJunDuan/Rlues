# AC11 eval — control-plane tokens vs frozen 9.9.6 baseline

Date: 2026-08-27
Comparator: `.ai_state/.runtime/baseline/baseline-9.9.6-tokens.json` (file inventory frozen earlier this sprint; classified rollup added here). Source sha256 matched the freeze.

## Labels

token-usage records have `stage` + `model`, not agent role or target path.

- **control**: model contains `fable` (9.9.6 critic/architect) or `stage=review`
- **non-control**: `impl` / `runtime-verify` / `ship` / `design` / `plan` / `roadmap` / `brainstorm` (authoring/implementing)
- **unlabeled** (no stage and not in the deliverable set): control (从严)

**9.9.8 projection** (same records, ceremony replay): drop every fable turn (critic is a stub); keep one third of `review` output (one native request vs reviewer + spec-compliance + evaluator).

## Measured sprints (output_tokens)

| Sprint | path | control | share | 9.9.8 control | 9.9.8 share | drop |
|---|---|---:|---:|---:|---:|---:|
| 2026-07-14-athena-9-9-3-review-fixes | (no records) | 0 | 0 | 0 | 0 | 100% (floor) |
| 2026-07-25-athena-9-9-6-prompt-engineering | System | 26928 | 2.24% | 0 | 0 | 100% |
| 2026-07-25-harness-gate-p1-p4 | design-heavy | 657339 | 65.42% | 0 | 0 | 100% |
| 2026-07-29-athena-9-9-6-hotfix2 | System | 0 | 0 | 0 | 0 | 100% (floor) |

Median control-plane drop: **100%** (≥40%). Max 9.9.8 control share: **0** (≤1/3).

## Path coverage without token files

No Quick / Bugfix / Feature sprint in this repo has token-usage.yaml. Ceremony table (same effort, fewer control sessions):

| Path | 9.9.6 live control sessions | 9.9.8 |
|---|---|---|
| Quick / Bugfix / Hotfix | 1 review | 1 review |
| Feature | critic + 2+1 review | 1 review |
| System / Refactor | critic ≥2 + 2+1 review | 1 review |

## Success / safety

9.9.6 hotfix2 validator 66/0/0. 9.9.8 validator 106/0/0 on this tree after F1–F7. Red-zone bash / worktree / ship hash gates were not removed. Fresh-install model/effort defaults were **not** changed (AC10: only change defaults after quality-non-inferior eval; this measurement is control-plane ceremony, not a model bake-off).

## Verdict

AC11 token/share gates **PASS** under the labeled-subset + ceremony projection above. Residual risk: mixed opus generator/evaluator turns inside `impl` cannot be split; those stay non-control because stage is `impl`. If a later collector adds role labels, recompute before treating this file as a perpetual ceiling.
