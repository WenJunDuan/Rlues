# Athena 9.9.6 local draft deployment

- Started (UTC): 2026-07-25T08:31:09Z
- Status: pre-write checkpoint; release-owned migration is authorized by the user, while upstream release status remains `reviewable draft / not released`.
- Source: `vibeCoding/claude/9.9.6/.claude` and `vibeCoding/codex/9.9.6/.codex`
- Targets: `/Users/mi_manchi/.claude` and `/Users/mi_manchi/.codex`
- Backup: `/Users/mi_manchi/.athena/backups/athena-9.9.6-20260725T083109Z`
- Backup manifest: `/Users/mi_manchi/.athena/backups/athena-9.9.6-20260725T083109Z/BACKUP-MANIFEST.json`
- Package gate: `python3 vibeCoding/scripts/validate-athena-9.9.6.py --repo .` → `76 PASS / 0 WARN / 0 FAIL`
- Runtime gate: not run; the package release documents exact-version CLI/App and prompt A/B validation as deferred.
- Preservation boundary: authentication, history, sessions, SQLite/state databases, project `.ai_state`, permissions, plugins, gateway/base URL, desktop/MCP settings, and unknown user files are retained unless explicitly classified as release-owned.
- Cleanup boundary: only disposable cache/junk paths will be considered after post-install verification; no history, database, auth, project-state, or configuration path is eligible for deletion.

## Result

- Completed (UTC): 2026-07-25T08:39:00Z
- CC/CX managed assets: installed and hash-verified against the 9.9.6 source tree.
- CC/CX version markers: `9.9.6`.
- CX skills: 26 release skills installed under `/Users/mi_manchi/.agents/skills`; legacy `/Users/mi_manchi/.codex/skills` retained unchanged, including the user `chronicle` skill.
- User data checks: CC/CX history JSONL parsed successfully (285/147 records); Codex goals, memories, state, and logs SQLite quick checks returned `ok`.
- Syntax checks: CC CJS 18/18; CX Python 21/21; JSON/TOML valid.
- Static package gate: `76 PASS / 0 WARN / 0 FAIL`.
- CLI compatibility: Codex `0.145.0`; CC `2.1.211`, below the draft's stated `2.1.219+` target. Running `claude --version` on this older CC normalized settings once; the validated 9.9.6 CC settings (including 15 deny rules) were restored afterward. Do not treat this as runtime validation.
- Cleanup: 11 disposable cache/junk items moved, 4,701,203 bytes; manifest: `/Users/mi_manchi/.athena/backups/athena-9.9.6-20260725T083109Z/cleanup-quarantine-20260725T083109Z/CLEANUP-MANIFEST.json`.
- Retained live/valuable paths: `.codex/tmp`, `.codex/.tmp`, plugin materializations, history/session archives, shell snapshots, downloads, paste cache, auth, and all SQLite/state files.
- Final status: local draft deployment complete; upstream 9.9.6 release and exact-version runtime/A-B validation remain deferred.
- Backup disposition (2026-07-25T08:46:08Z): at the user's request, the migration snapshot `/Users/mi_manchi/.athena/backups/athena-9.9.6-20260725T083109Z` and its cleanup quarantine were permanently deleted after the installed CC/CX version checks passed. No other backup root was targeted; rollback from this snapshot is no longer available.

## Migration rule

Release-owned prompt, agent, hook, rule/standard, and skill assets will be updated from the 9.9.6 package. Configuration is merged only where the installed value still matches the 9.9.3 release default; user-owned drift is preserved. If a write or verification fails, restore each endpoint from the backup as a unit and leave project `.ai_state` intact.
