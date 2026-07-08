---
doc_type: decision
slug: "token-usage-null-and-subagent-stop"
created: "2026-07-08"
sprint_slug: "2026-07-07-f1-orchestrator-framework-design"
status: accepted
deciders: ["user", "codex"]
---

# Decision: token-usage-null-and-subagent-stop

## 背景

Athena delivery reports need sprint token usage, but hook payloads do not always expose usage or transcript paths. Subagent transcripts may be separate from the main transcript.

## 选项

### 选项 A: Missing usage becomes 0
- 优点: easy arithmetic.
- 缺点: falsely claims no tokens were spent.

### 选项 B: Missing usage becomes null
- 优点: honest machine-readable unknown state.
- 缺点: reports must handle null display.

### 选项 C: Estimate from elapsed time
- 优点: always produces a number.
- 缺点: false precision and impossible to audit.

## 决定

Use `null` for unknown token totals, keep best-effort transcript parsing, and register collectors on both `Stop` and `SubagentStop` with `agent_transcript_path` support.

## 权衡

Some reports will show unknown usage until platform payloads provide enough data, but they will not mislead downstream cost review.

## 影响

- 本次 sprint: CC/CX collectors and schemas now share null/unknown semantics.
- 后续 sprint: delivery reports must read `token-usage.yaml` and preserve nulls.
- architecture/: documented in `architecture/lib-athena-delivery-pack.md`.
