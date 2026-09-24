# Review Prompts — F5 biz-delivery-loop

## Fallback Reason

Subagent review remained unavailable due Codex usage limit. User explicitly instructed the main
thread to write the prompts and carry out the work locally.

## Reviewer Prompt

Review F5 sprint `2026-07-08-f5-biz-delivery-loop` for correctness, security, test coverage, design
consistency, quality, and System-path evidence. Treat `plan.md` and `design.md` as the spec.

Scope:

- `biz-delivery-loop` SKILL/references/scripts in CC and CX.
- `project-data-reader` SKILL/references/scripts in CC and CX.
- `scripts/test-biz-delivery-loop.py`.
- F5 `.ai_state` files and architecture update.

Find P0/P1/P2 issues with file/line references. Check that validators are read-only, reject write
capabilities and static secrets, and that delivery-report schema cannot imply unrun dynamic tests.

## Spec Compliance Prompt

Compare F5 acceptance criteria in `plan.md` against the current diff. Output MISSING/EXTRA/DEVIATED
and PASS/REWORK. Include an Evidence Cross-Check against `runtime-verify.md`.
