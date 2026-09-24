# Plan — F3 db-schema-gen + unit-test-gen

- Sprint: `2026-07-08-f3-db-and-unit-test-gen`
- Path: Feature
- Roadmap item: `f3-db-and-unit-test-gen`
- Target repos: `Rlues` package source; read-only input from `/Users/mi_manchi/workspace/quantum/quantum-backend`

## Goal

Turn `db-schema-gen` and `unit-test-gen` from generic skeletons into usable backend generation skills that can consume and validate the quantum-backend Convention Pack.

## Inputs Read

- `quantum-backend/docs/ai/convention-pack/db-conventions.md`
- `quantum-backend/docs/ai/convention-pack/test-conventions.md`
- `quantum-backend/docs/ai/convention-pack/validate.md`
- `quantum-backend/docs/ai/convention-pack/templates/ddl.sql.tmpl`
- `quantum-backend/docs/ai/convention-pack/templates/schema-design.md.tmpl`
- `quantum-backend/docs/ai/convention-pack/templates/test-report.md.tmpl`

## Acceptance

1. CC and CX package copies of `db-schema-gen` remain equivalent.
2. CC and CX package copies of `unit-test-gen` remain equivalent.
3. `db-schema-gen` documents the backend DB Convention Pack contract, quantum-backend adapter, G5 gates, schema-design/DDL pair, PostgreSQL dialect, audit/version/deleted/dept_id rules.
4. `unit-test-gen` documents the backend test Convention Pack contract, quantum-backend adapter, G6 gates, JUnit5/Mockito/AssertJ patterns, required test method names, and report template.
5. A deterministic validator script checks the quantum-backend pack for DB/test required files, templates, validation gates, and placeholder coverage.
6. Tests prove the validator passes against the live quantum-backend pack and fails on missing required files/markers.

## Implementation Tasks

- Add `references/backend-db-convention-pack.md` and `references/quantum-backend-adapter.md` to `db-schema-gen`.
- Add `references/backend-test-convention-pack.md` and `references/quantum-backend-adapter.md` to `unit-test-gen`.
- Add shared `scripts/check_backend_pack.py` to both skills.
- Update CC/CX `SKILL.md` files to read the right references and run the validator.
- Add repo-level regression test for both package copies and the live quantum-backend pack.

## Validation Commands

- `python3 scripts/test-db-unit-gen.py`
- `python3 -m py_compile .../check_backend_pack.py scripts/test-db-unit-gen.py`
- Clean `__pycache__`, then `diff -qr` CC/CX copies for both skills.
- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on all four skill folders.
