---
doc_type: learning
slug: "codex-wire-evidence-fail-closed"
created: "2026-07-10"
sprint_slug: "2026-07-10-athena-9-9-1-validation"
severity: "P0"
status: executed
---

# Learning: Codex wire evidence must fail closed

## 现象

Athena 9.9.0 could load on Codex 0.144.1 while still producing false completion: PostToolUse read a legacy field, SubagentStop was treated as if it carried an exit code, and a generator Start or unknown evidence could satisfy delivery state.

## 根因

Prompt-era assumptions were treated as runtime facts. Canonical task identity, raw lifecycle identity, tool response shape, and user-visible completion were collapsed into one record even though the current platform exposes them through different surfaces.

## 教训

Compatibility is an executable contract, not a successful parse. Every completion claim must trace to an official wire field or an explicit command result; absence, ambiguity, strings, booleans, malformed rows, and unknown-only evidence remain unknown and cannot pass a gate.

## 可复用模式

1. Pin behavior to official schemas/source for the exact CLI version.
2. Store raw lifecycle events without inferred role or exit status.
3. Bind task role to raw `agent_id` in a separate main-thread-owned assignment record.
4. Join assignment, Stop, checklist, evidence, roadmap, and latest review at the gate.
5. Require at least one explicit pass and zero explicit fail; never infer success from non-empty output.
6. Ship one validator that reruns syntax, behavior, parity, baseline, isolated install, and discovery checks.

## 影响

- Athena 9.9.1 gates block orphaned, ambiguous, malformed, pending, failed, and unknown-only chains.
- Setup/migrate use one transaction across selected endpoints, because partial compatibility is another form of false success.
- Future Codex upgrades must start from source/schema diff plus negative fixtures before prompt edits.

## 相关引用

- PostToolUse schema: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/post-tool-use.command.input.schema.json
- Multi-agent v2 tools: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core/src/tools/handlers/multi_agents_spec.rs
- Codex skill loader: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337
- Review: `.ai_state/sprints/2026-07-10-athena-9-9-1-validation/reviews/pass2.md`
