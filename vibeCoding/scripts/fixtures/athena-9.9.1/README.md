# Athena 9.9.1 release fixtures

These fixtures are executable contracts for `validate-athena-9.9.1.py`.

## PostToolUse evidence outcomes

Only a top-level JSON integer (not boolean) `tool_response.exit_code` is reliable:

| Fixture | Outcome | Contract |
|---|---|---|
| `posttool-exit-zero.json` | `pass` | integer `0` |
| `posttool-exit-seven.json` | `fail` | non-zero integer |
| `posttool-string.json` | `unknown` | string response; prose is not parsed for an exit status |
| `posttool-string-exit-code.json` | `unknown` | string exit code is not a reliable integer |

Missing, boolean, nested-only, or otherwise untyped exit status is also `unknown`; `unknown` never upgrades to `pass`.

## Subagent ledger schemas

The two JSONL files use different strict schema-v1 records:

- Raw native event, `subagent-events.jsonl`: `schema_version`, `event`, `agent_id`, `agent_type`, `sprint_slug`, `timestamp`.
- Main-thread assignment, `subagent-assignments.jsonl`: `schema_version`, `agent_id`, `task_name`, `role`, `sprint_slug`, `timestamp`.

The gate joins them only by `agent_id + sprint_slug`. A generator requires one unambiguous `SubagentStart`, a matching latest `SubagentStop`, completed checklist tasks, non-empty passing evidence, and final review `VERDICT: PASS`. A Start alone never completes work.

## Gate cases

Only `complete-chain` may pass. When `current_roadmap_slug` is non-empty, its
`items.yaml` must parse successfully and every declared item must have exactly
one `status: completed`; missing, malformed, pending, in-progress, blocked, or
unknown states block ship. The gate selects the highest numeric
`reviews/passN.md`; an older PASS cannot
override a newer REWORK. All 21 negatives in `gate-cases.json` must block:

1. `missing-assignment`
2. `missing-generator-stop`
3. `agent-id-mismatch`
4. `checklist-incomplete`
5. `evidence-empty`
6. `evidence-unknown-only`
7. `evidence-fail`
8. `review-without-final-pass`
9. `latest-review-rework`
10. `malformed-jsonl`
11. `ambiguous-start`
12. `unbound-start`
13. `isolated-stop`
14. `orphan-stop`
15. `stop-before-assignment`
16. `roadmap-pending`
17. `roadmap-in-progress`
18. `roadmap-malformed`
19. `missing-index`
20. `malformed-index`
21. `unknown-stage`

## Setup and migration

- Setup: the five states in `setup-states.json` are mandatory, and repository-root discovery must include `vibeCoding/{claude,codex}/9.9.1`.
- Migration executable contract: `migrate-9.9.0-to-9.9.1.py --home HOME --repo-root ROOT [--only cc|cx|both] [--dry-run] [--backup-dir DIR]`. It preflights both endpoints, creates one transaction backup, merges only Athena-owned config/hooks, synchronizes release assets, preserves private hooks and third-party/user fields, rolls back all selected endpoints on injected failure, and is idempotent.
