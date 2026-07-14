#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/setup-athena.py"


def repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "vibeCoding/claude/9.9.3/.claude/settings.json").is_file():
            return candidate
    raise RuntimeError("release repository root not found")


ROOT = repo_root()
STATES = json.loads(
    (ROOT / "vibeCoding/scripts/fixtures/athena-9.9.3/setup-states.json").read_text(
        encoding="utf-8"
    )
)["states"]


def load_module():
    spec = importlib.util.spec_from_file_location("athena_setup_991", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SETUP = load_module()


def digest_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in root.rglob("*"):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def mtime_tree(root: Path) -> dict[str, int]:
    return {
        path.relative_to(root).as_posix(): path.stat().st_mtime_ns
        for path in root.rglob("*")
        if path.is_file()
    }


class SetupTests(unittest.TestCase):
    def run_setup(
        self, home: Path, *arguments: str, fault: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if fault:
            env["ATHENA_TEST_FAIL_AT"] = fault
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(ROOT),
                "--home",
                str(home),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def assert_installed(self, home: Path, cc: bool, cx: bool) -> None:
        self.assertEqual((home / ".claude/settings.json").is_file(), cc)
        self.assertEqual((home / ".codex/config.toml").is_file(), cx)
        if cc:
            data = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertEqual(data["env"]["VIBECODING_ATHENA_VERSION"], "9.9.3")
        if cx:
            data = tomllib.loads((home / ".codex/config.toml").read_text(encoding="utf-8"))
            self.assertEqual(
                data["shell_environment_policy"]["set"]["VIBECODING_VERSION"], "9.9.3"
            )
            self.assertTrue((home / ".codex/AGENTS.md").is_file())
            self.assertTrue((home / ".agents/skills/athena-dev/SKILL.md").is_file())

    def test_setup_state_fixture_contract(self) -> None:
        self.assertEqual(
            set(STATES), {"fresh", "cc-only", "cx-only", "same-version", "old-version"}
        )

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            result = self.run_setup(home)
            self.assertEqual(STATES["fresh"], "install-both")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_installed(home, True, True)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_setup(home, "--only", "cc").returncode, 0)
            result = self.run_setup(home)
            self.assertEqual(STATES["cc-only"], "install-cx-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_installed(home, True, True)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_setup(home, "--only", "cx").returncode, 0)
            result = self.run_setup(home)
            self.assertEqual(STATES["cx-only"], "install-cc-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_installed(home, True, True)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_setup(home).returncode, 0)
            before = digest_tree(home)
            before_mtime = mtime_tree(home)
            result = self.run_setup(home)
            self.assertEqual(STATES["same-version"], "verify-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no files changed", result.stdout)
            self.assertEqual(digest_tree(home), before)
            self.assertEqual(mtime_tree(home), before_mtime)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                '{"env":{"VIBECODING_ATHENA_VERSION":"9.8.0"},"secret":"secret"}\n',
                encoding="utf-8",
            )
            before = digest_tree(home)
            result = self.run_setup(home)
            self.assertEqual(STATES["old-version"], "route-migrate")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                digest_tree(home / ".claude"),
                {key.removeprefix(".claude/"): value for key, value in before.items()},
            )
            self.assertTrue((home / ".codex/config.toml").is_file())
            self.assertTrue((home / ".codex/AGENTS.md").is_file())
            self.assertNotIn("9.8.0", result.stdout + result.stderr)
            self.assertNotIn("secret", result.stdout + result.stderr)

    def test_fresh_transaction_rolls_back_faults(self) -> None:
        for point in ("after-first-config", "asset-copy"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                result = self.run_setup(home, fault=point)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("rollback complete", result.stderr)
                self.assertEqual(digest_tree(home), {})

    def test_old_endpoint_routes_migrate_while_missing_endpoint_installs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                '{"env":{"VIBECODING_ATHENA_VERSION":"9.9.0"},"secret":"secret-value"}\n',
                encoding="utf-8",
            )
            cc_before = digest_tree(home / ".claude")
            result = self.run_setup(home)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(digest_tree(home / ".claude"), cc_before)
            self.assertTrue((home / ".codex/AGENTS.md").is_file())
            self.assertTrue((home / ".agents/skills/athena-dev/SKILL.md").is_file())
            self.assertNotIn("9.9.0", result.stdout + result.stderr)
            self.assertNotIn("secret-value", result.stdout + result.stderr)

    def test_source_manifest_excludes_generated_junk(self) -> None:
        for kind, package in (
            ("cc", ROOT / "vibeCoding/claude/9.9.3/.claude"),
            ("cx", ROOT / "vibeCoding/codex/9.9.3/.codex"),
        ):
            paths = [relative for _, relative in SETUP.source_files(package, kind)]
            self.assertTrue(paths)
            self.assertFalse(any(SETUP.is_junk(path) for path in paths))

    def test_existing_managed_skill_collision_is_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            marker = home / ".agents/skills/athena-dev/README.md"
            marker.parent.mkdir(parents=True)
            marker.write_text("third-party\n", encoding="utf-8")
            before = digest_tree(home)
            result = self.run_setup(home, "--only", "cx")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((home / ".codex/config.toml").exists())
            self.assertEqual(digest_tree(home), before)


if __name__ == "__main__":
    unittest.main()
