#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import types
import unittest


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/migrate-9.9.0-to-9.9.1.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures/migrate-user-config.toml"
REAL_FIXTURE = Path(__file__).resolve().parent / "fixtures/real-9.9.0-config.toml"


def repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "vibeCoding/codex/9.9.0/.codex/config.toml").is_file():
            return candidate
    raise RuntimeError("repository root not found")


ROOT = repository_root()
OLD_CC = ROOT / "vibeCoding/claude/9.9.0/.claude"
OLD_CX = ROOT / "vibeCoding/codex/9.9.0/.codex"


def load_module():
    spec = importlib.util.spec_from_file_location("athena_migrate_991", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MIGRATE = load_module()


def argparse_namespace(**kwargs: object) -> types.SimpleNamespace:
    """Minimal stand-in for argparse.Namespace covering the attributes
    locate_package()/package_candidates() read (cc_package/cx_package/
    repo_root/only); tests only need to drive package discovery, not the
    full CLI surface."""
    defaults = {"cc_package": None, "cx_package": None, "repo_root": None, "only": "both"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def digest_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def copy_clean(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if MIGRATE.is_junk(relative):
            continue
        if path.is_file():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def prepare_old_home(home: Path) -> None:
    cc = home / ".claude"
    cx = home / ".codex"
    cc.mkdir(parents=True)
    cx.mkdir(parents=True)

    settings = json.loads((OLD_CC / "settings.json").read_text(encoding="utf-8"))
    settings["model"] = "user-choice"
    settings["env"]["PRIVATE_TOKEN"] = "do-not-log"
    settings["unknown_user_key"] = {"keep": True}
    settings["hooks"].setdefault("PostToolUse", []).insert(
        0,
        {
            "matcher": "Custom",
            "hooks": [{"type": "command", "command": "/opt/private/hook"}],
        },
    )
    cc_bash = next(
        group
        for group in settings["hooks"]["PostToolUse"]
        if group.get("matcher") == "Bash"
    )
    cc_bash["user_group_field"] = "keep-cc-group"
    cc_bash["hooks"].append(
        {
            "type": "command",
            "command": "node ~/.claude/hooks/private-third-party.cjs",
            "user_hook_field": "keep-cc-hook",
        }
    )
    settings["hooks"]["PrivateEvent"] = [
        {
            "matcher": "Private",
            "hooks": [
                {
                    "type": "command",
                    "command": "node ~/.claude/hooks/private-third-party.cjs",
                }
            ],
        }
    ]
    (cc / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    for name in ("CLAUDE.md", "statusline-command.sh", "rules", "hooks", "agents", "skills"):
        source = OLD_CC / name
        destination = cc / name
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            copy_clean(source, destination)

    config = (OLD_CX / "config.toml").read_text(encoding="utf-8").replace(
        "<USER_HOME>", home.as_posix()
    )
    config += f'''\n[[skills.config]]
path = "{home.as_posix()}/.codex/skills/private-customer-skill/SKILL.md"
enabled = true

[mcp_servers.private]
command = "private-command"
token_env = "PRIVATE_TOKEN"

[unknown.private]
keep = true
'''
    (cx / "config.toml").write_text(config, encoding="utf-8")
    hooks = json.loads((OLD_CX / "hooks.json").read_text(encoding="utf-8"))
    hooks["unknown"] = {"keep": True}
    hooks["hooks"].setdefault("PostToolUse", []).insert(
        0,
        {
            "matcher": "Custom",
            "hooks": [{"type": "command", "command": "/opt/private/hook"}],
        },
    )
    hooks["hooks"]["PostToolUse"].insert(
        0,
        {
            "matcher": "Bash|apply_patch|MCP|mcp__.*",
            "user_group_field": "keep-cx-group",
            "hooks": [
                {
                    "type": "command",
                    "command": "/usr/bin/env python3 ~/.codex/hooks/subagent-retry.py",
                },
                {
                    "type": "command",
                    "command": "/usr/bin/env python3 ~/.codex/hooks/private-third-party.py",
                    "user_hook_field": "keep-cx-hook",
                },
            ],
        },
    )
    hooks["hooks"]["PrivateEvent"] = [
        {
            "matcher": "Private",
            "hooks": [
                {
                    "type": "command",
                    "command": "/usr/bin/env python3 ~/.codex/hooks/private-third-party.py",
                }
            ],
        }
    ]
    (cx / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n", encoding="utf-8")
    for name in ("AGENTS.md", "hooks", "agents", "standards"):
        source = OLD_CX / name
        destination = cx / name
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            copy_clean(source, destination)
    copy_clean(OLD_CX / "skills", cx / "skills")

    private_skill = cx / "skills/private-customer-skill/SKILL.md"
    private_skill.parent.mkdir(parents=True)
    private_skill.write_text("private\n", encoding="utf-8")
    (cx / "hooks/private-third-party.py").write_text("# preserve\n", encoding="utf-8")
    (cc / "hooks/private-third-party.cjs").write_text("// preserve\n", encoding="utf-8")


class TransformerTests(unittest.TestCase):
    def transform(self, source: str) -> tuple[str, dict[str, int]]:
        parsed = tomllib.loads(source)
        order = MIGRATE.managed_skill_order(ROOT / "vibeCoding/codex/9.9.1/.codex")
        return MIGRATE.migrate_text(source, parsed, "/Users/example/.agents/skills", order)

    def test_defaults_nux_provider_and_protected_tables(self) -> None:
        original = REAL_FIXTURE.read_text(encoding="utf-8")
        migrated, stats = self.transform(original)
        parsed = tomllib.loads(migrated)
        self.assertEqual(parsed["model_provider"], "openai")
        self.assertEqual(parsed["model"], "gpt-5.6-sol")
        self.assertNotIn("model_context_window", parsed)
        self.assertNotIn("model_auto_compact_token_limit", parsed)
        self.assertNotIn("custom_openai", parsed.get("model_providers", {}))
        self.assertNotIn("model_availability_nux", parsed.get("tui", {}))
        self.assertEqual(stats["provider_tables_removed"], 1)
        self.assertEqual(stats["nux_entries_removed"], 1)

    def test_configured_provider_and_user_nux_are_preserved(self) -> None:
        source = FIXTURE.read_text(encoding="utf-8").replace(
            'base_url = ""', 'base_url = "https://gateway.invalid/v1"'
        )
        migrated, _ = self.transform(source)
        parsed = tomllib.loads(migrated)
        self.assertEqual(parsed["model_provider"], "custom_openai")
        self.assertEqual(parsed["model"], "gpt-5.5")
        self.assertEqual(
            parsed["model_providers"]["custom_openai"]["base_url"],
            "https://gateway.invalid/v1",
        )
        self.assertEqual(
            parsed["model_providers"]["custom_openai"]["user_note"],
            "preserve-extra-provider-key",
        )

    def test_extended_template_provider_and_private_nux_keep_extra_fields(self) -> None:
        source = REAL_FIXTURE.read_text(encoding="utf-8")
        source = source.replace('"gpt-5.5" = 4', '"gpt-5.5" = 4\n"gpt-private" = 7')
        source = source.replace(
            "requires_openai_auth = true",
            'requires_openai_auth = true\nuser_note = "preserve"',
        )
        migrated, _ = self.transform(source)
        parsed = tomllib.loads(migrated)
        self.assertNotIn("gpt-5.5", parsed["tui"]["model_availability_nux"])
        self.assertEqual(parsed["tui"]["model_availability_nux"]["gpt-private"], 7)
        self.assertEqual(
            parsed["model_providers"]["custom_openai"]["user_note"], "preserve"
        )


class OrchestratorTests(unittest.TestCase):
    def run_script(
        self,
        home: Path,
        backup: Path,
        *arguments: str,
        fault: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if fault:
            env["ATHENA_TEST_FAIL_AT"] = fault
        return subprocess.run(
            [
                str(SCRIPT),
                "--repo-root",
                str(ROOT),
                "--home",
                str(home),
                "--backup-dir",
                str(backup),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_full_transaction_preserves_user_fields_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)

            dry = self.run_script(home, backup, "--dry-run")
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertFalse(backup.exists())

            first = self.run_script(home, backup)
            self.assertEqual(first.returncode, 0, first.stderr)
            output = first.stdout + first.stderr
            self.assertNotIn("do-not-log", output)
            self.assertNotIn("private-command", output)
            self.assertIn("legacy=31 residue=0", output)
            self.assertTrue((backup / "manifest.json").is_file())

            cc = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            cx = tomllib.loads((home / ".codex/config.toml").read_text(encoding="utf-8"))
            hooks = json.loads((home / ".codex/hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(cc["env"]["VIBECODING_ATHENA_VERSION"], "9.9.1")
            self.assertEqual(cc["env"]["PRIVATE_TOKEN"], "do-not-log")
            self.assertEqual(cc["model"], "user-choice")
            self.assertTrue(cc["unknown_user_key"]["keep"])
            self.assertIn("/opt/private/hook", json.dumps(cc))
            cc_bash = next(
                group
                for group in cc["hooks"]["PostToolUse"]
                if group.get("matcher") == "Bash"
            )
            cc_commands = [hook.get("command", "") for hook in cc_bash["hooks"]]
            self.assertEqual(cc_bash["user_group_field"], "keep-cc-group")
            self.assertIn("node ~/.claude/hooks/private-third-party.cjs", cc_commands)
            self.assertIn("node ~/.claude/hooks/evidence-collector.cjs", cc_commands)
            self.assertEqual(
                next(
                    hook
                    for hook in cc_bash["hooks"]
                    if hook.get("command")
                    == "node ~/.claude/hooks/private-third-party.cjs"
                )["user_hook_field"],
                "keep-cc-hook",
            )
            self.assertIn("PrivateEvent", cc["hooks"])
            self.assertEqual(
                cx["shell_environment_policy"]["set"]["VIBECODING_VERSION"], "9.9.1"
            )
            self.assertEqual(cx["mcp_servers"]["private"]["command"], "private-command")
            self.assertTrue(cx["unknown"]["private"]["keep"])
            self.assertTrue(hooks["unknown"]["keep"])
            self.assertIn("/opt/private/hook", json.dumps(hooks))
            cx_mixed = next(
                group
                for group in hooks["hooks"]["PostToolUse"]
                if group.get("matcher") == "Bash|apply_patch|MCP|mcp__.*"
            )
            cx_commands = [hook.get("command", "") for hook in cx_mixed["hooks"]]
            self.assertEqual(cx_mixed["user_group_field"], "keep-cx-group")
            self.assertIn(
                "/usr/bin/env python3 ~/.codex/hooks/private-third-party.py",
                cx_commands,
            )
            self.assertIn(
                "/usr/bin/env python3 ~/.codex/hooks/evidence-collector.py",
                cx_commands,
            )
            self.assertEqual(
                next(
                    hook
                    for hook in cx_mixed["hooks"]
                    if hook.get("command")
                    == "/usr/bin/env python3 ~/.codex/hooks/private-third-party.py"
                )["user_hook_field"],
                "keep-cx-hook",
            )
            self.assertNotIn(
                "/usr/bin/env python3 ~/.codex/hooks/subagent-retry.py",
                cx_commands,
            )
            self.assertIn("PrivateEvent", hooks["hooks"])
            self.assertTrue((home / ".agents/skills/athena-dev/SKILL.md").is_file())
            self.assertFalse((home / ".codex/skills/athena-dev").exists())
            self.assertFalse((home / ".codex/skills/augment").exists())
            self.assertTrue((home / ".codex/skills/private-customer-skill/SKILL.md").is_file())
            self.assertTrue((home / ".codex/hooks/private-third-party.py").is_file())
            self.assertTrue((home / ".claude/hooks/private-third-party.cjs").is_file())

            before = digest_tree(home)
            backup_before = digest_tree(backup)
            second = self.run_script(home, backup)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("no backup or write", second.stdout)
            self.assertEqual(digest_tree(home), before)
            self.assertEqual(digest_tree(backup), backup_before)

    def test_unregistered_modified_release_name_is_preserved_as_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)
            augment = home / ".codex/skills/augment/SKILL.md"
            augment.write_text(
                augment.read_text(encoding="utf-8") + "\nuser-modified\n",
                encoding="utf-8",
            )
            result = self.run_script(home, backup, "--only", "cx")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("legacy=30 residue=1", result.stdout)
            self.assertIn("preserved legacy residue", result.stdout)
            self.assertTrue(augment.is_file())
            self.assertIn("user-modified", augment.read_text(encoding="utf-8"))
            self.assertTrue((home / ".codex/skills/private-customer-skill/SKILL.md").is_file())
            self.assertFalse((home / ".codex/skills/athena-dev").exists())
            self.assertTrue((home / ".agents/skills/augment/SKILL.md").is_file())

    def test_fault_points_roll_back_every_endpoint(self) -> None:
        for point in ("after-backup", "after-first-config", "asset-copy", "post-verify"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                home = root / "home"
                backup = root / "backup"
                prepare_old_home(home)
                before = digest_tree(home)
                result = self.run_script(home, backup, fault=point)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("rollback complete", result.stderr)
                self.assertEqual(digest_tree(home), before)

    def test_only_cx_leaves_cc_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)
            cc_before = digest_tree(home / ".claude")
            result = self.run_script(home, backup, "--only", "cx")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(digest_tree(home / ".claude"), cc_before)
            self.assertEqual(
                tomllib.loads((home / ".codex/config.toml").read_text(encoding="utf-8"))
                ["shell_environment_policy"]["set"]["VIBECODING_VERSION"],
                "9.9.1",
            )

    def test_owned_group_entirely_dropped_when_release_stops_shipping_its_hook(
        self,
    ) -> None:
        """9.9.0 registers WorktreeCreate/WorktreeRemove groups whose only hook
        is worktree-tracker.cjs; 9.9.1 no longer packages that hook (native
        worktree support replaces it). The merge must drop those event keys
        entirely rather than leaving an empty-hooks group or a stale hook
        pointing at a file the 9.9.1 release no longer ships."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)
            before_settings = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertIn("WorktreeCreate", before_settings["hooks"])
            self.assertIn("WorktreeRemove", before_settings["hooks"])

            result = self.run_script(home, backup, "--only", "cc")
            self.assertEqual(result.returncode, 0, result.stderr)

            migrated = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertNotIn("WorktreeCreate", migrated["hooks"])
            self.assertNotIn("WorktreeRemove", migrated["hooks"])
            self.assertNotIn("worktree-tracker.cjs", json.dumps(migrated["hooks"]))

    def test_athena_hook_allowlist_is_the_union_of_old_and_new_release_hooks(
        self,
    ) -> None:
        """The allowlist that decides which installed hooks are athena-owned
        (and therefore safe to replace/drop) must recognize hooks the *old*
        9.9.0 release shipped even when 9.9.1 no longer ships them — otherwise
        a stale 9.9.0-only hook like worktree-tracker.cjs would be
        misclassified as a private user hook and preserved forever instead of
        being cleanly retired."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)

            old_package = OLD_CC
            new_package = MIGRATE.locate_package(
                "cc",
                argparse_namespace(repo_root=ROOT, cc_package=None, cx_package=None, only="cc"),
            )
            allowlist = MIGRATE.release_hook_allowlist(
                new_package, "cc"
            ) | MIGRATE.release_hook_allowlist(old_package, "cc")
            self.assertIn("worktree-tracker.cjs", allowlist)
            self.assertIn("evidence-collector.cjs", allowlist)

            result = self.run_script(home, backup, "--only", "cc")
            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertNotIn("WorktreeCreate", migrated["hooks"])

    def test_user_added_permission_rules_survive_migration(self) -> None:
        """A permission entry the user added on top of the 9.9.0 defaults
        (not present in the old package's allow/deny lists) must still be
        present, in addition to the 9.9.1 package defaults, after migration."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)
            settings_path = home / ".claude/settings.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["permissions"]["allow"].append("Bash(make deploy-staging*)")
            settings["permissions"]["deny"].append("Bash(curl http://internal-admin*)")
            settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(home, backup, "--only", "cc")
            self.assertEqual(result.returncode, 0, result.stderr)

            migrated = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertIn("Bash(make deploy-staging*)", migrated["permissions"]["allow"])
            self.assertIn("Bash(curl http://internal-admin*)", migrated["permissions"]["deny"])
            new_package = MIGRATE.locate_package(
                "cc",
                argparse_namespace(repo_root=ROOT, cc_package=None, cx_package=None, only="cc"),
            )
            packaged = json.loads((new_package / "settings.json").read_text(encoding="utf-8"))
            for rule in packaged["permissions"]["allow"]:
                self.assertIn(rule, migrated["permissions"]["allow"])
            for rule in packaged["permissions"]["deny"]:
                self.assertIn(rule, migrated["permissions"]["deny"])

    def test_unsupported_version_is_zero_write_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            backup = root / "backup"
            prepare_old_home(home)
            settings = home / ".claude/settings.json"
            data = json.loads(settings.read_text(encoding="utf-8"))
            data["env"]["VIBECODING_ATHENA_VERSION"] = "8.0.0"
            settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            before = digest_tree(home)
            result = self.run_script(home, backup)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(backup.exists())
            self.assertEqual(digest_tree(home), before)
            self.assertNotIn("8.0.0", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
