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

Claude Code uses `best`, root `xhigh`, role-owned subagent models, the Fable pin,
privacy, attribution and installation-check choices, and a 600-second API
timeout. Dated Opus/Sonnet pins and the global subagent override are not
restored; Tool Search remains on by platform default. The local proxy overlay is
opt-in. Existing user permission and gateway choices win during migration.

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
