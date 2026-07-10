---
name: athena-setup
description: Fresh-install Athena v9.9.1 globally, install a missing Claude Code or Codex endpoint, or verify an existing v9.9.1 installation. Use for first-time global setup; route older installations to athena-migrate instead of overwriting them.
---

# Athena setup v9.9.1

Run the bundled installer. It evaluates Claude Code (CC) and Codex (CX) independently.
The repository distribution pair is `vibeCoding/claude/9.9.1/.claude` and
`vibeCoding/codex/9.9.1/.codex`.

```bash
# From the Rlues repository root: inspect first, then install.
python3 vibeCoding/codex/9.9.1/.codex/skills/athena-setup/scripts/setup-athena.py \
  --repo-root "$PWD" --dry-run
python3 vibeCoding/codex/9.9.1/.codex/skills/athena-setup/scripts/setup-athena.py \
  --repo-root "$PWD"
```

Use `--only cc` or `--only cx` for one endpoint. Outside the repository, pass
`--cc-package <path-to-.claude>` / `--cx-package <path-to-.codex>`, or set
`ATHENA_CC_PKG` / `ATHENA_CX_PKG`.

## State policy

| Endpoint state | Action |
|---|---|
| `fresh` | Preflight every managed destination, then install selected missing endpoints transactionally |
| `CC-only` | Install only CX; leave CC untouched |
| `CX-only` | Install only CC; leave CX untouched |
| `same-version` | Verify files, dynamic package counts, version, and CX skill paths; never overwrite |
| `old-version` | Route that endpoint to `/athena-migrate`; another selected fresh endpoint may still install |
| Existing unversioned or invalid config | Refuse to overwrite; require an explicit merge decision |

The installer reports paths and counts only. It never prints user configuration values.

## Installed assets

- CC: `~/.claude/settings.json`, `CLAUDE.md`, status line, rules, hooks, agents, and skills.
- CX: `~/.codex/config.toml`, `hooks.json`, `AGENTS.md`, hooks, agents, and standards.
- CX skills: `~/.agents/skills/<name>/SKILL.md`. Codex keeps `$CODEX_HOME/skills`
  only as deprecated backward compatibility; the user-level standard is
  `$HOME/.agents/skills` ([Codex 0.144.1 loader source](https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337)).

Asset counts come from the selected package at runtime. Do not encode release counts in this skill.
For the fresh CX endpoint, the installer collision-checks and atomically installs the packaged
`AGENTS.md`; do not copy it manually against an existing endpoint.

## Safety boundaries

- Setup is fresh-only. Never copy a whole release config over an installed config.
- Fresh selected endpoints are staged as one transaction. A config-write or asset-copy failure
  removes every file created by that transaction; exit code `3` is reserved for incomplete cleanup.
- Generated package junk (`__pycache__`, `*.pyc`, `.DS_Store`, and `tmp/`) is excluded from the
  runtime manifest.
- Do not modify provider, MCP, project, desktop, plugin, permission, or unknown user fields.
- Do not delete `~/.codex/skills` or `~/.agents/skills`. Migration may remove only legacy
  `~/.codex/skills/<name>` paths that the old Athena config explicitly registered.
- Do not read, write, or bypass Codex's hook trust store. Hook content changes can require the
  user to review and trust them again in Codex; report that fact after installation.
- Treat a verification mismatch as drift to review, not permission to repair automatically.

## Verification

Run the same command again. A same-version run is read-only and exits successfully only when
all packaged assets exist, hashes match, the version marker is `9.9.1`, and CX skill entries no
longer point at `~/.codex/skills`.

```bash
python3 vibeCoding/codex/9.9.1/.codex/skills/athena-setup/tests/test_setup_991.py
```
