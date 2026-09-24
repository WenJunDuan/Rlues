# Biz Delivery Loop Orchestration Contract

`biz-delivery-loop` is a PACE specialization. It coordinates existing skills and evidence, but it
does not implement code, own a parallel state machine, or guess project-specific commands.

## Single State Authority

- `_index.md` remains the only durable workflow state.
- `roadmap/items.yaml` owns item status and dependency ordering.
- Sprint artifacts own evidence: `design.md`, `runtime-verify.md`, `reviews/implementation-review.md`,
  `checkpoints.yaml`, and `delivery-report.md`. Optional usage is a cited native source, not a required collector file.
- Rework uses PACE next actions (`rework_impl`, `runtime-verify`, `polish`, `review`, `ship`) and checkpoint
  `fail_target`; it never rolls all the way back unless the checkpoint says so.

## Skill Chain

| Step | Skill | Required input | Required output |
|---|---|---|---|
| FE demo | `quantum-codegen (mode=page)` | FE Convention Pack + runtime-env | runnable demo evidence |
| DB package | `quantum-codegen (mode=db)` | DB Convention Pack + schema requirements | design doc + DDL |
| BE module | `quantum-codegen (mode=module)` | backend Convention Pack + DB/API contract | compile-ready module |
| Unit/debug | `quantum-codegen (mode=unit)` | test Convention Pack + changed code | tests + report |
| E2E | `quantum-codegen (mode=e2e)` | runtime-env + accepted flows | rerunnable tests + trace/screenshot/report |
| Security | `quantum-codegen (mode=security)` | security gates + runtime-env + accounts | static/dynamic security report |
| Runtime reads | `quantum-data` | MCP endpoint + Capability Manifest | read-only structured evidence |

## Checkpoint Rules

- CP1 mockup and CP3 schema are human confirmations; cite prior valid decisions and do not ask again or fake approval.
- CP2 demo, CP4 backend gate, E2E/security, and contract diff are machine gates.
- Every checkpoint records evidence, attempt, `fail_target`, `rollback_target`, and `issue_path`.
- Three consecutive failures on the same checkpoint produce a blocked issue and stop the loop.

## Evidence Rules

- Command evidence must include command, cwd, exit code, summary, and artifact path when available.
- Runtime-env warnings go into both `runtime-verify.md` and `delivery-report.md`.
- Token usage reads an available native output reference; a legacy `token-usage.yaml` may be consumed if it already exists. Unavailable totals stay `null` with status `unavailable`; missing usage does not block functional delivery.
- Capability reads must cite the manifest and the read-only capability name.
- Dynamic E2E/security gaps are `blocked_dynamic_cases`, not silently passed tests.

## Admission, Parallel Work and Review

Follow [PACE execution contracts](../../pace/references/execution-contracts.md) for real-project admission, input/evidence binding, writer recovery and final integration. CX-only can execute the full applicable chain. Mock demos do not satisfy real FE/BE/DB acceptance. R/S performs runtime-verify → polish → one independent review; no legacy three-role chain.

## Blocking Conditions

- Missing Convention Pack or runtime-env for a requested runnable slice.
- Missing checkpoint evidence or report fields.
- `quantum-data` capability is not declared read-only.
- Delivery report omits requirement reconciliation, test/security/E2E evidence, token status, or manual confirmations.
