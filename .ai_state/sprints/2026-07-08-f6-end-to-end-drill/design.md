# F6 Design — contract drill before live drill

## Why

F6 is the last roadmap item. The original goal is a true small-business end-to-end drill across FE, BE, and AI/cowork. Current local evidence shows the contract layer is ready, while live stack inputs are incomplete. The design therefore makes the drill two-layered.

## Approach

1. **Static contract drill**: validate all fullstack-delivery skills against the actual local quantum convention packs and MCP/cowork source contracts.
2. **Repo runtime checks**: run each feasible repo test command locally.
3. **Dynamic E2E gate**: require backend runtime-env, OAuth/test account path, and a reachable MCP endpoint before claiming a true live flow.
4. **Fallback review**: subagents were unavailable due usage limit; main thread runs reviewer/spec/evaluator prompts and records the prompts verbatim.

## Acceptance Criteria

- F2-F5 regression scripts pass.
- F6 drill script returns `static-ok-dynamic-blocked` or `ok` with no failures.
- `quantum-front bun test` passes.
- `quantum-backend mvn -pl quantum-mcp -am test` passes.
- `quantum-cowork bun test` passes.
- Dynamic blockers are concrete and actionable.

## File Structure Plan

- `scripts/test-end-to-end-drill.py`: repeatable static/dynamic readiness drill.
- `.ai_state/sprints/2026-07-08-f6-end-to-end-drill/runtime-verify.md`: real command evidence.
- `.ai_state/sprints/2026-07-08-f6-end-to-end-drill/reviews/pass1.md`: fallback review.
- `.ai_state/sprints/2026-07-08-f6-end-to-end-drill/review-prompts.md`: self-directed review prompts.

## Critic Findings Round 1

- Risk: A passing static drill can be mistaken for a live E2E. Mitigation: script status names the dynamic blocker, and runtime-verify keeps blocked cases separate.
- Risk: `quantum-cowork` remote fetch failure may hide remote drift. Mitigation: record it as a blocker and rely only on local tests for current proof.
- Risk: backend single-module Maven command can fail due reactor dependency resolution. Mitigation: use `mvn -pl quantum-mcp -am test`.

## Verdict

Proceed with static contract drill and blocked dynamic E2E closure.
