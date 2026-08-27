# Athena Claude Code 9.9.8

Status: implementation in progress. Baseline: 9.9.6-hotfix2.

Thin PACE control plane: one native async review, derived review-packet, hook red/yellow/green, bounded `_index`, telemetry off Git. VM and LLM-as-a-Verifier remain opt-in slots.

Platform: Claude Code 2.1.231+ measured; `/code-review` is a background subagent since 2.1.221; `/review` is its alias since 2.1.223. `permissions.defaultMode` stays `default`; Claude Code 2.1.200+ also accepts `manual` as a `default` alias.

Migration never overwrites user model/effort/output-style.
