# Plan — F2 scaffold-page-gen

- Sprint: `2026-07-08-f2-scaffold-page-gen`
- Path: Feature
- Roadmap item: `f2-scaffold-page-gen`
- Target repos: `Rlues` package source; read-only input from `/Users/mi_manchi/workspace/quantum/quantum-front`

## Goal

Turn `scaffold-page-gen` from a thin skeleton into a usable frontend page generation skill that can consume a target frontend Convention Pack, with quantum-front as the first concrete adapter.

## Inputs Read

- `quantum-front/docs/ai/convention-pack/conventions.md`
- `quantum-front/docs/ai/convention-pack/validate.md`
- `quantum-front/docs/ai/convention-pack/templates/*`
- Existing examples under `src/features/system/user` and `src/features/system/role`

## Acceptance

1. CC and CX package copies of `scaffold-page-gen` remain equivalent.
2. `SKILL.md` stays concise and points to references only when needed.
3. A generic frontend Convention Pack contract exists: required files, template expectations, runtime-env, validation evidence.
4. A quantum-front adapter reference records the actual pack path, React/Vite/TanStack/shadcn conventions, route registration, security gates G1-G6, and validation commands.
5. A deterministic validator script can check a Convention Pack directory for required files/templates and placeholder coverage.
6. Tests prove the validator passes against the live quantum-front Convention Pack and fails on a missing required file.

## Implementation Tasks

- Add `references/frontend-convention-pack.md`.
- Add `references/quantum-front-adapter.md`.
- Add `scripts/check_frontend_pack.py`.
- Update CC/CX `SKILL.md` to read the right reference by scaffold id.
- Add repo-level regression test for both package copies.

## Validation Commands

- `python3 scripts/test-scaffold-page-gen.py`
- `python3 -m py_compile .../check_frontend_pack.py scripts/test-scaffold-page-gen.py`
- `find ... -name __pycache__ -prune -exec rm -rf {} +` then `diff -qr` between CC/CX scaffold-page-gen directories.
- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on both skill folders.
