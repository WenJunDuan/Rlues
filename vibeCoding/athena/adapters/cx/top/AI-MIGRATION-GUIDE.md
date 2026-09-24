# Athena 9.9.9 — CX candidate migration guide

Upgrade baseline: 9.9.8. Candidate only; prepare a preview and reviewable diff before applying. Preserve user auth, provider/base URL, model/effort, permissions, plugins, third-party hooks/skills and project `.ai_state`. Never copy credentials from release assets.

## Platform selection

Use the CX package's own athena-setup entry for CX-only; follow its current SKILL.md/CLI help. Source: `vibeCoding/codex/9.9.9/.codex`. CX-only must not require a Claude Code installation or account. Select a second platform only when the user chooses it; detecting a CLI does not enable it.

```
python3 vibeCoding/codex/9.9.9/.codex/skills/athena-setup/scripts/setup-athena.py \
  --repo-root "$PWD" --only cx --dry-run
python3 vibeCoding/codex/9.9.9/.codex/skills/athena-setup/scripts/setup-athena.py \
  --repo-root "$PWD" --only cx --migrate
```

Skills install to `~/.agents/skills`. Codex `$CODEX_HOME/skills` is deprecated compatibility only.

## Managed update

1. Read the selected platform's athena-migrate skill; produce the exact managed-file preview and per-file backup before mutation.
2. Apply only selected managed assets transactionally, preserving installed user settings, third-party entries, and chat sessions (`sessions`, `archived_sessions`, `history.jsonl`). The review prompt is `skills/athena-review/REVIEW.md`. VM schema/example and `/llm-as-a-verifier` ship in the package. Agents follow a 70-turn instruction budget; Codex currently has no native turn-limit setting. At the limit, return partial progress without claiming PASS. Same-platform fresh/redeploy backups older than the current transaction may be listed then deleted; migrate backups are never auto-deleted. Migration merges managed deny/plugin/hook diffs; same-version reruns do not reinsert user-deleted hooks.
3. Update current release identity to 9.9.9. New index writes use cc/cx lists; legacy `["both"]` stays readable.
4. New sprints use design.md Done Contract, optional checklist, and reviews/implementation-review.md with actual run/output/packet/input bindings. Keep closed sprint history unchanged.
5. Retired critic/evaluator/spec-compliance stay disabled. R/S uses runtime-verify → polish → review.
6. Do not reactivate self-built token telemetry. Unavailable usage does not block functional delivery.
7. Read back the exact installed assets, run `python3 vibeCoding/scripts/validate-athena-9.9.9.py`. Candidate installation is not proof of functional AC completion.

## Rollback

Use `--rollback ~/.athena/backups/<id>`. Preserve unrelated user changes; do not mix hook versions.

Functional single/dual-platform install, migration and rollback proof remains part of the 9.9.9 release acceptance. No install or publishing was performed by generating this candidate.
