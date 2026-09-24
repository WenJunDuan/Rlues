# Deployment — Athena 9.9.8 installation sync

- When: 2026-08-27T06:33:29Z
- Backup: `/Users/mi_manchi/.athena/backups/athena-9.9.8-20260827T063329Z` (257 existing files copied aside; manifest.json in backup)
- Copied: 266 release-owned files (CC hooks/agents/skills/rules/CLAUDE.md/REVIEW.md; CX hooks/agents/standards/AGENTS.md/hooks.json; CX skills → `~/.agents/skills`)
- Not touched: histories, sessions, plugins, projects, SQLite, auth
- Config merge:
  - CC `settings.json`: hooks + `VIBECODING_ATHENA_VERSION=9.9.8`; preserved `model=opus[1m]`, `effortLevel=xhigh`, user permission extras
  - CX `config.toml`: only `VIBECODING_VERSION=9.9.8`; preserved `model=gpt-5.6-sol`, `model_reasoning_effort=xhigh`, `openai_base_url`, `[desktop]`
- Verify: installed `delivery-gate.cjs/.py` sha256 match canonical 9.9.8; `~/.claude/REVIEW.md` present

## Redeploy 2026-08-27T11:02:06Z (history-preserving)

User asked to deploy 9.9.8 to both local endpoints and keep history.

- Backup: `/Users/mi_manchi/.athena/backups/athena-9.9.8-redeploy-20260827T110206Z`
- Copied: 363 release-owned files
  - CC: `~/.claude/{hooks,agents,skills,rules,CLAUDE.md,REVIEW.md}`
  - CX: `~/.codex/{hooks,agents,standards,AGENTS.md,hooks.json}`
  - CX skills: `~/.agents/skills` (canonical) and `~/.codex/skills` (leftover reader path, extras not deleted)
- Write-block list: histories, sessions, archived_sessions, projects, file-history, plugins, SQLite, auth, memories, computer-use, config.toml, settings.json
- Protected fingerprint **before == after** (`protected_changed: NONE`):
  - CC `history.jsonl` 350165 B sha `a4335c62fab8…`
  - CC `projects/` 695 files
  - CX `history.jsonl` 37162 B sha `d9fe194b5a5f…`
  - CX `sessions/` 476 files
  - CX `archived_sessions/` 45 files
  - CX `auth.json`, `session_index.jsonl`, `transcription-history.jsonl`, sqlite/memories unchanged
- User config still: CC `model=opus[1m]` `effortLevel=xhigh`; CX `gpt-5.6-sol` `model_reasoning_effort=xhigh` + `openai_base_url`
