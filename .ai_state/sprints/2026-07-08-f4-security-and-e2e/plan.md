# Plan — F4 security-test + playwright-e2e

- Sprint: `2026-07-08-f4-security-and-e2e`
- Path: Feature
- Roadmap item: `f4-security-and-e2e`
- Target repos: `Rlues` package source; read-only input from `quantum-front` and `quantum-backend`

## Goal

Turn `security-test` and `playwright-e2e` from generic skeletons into usable full-stack verification
skills that can consume project Convention Packs, fail closed on missing runtime-env, and hand
evidence into runtime-verify / delivery reports.

## Inputs Read

- `quantum-front/docs/ai/convention-pack/conventions.md`
- `quantum-front/docs/ai/convention-pack/validate.md`
- `quantum-front/docs/ai/convention-pack/runtime-env.md`
- `quantum-backend/docs/ai/convention-pack/conventions.md`
- `quantum-backend/docs/ai/convention-pack/validate.md`
- `quantum-backend/docs/ai/convention-pack/templates/Controller.java.tmpl`
- `quantum-backend/docs/ai/convention-pack/templates/ServiceImpl.java.tmpl`
- `quantum-backend/docs/ai/convention-pack/templates/menu-permission.sql.tmpl`
- `biz-delivery-loop/references/runtime-env-contract.md`

## Acceptance

1. CC and CX package copies of `security-test` remain equivalent.
2. CC and CX package copies of `playwright-e2e` remain equivalent.
3. `security-test` documents a generic security-test contract plus quantum security adapter.
4. `playwright-e2e` documents a generic E2E contract plus quantum E2E adapter.
5. A shared validator checks FE/BE pack structure, security gates, runtime-env markers, and E2E contract markers.
6. The validator passes against the live quantum packs and fails on missing runtime-env, missing backend validate, missing permission annotation, and missing access exemption marker.
7. Dynamic full-stack E2E/security is explicitly blocked when backend/database runtime-env or authorized test accounts are not declared; static contract verification still passes.

## Implementation Tasks

- Add `references/security-test-contract.md` and `references/quantum-security-adapter.md` to `security-test`.
- Add `references/e2e-convention-pack.md` and `references/quantum-e2e-adapter.md` to `playwright-e2e`.
- Add shared `scripts/check_security_e2e_pack.py` to both skills.
- Update CC/CX `SKILL.md` files to read the right references and run the validator.
- Add repo-level regression test for both package copies and the live quantum FE/BE packs.

## Validation Commands

- `python3 scripts/test-security-e2e.py`
- `python3 -m py_compile .../check_security_e2e_pack.py scripts/test-security-e2e.py`
- Clean `__pycache__`, then `diff -qr` CC/CX copies for both skills.
- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on all four skill folders.
