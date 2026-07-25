# Athena 9.9.6 — DRAFT AI migration guide

> Not released. Do not claim deferred runtime, migration, rollback, invocation,
> or A/B suites passed.

## Install or upgrade

Use `vibeCoding/claude/9.9.6/.claude` for Claude Code and
`vibeCoding/codex/9.9.6/.codex` for Codex. Before writing, back up the installed
endpoint and `.ai_state`. Apply release-owned prompt, role, skill, hook, and
standard files; merge configuration only when the installed value still equals
the 9.9.3 default.

Preserve user permissions, sandbox choices, authentication, credentials,
plugins, gateway/base URL, and project state. Never place credentials in the
release tree.

Claude Code uses `best`, root `xhigh`, role-owned subagent models, the Fable pin,
privacy, attribution and installation-check choices, and a 600-second API
timeout. Dated Opus/Sonnet pins and the global subagent override are not
restored; Tool Search remains on by platform default. The local proxy overlay is
opt-in. Existing user permission and gateway choices win during migration.

Codex uses the built-in `openai` provider and `gpt-5.6-sol`. The fresh template
exposes `openai_base_url=https://api.openai.com/v1`; migration preserves an
existing gateway and never copies credentials.

## Rollback and validation

Restore the backup as one unit; do not mix endpoint versions. The final release
must still prove exact-version CLI/App behavior, controlled skill invocation,
bounded state recovery, migration/rollback, N9/N10, and N≥3 A/B evaluation.
