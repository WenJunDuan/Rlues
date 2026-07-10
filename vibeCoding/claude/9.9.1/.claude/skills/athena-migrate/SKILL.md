---
name: athena-migrate
description: Upgrade an existing Athena installation with backup, targeted config migration, asset synchronization, rollback safety, and post-migration verification. Use for Athena v9.9.0 to v9.9.1 upgrades; never use fresh setup to overwrite an older installation.
---

# Athena migrate v9.9.1

Current automated path: `9.9.0 → 9.9.1`. Every selected endpoint must already be `9.9.0` or
`9.9.1`; a missing endpoint belongs to `/athena-setup`. All selected `9.9.0` endpoints share one
backup and rollback transaction, while a selected `9.9.1` endpoint is verification-only.

## 1. Preflight and backup

1. Locate release packages from the repository root:
   `vibeCoding/claude/9.9.1/.claude` and `vibeCoding/codex/9.9.1/.codex`.
2. Parse installed configs without printing them:
   - CC marker: `~/.claude/settings.json` → `env.VIBECODING_ATHENA_VERSION`.
   - CX marker: `~/.codex/config.toml` →
     `shell_environment_policy.set.VIBECODING_VERSION`.
3. Refuse unsupported or invalid versions. Do not infer ownership from directory presence alone.
4. Create a timestamped backup outside the release package. Back up every managed destination
   before replacement; never delete backups automatically.

## 2. Migrate CX config atomically

Inspect both selected endpoints first, then apply:

```bash
MIGRATE=vibeCoding/codex/9.9.1/.codex/skills/athena-migrate/scripts/migrate-9.9.0-to-9.9.1.py
python3 "$MIGRATE" --repo-root "$PWD" --home "$HOME" --dry-run
python3 "$MIGRATE" --repo-root "$PWD" --home "$HOME" \
  --backup-dir ~/.athena-backups/9.9.1-transaction
```

Use `--only cc` or `--only cx` for one endpoint. Outside the repository pass `--cc-package` and
`--cx-package`. The script completes a zero-target-write preflight, stages and parses generated
configs, backs up every changed/deleted destination before the first replacement, fsyncs config
temporary files, and replaces them atomically. A second successful run verifies only and creates
no backup.

Its write boundary is deliberately narrow:

- Change the old Athena defaults only when they still equal the v9.9.0 defaults: built-in
  provider/model selection, obsolete 1M/900k context overrides, and the Athena version marker.
- Remove the stale `gpt-5.5` model-availability NUX entry in that default state. Remove the
  `custom_openai` provider table only when its complete key/value set exactly matches the v9.9.0
  template; preserve the table when it contains a user URL or any extra key.
- Rewrite release-managed `[[skills.config]]` entries from `~/.codex/skills/<name>` to
  `~/.agents/skills/<name>` and add release-managed entries missing from the v9.9.0 registry.
- Preserve custom providers with a configured URL, third-party skill entries, MCP servers,
  projects, desktop settings, plugins, and unknown tables. Logs contain counts and paths, never
  config values or secrets.

Codex 0.144.1 treats `$CODEX_HOME/skills` as deprecated compatibility and loads user skills from
`$HOME/.agents/skills` ([official source](https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337)).

## 3. Merge config-bearing JSON; do not replace it wholesale

- CC `settings.json`: update only `env.VIBECODING_ATHENA_VERSION` and individual hooks whose
  standard-directory filename is in the release package's exact `.claude/hooks` allowlist.
- CX `hooks.json`: apply the same per-hook rule using the release package's exact `.codex/hooks`
  filename allowlist. A private command merely living under either standard hooks directory is
  not Athena-owned. Preserve private hooks inside mixed groups, non-Athena events/groups, user
  model choices, permissions, plugins, environment entries, status line, unknown fields, and
  existing order where possible; then install the release Athena hooks.
- Parse the merged JSON in a temporary file before atomic replacement. Never echo either JSON
  document to the transcript.

## 4. Synchronize release-owned assets

Compute manifests from the package at runtime; do not hard-code counts.

- CC: synchronize package-named rules, hooks, agents, and skill directories. Preserve extra
  third-party names.
- CX: synchronize package-named hooks, agents, standards, and `AGENTS.md`; install package skill
  directories at `~/.agents/skills/<name>`. Preserve extra third-party names.
- Before CX config migration, record exact old `[[skills.config]].path` values. After the new
  copies validate, remove recorded paths under `~/.codex/skills/<release-managed-name>`.
  v9.9.0 omitted `augment` from its config registry despite shipping the directory: when the
  v9.9.0 package is locatable, an unregistered release-managed directory is also removable only
  when its complete relative-path/file-hash signature exactly matches the v9.9.0 counterpart.
  A missing counterpart, changed file, symlink, or extra entry is preserved and reported as
  `legacy residue`. Never remove the whole `~/.codex/skills` or `~/.agents/skills` tree.

Do not read, edit, or bypass the Codex hook trust store. Content changes may trigger a new trust
review in Codex; report that to the user.

## 5. Verify and roll back on failure

Verify all of the following before reporting completion:

- Both configs parse and report `9.9.1`; CX model/default changes match the migration plan.
- Provider, MCP, project, desktop, plugin, and unknown-table fixtures remain semantically or
  byte-for-byte unchanged.
- Every configured Athena skill resolves under `~/.agents/skills`; third-party skill entries
  keep their original paths.
- The plan reports both safe `legacy` deletions and preserved `residue` paths; an exact omitted
  v9.9.0 `augment` copy is deleted, while a modified same-name directory remains untouched.
- Package-derived counts match installed release-owned rules/hooks/agents/standards/skills.
- All copied Python/JSON/TOML release files pass syntax parsing; release validation runs the
  official skill validator separately.
- A second migration run reports no changes and creates no new backup.

Bundled regression tests cover dry-run, real migration, idempotence, protected user config, and
invalid-input rollback:

```bash
python3 vibeCoding/codex/9.9.1/.codex/skills/athena-migrate/tests/test_migrate_991.py
```

If any write or post-copy check fails, restore every selected endpoint and every newly created
path. Exit code `3` is reserved for an incomplete rollback; a refused migration or fully rolled
back failure exits `2`. Never report a partial endpoint as upgraded.

## Legacy migrations

The historic `9.6.2 → 9.6.4` state-layout migration remains destructive because `details/` and
`lessons.md` require user choices. Do not fold it into this unattended script. Obtain explicit
user selection, retain its full `.ai_state` backup, finish that migration first, and advance
through intermediate release packages before running `9.9.0 → 9.9.1`.
