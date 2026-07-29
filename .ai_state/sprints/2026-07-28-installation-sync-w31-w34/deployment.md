---
sprint_slug: "2026-07-28-installation-sync-w31-w34"
status: "completed"
completed_at: "2026-07-28T14:37:30Z"
source_commit: "6bcd16c9704373b4f43da4f6ba83136cc7eb2b2d"
---

# Deployment record — W31-W34

- Source entries accounted for: 12; unique installed targets: 10; stale targets updated: 9; all 10 target hashes match the release sources after sync.
- Endpoint targets: /Users/mi_manchi/.claude and /Users/mi_manchi/.codex.
- Backup: /Users/mi_manchi/.athena/backups/athena-9.9.6-w31-w34-20260728T143730Z-7667; per-file target manifest and rollback copies retained.
- Protected-state result: Claude settings/history and Codex config/auth/history/session index/hooks JSON were unchanged; session/plugin/project directory inventories had no delta.
- Readability result: Claude history 416 rows; Codex history 150 rows; 9 SQLite quick-check results were ok; JSON/TOML and endpoint hook syntax checks passed.
- Cleanup request: _to_delete_git_debris (8 empty lock/debris files, 0 bytes) and _to_delete_k_staging (3 files, 81,656 bytes) were removed from the repository after inspection.
- Deletion safety: the executor rejected rm -rf, so both directories were moved intact into the retained backup quarantine at backup/deleted-to-delete/; repository paths are absent and recovery remains possible.

No commit, push, config overwrite, history deletion, session deletion, or plugin/database cleanup was performed.
