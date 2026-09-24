#!/usr/bin/env python3
"""Install behavior for Athena 9.9.9. Never writes the real HOME."""

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
        if (candidate / "vibeCoding/claude/9.9.9/.claude/settings.json").is_file():
            return candidate
    raise RuntimeError("release repository root not found")


ROOT = repo_root()


def load_module():
    spec = importlib.util.spec_from_file_location("athena_setup_999", SCRIPT)
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


class SetupTests(unittest.TestCase):
    def run_setup(self, home: Path, *arguments: str, fault: str | None = None) -> subprocess.CompletedProcess[str]:
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

    def test_fresh_cc_only_installs_and_keeps_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            sessions = home / ".claude/sessions"
            sessions.mkdir(parents=True)
            (sessions / "kept.jsonl").write_text("history\n", encoding="utf-8")
            result = self.run_setup(home, "--only", "cc")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertEqual(data["env"]["VIBECODING_ATHENA_VERSION"], "9.9.9")
            self.assertTrue((home / ".claude/skills/athena-review/REVIEW.md").is_file())
            self.assertTrue((home / ".claude/skills/athena-vm/templates/vm.json.example").is_file())
            self.assertTrue((home / ".claude/skills/llm-as-a-verifier/SKILL.md").is_file())
            self.assertFalse((home / ".claude/REVIEW.md").exists())
            self.assertFalse((home / ".codex/config.toml").exists())
            self.assertEqual((sessions / "kept.jsonl").read_text(encoding="utf-8"), "history\n")

    def test_same_version_is_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_setup(home, "--only", "cc").returncode, 0)
            before = digest_tree(home)
            result = self.run_setup(home, "--only", "cc")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no files changed", result.stdout)
            self.assertEqual(digest_tree(home), before)

    def test_old_version_requires_migrate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                '{"env":{"VIBECODING_ATHENA_VERSION":"9.9.8"},"secret":"secret-value"}\n',
                encoding="utf-8",
            )
            before = digest_tree(home)
            result = self.run_setup(home, "--only", "cc")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(digest_tree(home), before)
            self.assertNotIn("secret-value", result.stdout + result.stderr)

    def test_fresh_transaction_rolls_back_faults(self) -> None:
        for point in ("after-first-config", "asset-copy"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                result = self.run_setup(home, "--only", "cc", fault=point)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse((home / ".claude/settings.json").exists())
                self.assertFalse((home / ".claude/CLAUDE.md").exists())
                leftovers = {path for path in digest_tree(home) if not path.startswith(".athena/backups/")}
                self.assertEqual(leftovers, set())

    def test_source_manifest_excludes_generated_junk(self) -> None:
        for kind, package in (
            ("cc", ROOT / "vibeCoding/claude/9.9.9/.claude"),
            ("cx", ROOT / "vibeCoding/codex/9.9.9/.codex"),
        ):
            paths = [relative for _, relative in SETUP.source_files(package, kind)]
            self.assertTrue(paths)
            self.assertFalse(any(SETUP.is_junk(path) for path in paths))
            self.assertFalse(any(SETUP.is_preserved_session(path) for path in paths))

    def test_agents_have_70_turn_cap(self) -> None:
        agents = ROOT / "vibeCoding/claude/9.9.9/.claude/agents"
        for path in agents.glob("*.md"):
            frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
            caps = [line for line in frontmatter.splitlines() if line.startswith("maxTurns:")]
            self.assertEqual(caps, ["maxTurns: 70"], path.name)


class LaavTests(unittest.TestCase):
    def test_disabled_skip(self) -> None:
        script = ROOT / "vibeCoding/claude/9.9.9/.claude/skills/llm-as-a-verifier/scripts/rank.py"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            packet = base / "packet.md"
            packet.write_text("AC1: foo\n", encoding="utf-8")
            a = base / "a.diff"
            b = base / "b.diff"
            a.write_text("diff a\n", encoding="utf-8")
            b.write_text("diff b\n", encoding="utf-8")
            output = base / "rank.json"
            result = subprocess.run(
                [sys.executable, str(script), "--packet", str(packet), "--candidate", str(a),
                 "--candidate", str(b), "--output", str(output), "--index", str(base / "missing.md")],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "skipped")
            self.assertEqual(data["reason"], "disabled")


if __name__ == "__main__":
    unittest.main()
