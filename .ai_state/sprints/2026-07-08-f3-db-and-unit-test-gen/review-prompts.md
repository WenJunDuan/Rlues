# Review Prompts — F3 db-schema-gen + unit-test-gen

## Fallback Reason

Subagent review was attempted but failed due Codex usage limit. User explicitly instructed the main
thread to continue by writing the prompts and carrying out the work locally.

## Reviewer Prompt

Review F3 sprint `2026-07-08-f3-db-and-unit-test-gen` for correctness, security, test coverage,
design consistency, and quality. Treat `plan.md` as the spec. Scope:

- `db-schema-gen` SKILL/references/scripts in CC and CX.
- `unit-test-gen` SKILL/references/scripts in CC and CX.
- `scripts/test-db-unit-gen.py`.
- F3 `.ai_state` files.

Find P0/P1/P2 issues with file/line references. Check that validator logic is read-only, does not
execute DDL/Maven, and that negative tests prove missing required files/markers fail.

## Spec Compliance Prompt

Compare F3 acceptance criteria in `plan.md` against the current diff:

- CC/CX `db-schema-gen` parity.
- CC/CX `unit-test-gen` parity.
- DB contract covers G5, schema-design/DDL pair, PostgreSQL, audit/version/deleted/dept_id rules.
- Test contract covers G6, JUnit5/Mockito/AssertJ, required method names, report template.
- Validator checks required backend pack files, templates, validation gates, placeholders.
- Regression passes against live quantum-backend pack and fails on missing DB/test files and G5/G6 markers.

Output MISSING/EXTRA/DEVIATED and PASS/REWORK.
