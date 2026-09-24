# Athena 9.9.8 — AI migration guide

Upgrade from 9.9.6. Preserve user-owned auth, permissions, sandbox, gateway/base URL, plugins, model/effort/output-style, and project `.ai_state`. Never copy credentials from the release tree.

## Fresh install

- Claude Code: `vibeCoding/claude/9.9.8/.claude`
- Codex: `vibeCoding/codex/9.9.8/.codex`

```
python3 vibeCoding/codex/9.9.8/.codex/skills/athena-setup/scripts/setup-athena.py \
  --home "$HOME" --repo-root <Rlues> --only both
```

`permissions.defaultMode` stays `default`; Claude Code 2.1.200+ also accepts `manual` as a `default` alias. Migration preserves the installed value.

## Upgrade from 9.9.6

1. Back up `~/.claude`, `~/.codex`, and `.ai_state`.
2. Apply release-owned prompts, agents, skills, hooks, `REVIEW.md`, and templates.
3. Merge config only where the installed value still equals the 9.9.6 default. **Do not overwrite** user `model`, `model_reasoning_effort`, `effortLevel`, or output style.
4. Set version markers to `9.9.8` (`VIBECODING_ATHENA_VERSION` / `VIBECODING_VERSION`).
5. Sprint artifacts: `reviews/passN.md` is no longer the ship subject. New sprints write `reviews/implementation-review.md` with `review_run_id` + `native_output_ref`. Existing closed sprints stay in place; do not rewrite history.
6. `critic` / `evaluator` / `spec-compliance` are stubs. Do not spawn them. One native review request; `next_action=await-review-result` while it is in flight.
7. Telemetry: copy any still-needed `token-usage.yaml` / `tool-trace.jsonl` aside, then stop tracking them (`git rm --cached`). Runtime files live in `.ai_state/.runtime/` (gitignored). Frozen AC11 baseline is `.ai_state/.runtime/baseline/` and is retention-exempt.
8. Validate: `python3 vibeCoding/scripts/validate-athena-9.9.8.py`

## Rollback

Restore the 9.9.6 endpoint backup as one unit. Do not mix 9.9.6 and 9.9.8 hook files. Keep `.ai_state` unless you also restore a matching backup.

## Deferred

AC11 representative-task token eval (control-plane ↓≥40%) is a ship gate, not claimed by install.
