---
sprint_slug: "2026-07-28-installation-sync-w31-w34"
path: "System"
route_confidence: 0.97
---

# Route note — W31-W34 installation sync

## Candidates

- **System deployment (chosen):** 12 W31-W34 release-source entries span both external endpoint trees; target writes are outside the repository, so worktree isolation has no effect. Existing source commit 6bcd16c and W31-W34 smoke evidence already exist.
- **Quick:** lower ceremony, but it violates the cross-endpoint and >5-file system-scope floor.
- **Defer:** preserves state but leaves both installed gates stale, defeating the completed source work.

## Decision

Use a deployment-only System impl route with harness_target_outside_repo=true. Back up every target file before atomic replacement, preserve user-owned state, verify source/target hashes and history/database readability, then remove only the two explicitly named repository _to_delete_* directories.

## Acceptance

- W31-W34 source entries are accounted for and the unique installed targets match their release sources.
- Claude and Codex history/session/auth/config/plugin/database paths are unchanged and readable.
- Backup manifest, deployment record, deletion list and byte counts are retained.
- Any hash mismatch, config mutation, or protected-state change stops the sync and restores the backup.

## Exit point

After verification, close this deployment sprint; do not reopen the superseded prompt-engineering implementation route.
