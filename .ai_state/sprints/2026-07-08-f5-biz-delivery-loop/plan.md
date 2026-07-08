# Plan — F5 biz-delivery-loop

- Sprint: `2026-07-08-f5-biz-delivery-loop`
- Path: System
- Roadmap item: `f5-biz-delivery-loop`
- Target repos: `Rlues` package source only

## Goal

Close the package-level orchestration slice: make `biz-delivery-loop` mechanically validate its
checkpoint/report/runtime-env orchestration contracts, and make `project-data-reader` mechanically
validate Capability Manifest read-only boundaries.

## Acceptance

1. CC/CX `biz-delivery-loop` stay source-equivalent.
2. CC/CX `project-data-reader` stay source-equivalent.
3. `biz-delivery-loop` documents a single-state-authority orchestration contract mapping F2-F4 skills, checkpoints, evidence, token usage, runtime-env warnings, and dynamic blockers.
4. `delivery-report-schema.md` includes token status, runtime-env warnings, blocked dynamic cases, and runtime read evidence.
5. `check_delivery_loop_contract.py` validates the loop references and required report/checkpoint/runtime markers.
6. `project-data-reader` documents a Capability Manifest contract and refuses write capabilities, missing permission/data-scope/audit, and static secrets.
7. `scripts/test-biz-delivery-loop.py` covers positive and negative validator behavior plus CC/CX parity.
8. System path closeout includes runtime-verify, review Evidence Cross-Check, polish cleanup, and architecture update.

## Implementation Tasks

- Add `references/orchestration-contract.md` and `scripts/check_delivery_loop_contract.py` to `biz-delivery-loop`.
- Extend `delivery-report-schema.md` with token status, runtime-env warnings, dynamic blockers, and capability read evidence.
- Add `references/capability-manifest-contract.md` and `scripts/check_capability_manifest.py` to `project-data-reader`.
- Update both SKILL.md files to load the new references and run validators.
- Add repo-level regression test for both skill families.

## Validation Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-biz-delivery-loop.py`
- `python3 -m py_compile .../check_delivery_loop_contract.py .../check_capability_manifest.py scripts/test-biz-delivery-loop.py`
- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on all four skill folders.
- Clean `__pycache__`, then `diff -qr` CC/CX copies for both skills.
