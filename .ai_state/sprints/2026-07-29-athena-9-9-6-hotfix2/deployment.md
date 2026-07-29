---
sprint_slug: "2026-07-29-athena-9-9-6-hotfix2"
status: "completed"
completed_at: "2026-07-29T14:24:00Z"
source_commit: "77b64bbbcc018a89d649eeee503378ddc362af6a"
base_ref: "6bcd16c"
---

# Deployment record — W35-W40 installation sync

- Target roots: `/Users/mi_manchi/.claude` and `/Users/mi_manchi/.codex`.
- Candidate installation surfaces: 31; updated targets: 30. Canonical package files were used; the stale, no-consumer `_hf2_sync` mirror was removed so it cannot reintroduce an old W38 gate.
- Transaction backup: `/Users/mi_manchi/.athena/backups/athena-9.9.6-hotfix2-20260729T141144Z`; manifest and per-file rollback copies retained.
- Protected-state inventory: 2,771 files across histories, sessions, archived sessions, plugins, projects, tasks and SQLite stores. No protected file was in the write list. The active Codex session/log grew during verification; no history/session file was deleted.
- Config merge: release hook/settings wiring was applied; user-owned Claude `statusLine`/`theme`/plugin additions and Codex desktop/marketplace/project sections were retained. The hotfix removed `openai_base_url`, `model_context_window`, and `model_auto_compact_token_limit` from the live Codex config.
- Cleanup: known `.DS_Store`/`.pyc` caches were removed from release-owned trees. The executor rejects literal `rm -rf`; explicitly named `_to_delete_hf2_out` (280K, 30 files) and `_to_delete_git_debris` (0B, 4 lock remnants) were moved intact to `backup/deleted-to-delete/`, and their repository paths are absent.
- Verification: validator `66 PASS / 0 FAIL / 0 SKIP`; W35-W40 source/installed ledger PASS; metrics `verdict_ac2=PASS` (git-scale proxy); syntax, redaction, worktree boundary and SQLite checks PASS.
