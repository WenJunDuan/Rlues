# Athena 9.9.9 — CC candidate migration guide

Upgrade baseline: 9.9.8. Candidate only; prepare a preview and reviewable diff before applying. Preserve user auth, provider/base URL, model/effort/output style, permissions, plugins, third-party hooks/skills and project `.ai_state`. Never copy credentials from release assets.

## Platform selection

Use the CC package's own athena-setup entry for CC-only; follow its current SKILL.md/CLI help. Source: `vibeCoding/claude/9.9.9/.claude`. CC-only must not require a Codex installation or account. Select a second platform only when the user chooses it; detecting a CLI does not enable it.

## Managed update

1. Read the selected platform's athena-migrate skill; produce the exact managed-file preview and per-file backup before mutation.
2. Apply only selected managed assets transactionally, preserving installed user settings, third-party entries, and chat sessions (`sessions`, `history.jsonl`, `file-history`, `projects`). The review prompt is `skills/athena-review/REVIEW.md`; do not keep installing `~/.claude/REVIEW.md`. VM schema/example and `/llm-as-a-verifier` ship in the package. The fresh template inherits the effective model; this does not authorize erasing an existing model preference. Athena agents use `maxTurns: 70`; reaching the limit returns partial progress, not a PASS. Same-platform fresh/redeploy backups older than the current transaction may be listed then deleted; migrate backups are never auto-deleted. Migration merges managed deny/plugin/hook diffs; same-version reruns do not reinsert user-deleted hooks.
3. Update current release identity to 9.9.9. New index writes use cc/cx lists; legacy `["both"]` stays readable.
4. New sprints use design.md Done Contract, optional checklist, and reviews/implementation-review.md with actual run/output/packet/input bindings. Keep closed sprint history unchanged; existing results need current input validation before reuse.
5. Retired critic/evaluator/spec-compliance stay disabled; no extra review pipeline. R/S uses runtime-verify → polish → review.
6. Do not reactivate self-built token telemetry. Available native usage may be reported; unavailable usage does not block functional delivery.
7. Read back the exact installed assets, run the current package validator and selected platform smoke checks. Candidate installation is not proof of functional AC completion.

## Rollback

Use the migration transaction's per-file backup to restore the selected endpoint and matching managed files. Preserve unrelated user changes; do not mix hook versions. Restore `.ai_state` only with a matching backup when that state was actually migrated.

Functional single/dual-platform install, migration and rollback proof remains part of the 9.9.9 release acceptance. No install or publishing was performed by generating this candidate.
