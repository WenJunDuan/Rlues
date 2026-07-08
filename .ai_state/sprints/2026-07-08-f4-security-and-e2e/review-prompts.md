# Review Prompts — F4 security-test + playwright-e2e

## Fallback Reason

Subagent review remained unavailable due Codex usage limit. User explicitly instructed the main
thread to write the prompts and carry out the work locally.

## Reviewer Prompt

Review F4 sprint `2026-07-08-f4-security-and-e2e` for correctness, security, test coverage, design
consistency, and quality. Treat `plan.md` as the spec. Scope:

- `security-test` SKILL/references/scripts in CC and CX.
- `playwright-e2e` SKILL/references/scripts in CC and CX.
- `scripts/test-security-e2e.py`.
- F4 `.ai_state` files.

Find P0/P1/P2 issues with file/line references. Check that validator logic is read-only, does not
start browsers/services or run security scans, and that missing runtime-env/test-account coverage is
reported blocked instead of inferred.

## Spec Compliance Prompt

Compare F4 acceptance criteria in `plan.md` against the current diff:

- CC/CX `security-test` parity.
- CC/CX `playwright-e2e` parity.
- Security contract covers FE access gates, BE permissions/data-scope gates, runtime-env, dynamic-case blocking.
- E2E contract covers runtime-env startup, Playwright wrapper behavior, evidence paths, and FE/BE contract mapping.
- Validator checks required FE/BE files, runtime-env markers, security gates, and E2E markers.
- Regression passes against live quantum packs and fails on missing runtime-env, backend validate, permission annotation, and access exemption marker.

Output MISSING/EXTRA/DEVIATED and PASS/REWORK.
