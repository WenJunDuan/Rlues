# Athena 9.9.6 — DRAFT AI migration guide

> DRAFT only. This adapter is not released. Do not publish it or describe the
> deferred runtime, invocation, migration, rollback, or A/B suites as passing.

## Fresh install

Install the endpoint directory that matches the host:

- Claude Code: `vibeCoding/claude/9.9.6/.claude`
- Codex: `vibeCoding/codex/9.9.6/.codex`

Preserve user-owned authentication, permissions, sandbox choices, gateway or
base URL, plugin choices, and project `.ai_state`. Never copy credentials from
the release tree.

## Upgrade from 9.9.3

1. Back up the existing endpoint directory and `.ai_state` before writing.
2. Compare the installed 9.9.3 defaults with the 9.9.6 adapter.
3. Apply release-owned prompt, agent, skill, hook, and standard files.
4. Merge configuration only where the installed value still equals the 9.9.3
   default. Preserve user-owned permission, sandbox, plugin, authentication,
   gateway, and base-URL choices.
5. Set the endpoint version marker to `9.9.6` and validate syntax before any
   cleanup.

Claude Code keeps the main session on the official `best` alias, which currently
resolves to `opus`. The release sets no global subagent model override:
`CLAUDE_CODE_SUBAGENT_MODEL` outranks agent frontmatter, so shipping it would
disable the role matrix. Role model and effort live in frontmatter --
`architect`/`critic` on `fable`; `evaluator`/`generator`/`reviewer`/
`spec-compliance`/`polish-worker` on `opus`.
`ANTHROPIC_DEFAULT_FABLE_MODEL` is pinned only so the `fable` alias resolves.
`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` ships as a privacy-conservative
default; migration preserves an existing user value instead of overwriting it.
It uses `default` as the fresh-template permission mode, restores root `xhigh`,
the Fable alias pin, attribution, installation-check and privacy choices, and
sets API timeout to the current 600-second default. Dated Opus/Sonnet pins stay
unset and default-on Tool Search is not repeated. `settings.proxy.json` carries
the optional local 6152/6153 proxy and is inactive unless passed with
`claude --settings`; migration preserves existing gateway and permission choices.

Codex uses the built-in `openai` provider and `gpt-5.6-sol`. ChatGPT login and
OpenAI API keys use that provider. The fresh template omits `openai_base_url`
so the built-in provider selects its official endpoint; migration preserves an
existing non-empty gateway/base URL and never copies credentials.

## Rollback

Restore the backup as one unit. Do not partially mix 9.9.3 and 9.9.6 endpoint
files. Keep project `.ai_state` unless a separately validated migration changed
it; this bottom draft does not authorize such a migration.

## Deferred validation

Before release, the final sprint must run exact-version CLI/App smoke tests,
skill invocation tests, bounded state recovery, migration/rollback, N9/N10,
and N≥3 prompt A/B evaluation. None of those results is claimed here.
