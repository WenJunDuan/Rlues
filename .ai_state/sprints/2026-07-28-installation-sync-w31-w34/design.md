---
sprint_slug: "2026-07-28-installation-sync-w31-w34"
path: "System"
created: "2026-07-28"
document_status: "completed"
implementation_authorized: false
git_commit_authorized: false
roadmap_slug: ""
---

# Design — W31-W34 installation sync

## Outcome

Synchronize the already committed W31-W34 prompt and gate changes from the 9.9.6 release sources into the two live endpoint trees. This sprint does not alter source code, user configuration, credentials, sessions, history, databases, plugins, or project state.

## Acceptance Criteria

- AC1: The 12 W31-W34 source entries are accounted for; every unique target under /Users/mi_manchi/.claude or /Users/mi_manchi/.codex matches its release-source SHA-256 after sync.
- AC2: Claude history.jsonl, Codex history.jsonl, session directories, auth/config files, plugin trees, and SQLite files exist as before; history JSONL remains parseable and SQLite quick_check remains ok.
- AC3: A timestamped per-file backup and deployment record exist before writes; a protected-state manifest proves config and history hashes are unchanged.
- AC4: Only the explicitly named repository directories _to_delete_git_debris and _to_delete_k_staging are deleted after content inspection; their paths and byte counts are recorded.
- AC5: Post-sync syntax and smoke checks pass for both endpoint hook copies, and a rollback path remains available until verification completes.

## Done Contract

All acceptance criteria are verified from the deployment record. On any mismatch, restore the per-file backup and stop without deleting protected state.
