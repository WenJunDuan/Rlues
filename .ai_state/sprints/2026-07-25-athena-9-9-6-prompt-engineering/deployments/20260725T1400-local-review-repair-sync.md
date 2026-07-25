# Athena 9.9.6 review-repair sync

- Scope: direct sync into the existing user endpoints; no worktree.
- Source: `vibeCoding/claude/9.9.6` and `vibeCoding/codex/9.9.6`.
- CC managed files synchronized: 127; CX managed files: 33; CX skills: 97.
- Claude settings were merged field-by-field: release hooks and bounded `npx` permissions were updated; user-owned fields were retained.
- Codex `~/.codex/config.toml` was not rewritten. Its built-in `openai` provider and existing nonempty gateway remained unchanged.
- User data preservation checks: 2 JSONL history files, 436 rows parsed; 9 SQLite databases passed `quick_check`.
- Post-sync checks: CC version `9.9.6`; unsafe unbounded `npx` entries absent; CX spawn guard and worktree audit present; managed hashes matched (256).
- Backup: full endpoint backup was created at `~/.athena/backups/athena-9.9.6-review-repair-20260725T142614Z`, used for rollback protection, then deleted only after all checks passed. No rollback snapshot remains.
- The package fresh config now omits `openai_base_url`; the installed user gateway was preserved.
