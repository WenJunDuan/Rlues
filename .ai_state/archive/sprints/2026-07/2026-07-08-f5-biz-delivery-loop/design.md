# Design — F5 biz-delivery-loop

## Round 1

F5 turns the fullstack-delivery family from independent skill contracts into a validated package
loop. The implementation stays inside Rlues package files and does not call live systems.

### Decisions

- `biz-delivery-loop` remains a PACE specialization. `_index.md` and roadmap items stay the only workflow state.
- The loop contract is a reference file, not code that runs the workflow. The script validates the contract surface.
- Delivery report frontmatter is extended so F6 can report runtime-env warnings, blocked dynamic E2E/security cases, token usage status, and `project-data-reader` reads.
- `project-data-reader` gets a local JSON manifest validator. It rejects write capabilities and static secrets before any live MCP call is trusted.

### File Structure Plan

- `biz-delivery-loop/references/orchestration-contract.md`
- `biz-delivery-loop/scripts/check_delivery_loop_contract.py`
- `project-data-reader/references/capability-manifest-contract.md`
- `project-data-reader/scripts/check_capability_manifest.py`
- `scripts/test-biz-delivery-loop.py`

## Critic Findings Round 1

- Risk: a validator that only checks any marker anywhere can produce false positives. Resolution:
  `check_delivery_loop_contract.py` checks the specific reference file responsible for each marker group.
- Risk: manifest validation could accept read-looking tools without auth/audit/data-scope declarations. Resolution:
  `check_capability_manifest.py` requires per-capability permission, data_scope, audit, redaction, input_schema, and output_schema.
- Risk: delivery reports could imply dynamic E2E/security ran when runtime-env is incomplete. Resolution:
  `delivery-report-schema.md` now includes `blocked_dynamic_cases` and `runtime_env_warnings`.

## Round 2

The final design keeps deterministic tests synthetic by design: this sprint validates package
contracts, while F6 performs the real end-to-end drill. The validators avoid network and MCP calls,
so they are safe to run in package CI or local preflight.

### Acceptance Mapping

- Loop contract: single state authority, skill chain, checkpoints, evidence, blockers.
- Report schema: requirement status, FE/BE/E2E/security tests, token status, capability reads, manual confirmations.
- Reader contract: OAuth/MCP identity passthrough, read-only tools, target-enforced permission/data-scope, no embedded secrets.
- Regression: positive and negative validators plus CC/CX parity.

## Critic Findings Round 2

- Risk: project-data-reader could be mistaken for a codegen skill. Resolution:
  SKILL.md and manifest contract repeat that it is runtime read-only and hands evidence to `biz-delivery-loop`.
- Risk: F5 could overreach into quantum MCP implementation. Resolution:
  this sprint only defines system-agnostic manifest shape and validator; quantum S3/F6 owns live capability proof.
- Risk: System delivery gate requires runtime-verify/review/polish even for contract-only package work. Resolution:
  this sprint includes runtime-verify.md, Evidence Cross-Check in pass1, cleanup-pass, and architecture updates.
