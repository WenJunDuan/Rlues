---
date: "2026-09-07"
path: "System"
confidence: 0.99
scope: "local CC/CX 9.9.9 migration"
---
# Local installation exception

The requested targets are the user-level `~/.claude`, `~/.codex`, and
`~/.agents` harness paths rather than repository files. A Git worktree cannot
isolate them, so one bound generator performs the installer transaction and
safe cache cleanup serially. The installer preserves session/history paths,
creates a per-file transaction backup, and the user authorized removal of that
backup only after successful verification.
