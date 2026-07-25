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

Claude Code keeps the main session on the official `best` alias, which currently
resolves to `opus`. The release sets no global subagent model override:
`CLAUDE_CODE_SUBAGENT_MODEL` outranks agent frontmatter, so shipping it would
disable the role matrix. Role model and effort live in frontmatter --
`architect`/`critic` on `fable`; `evaluator`/`generator`/`reviewer`/
`spec-compliance`/`polish-worker` on `opus`.
`ANTHROPIC_DEFAULT_FABLE_MODEL` is pinned only so the `fable` alias resolves.
`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` ships as a privacy-conservative
default; migration preserves an existing user value instead of overwriting it.
It uses the fresh-template `default` permission mode, restores root `xhigh`,
the Fable alias pin, attribution, installation-check and privacy choices, and
sets API timeout to the current 600-second default. Dated Opus/Sonnet pins stay
unset and default-on Tool Search is not repeated. `settings.proxy.json` carries
the optional local 6152/6153 proxy and is inactive unless passed with
`claude --settings`; migration preserves existing gateway and permission choices.

Codex uses the built-in `openai` provider and `gpt-5.6-sol`. The fresh template
exposes `openai_base_url=https://api.openai.com/v1`; migration preserves an
existing gateway and never copies credentials.

## Rollback and validation

Restore the backup as one unit; do not mix endpoint versions. The final release
must still prove exact-version CLI/App behavior, controlled skill invocation,
bounded state recovery, migration/rollback, N9/N10, and N≥3 A/B evaluation.
