# Runtime Verify — F5 biz-delivery-loop

## /goal 完成条件

1. Loop contract validator passes on CC/CX `biz-delivery-loop`.
2. Capability Manifest validator passes on a valid read-only manifest and fails on write/static-secret/missing-data-scope manifests.
3. CC/CX source parity holds for `biz-delivery-loop` and `project-data-reader`.
4. F2/F3/F4 regression scripts still pass after F5 changes.

## 测试场景 (实跑)

| 场景 | 类型 | 命令 | 实际输出 | 判定 |
|---|---|---|---|---|
| F5 regression | script | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-biz-delivery-loop.py` | `biz-delivery-loop and project-data-reader regression ok` | PASS |
| F5 syntax | compile | `python3 -m py_compile scripts/test-biz-delivery-loop.py .../check_delivery_loop_contract.py .../check_capability_manifest.py` | exit 0 | PASS |
| F5 skill validation | skill schema | `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill>` for four folders | `Skill is valid!` x4 | PASS |
| F2-F5 regression chain | script | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-scaffold-page-gen.py && PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-db-unit-gen.py && PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-security-e2e.py && PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-biz-delivery-loop.py` | all four `... regression ok` lines | PASS |

## 自测自改记录

- Tightened F4 validators during runtime checks to avoid marker-anywhere false positives.
- F5 validators were designed per-file from the start: loop fields are checked in their owning reference, manifest read boundaries are checked per capability.

## Reflect

- The package contract is now mechanically testable, but no live MCP server or real browser/business flow was exercised in F5. That is intentional and remains F6 scope.
- Dynamic full-stack E2E/security remains blocked unless a target project declares backend/database runtime-env and test accounts.

## VERDICT

PASS. F5 may enter review.
