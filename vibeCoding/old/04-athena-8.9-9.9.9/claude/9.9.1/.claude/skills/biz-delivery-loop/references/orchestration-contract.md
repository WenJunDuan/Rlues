# Biz Delivery Loop Orchestration Contract

`biz-delivery-loop` is a PACE specialization. It coordinates existing skills and evidence, but it
does not implement code, own a parallel state machine, or guess project-specific commands.

## Single State Authority

- `_index.md` remains the only durable workflow state.
- `roadmap/items.yaml` owns item status and dependency ordering.
- Sprint artifacts own evidence: `design.md`, `runtime-verify.md`, latest `reviews/passN.md`,
  `checkpoints.yaml`, `delivery-report.md`, and `token-usage.yaml`.
- Rework uses PACE next actions (`rework_impl`, `runtime-verify`, `review`, `ship`) and checkpoint
  `fail_target`; it never rolls all the way back unless the checkpoint says so.

## Skill Chain

| Step | Skill | Required input | Required output |
|---|---|---|---|
| FE demo | `scaffold-page-gen` | FE Convention Pack + runtime-env | runnable demo evidence |
| DB package | `db-schema-gen` | DB Convention Pack + schema requirements | design doc + DDL |
| BE module | `scaffold-module-gen` | backend Convention Pack + DB/API contract | compile-ready module |
| Unit/debug | `unit-test-gen` | test Convention Pack + changed code | tests + report |
| E2E | `playwright-e2e` | runtime-env + accepted flows | rerunnable tests + trace/screenshot/report |
| Security | `security-test` | security gates + runtime-env + accounts | static/dynamic security report |
| Runtime reads | `project-data-reader` | MCP endpoint + Capability Manifest | read-only structured evidence |

## Checkpoint Rules

- CP1 mockup and CP3 schema are human confirmations; do not fake approval.
- CP2 demo, CP4 backend gate, E2E/security, and contract diff are machine gates.
- Every checkpoint records evidence, attempt, `fail_target`, `rollback_target`, and `issue_path`.
- Three consecutive failures on the same checkpoint produce a blocked issue and stop the loop.

## Evidence Rules

- Command evidence must include command, cwd, exit code, summary, and artifact path when available.
- Runtime-env warnings go into both `runtime-verify.md` and `delivery-report.md`.
- Token usage reads `token-usage.yaml`; unknown totals stay `null`.
- Capability reads must cite the manifest and the read-only capability name.
- Dynamic E2E/security gaps are `blocked_dynamic_cases`, not silently passed tests.

## Blocking Conditions

- Missing Convention Pack or runtime-env for a requested runnable slice.
- Missing checkpoint evidence or report fields.
- `project-data-reader` capability is not declared read-only.
- Delivery report omits requirement reconciliation, test/security/E2E evidence, token status, or manual confirmations.
