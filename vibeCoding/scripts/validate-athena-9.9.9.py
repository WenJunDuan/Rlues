#!/usr/bin/env python3
"""Validate the CC/CX 9.9.9 candidate packages and their behavior regressions.

This is a package/code check. Real project acceptance, platform agent evals and
independent release approval are recorded separately; a green run is not ship.
Uses Python 3.11+ and Node.js. It never installs into the caller's home.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
VERSION = "9.9.9"
OUTCOMES: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    OUTCOMES.append((name, bool(passed), detail))


def command(args: list[str], timeout: int = 120):
    return subprocess.run(args, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=timeout)


def source_files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def syntax(package: Path, side: str, node: str | None):
    failures = []
    for path in sorted(package.rglob("*")):
        if not path.is_file() or "tests" in path.parts:
            continue
        rel = path.relative_to(package).as_posix()
        try:
            if path.suffix == ".py":
                ast.parse(path.read_text(), filename=rel)
            elif path.suffix == ".json":
                json.loads(path.read_text())
            elif path.suffix == ".toml":
                tomllib.loads(path.read_text())
            elif path.suffix == ".cjs" and node:
                result = command([node, "--check", str(path)], timeout=15)
                if result.returncode:
                    failures.append(rel + ": " + result.stderr[-300:])
        except (SyntaxError, ValueError) as exc:
            failures.append(rel + ": " + str(exc))
    check(side + " Python/JSON/TOML/JS syntax", not failures, "\n".join(failures))


def package_contracts():
    node = shutil.which("node")
    check("Node.js available for CC runtime checks", bool(node))
    skills_by_side = {}
    for side, vendor, native, entry, retired in (
        ("CC", "claude", ".claude", "CLAUDE.md", "hooks/token-usage-collector.cjs"),
        ("CX", "codex", ".codex", "AGENTS.md", "hooks/token-usage-collector.py"),
    ):
        release = ROOT / "vibeCoding" / vendor / VERSION
        package = release / native
        baseline = release.with_name("9.9.8") / native
        check(side + " candidate directory", package.is_dir())
        if not package.is_dir():
            continue
        missing = source_files(baseline) - source_files(package) - {retired, "REVIEW.md"}
        check(side + " complete package (declared retirement only)", not missing, repr(sorted(missing)))
        junk = [str(p.relative_to(package)) for p in package.rglob("*") if p.name in {"__pycache__", ".DS_Store"} or p.suffix == ".pyc"]
        check(side + " no generated cache in package", not junk, repr(junk))
        check(side + " current root identity", f"v{VERSION}" in (package / entry).read_text())
        check(side + " retired telemetry removed", not (package / retired).exists())
        skill_names = {p.name for p in (package / "skills").iterdir() if p.is_dir()}
        skills_by_side[side] = skill_names
        check(side + " 26 core skills retained", {"pace", "athena-setup", "athena-vm", "athena-review"}.issubset(skill_names), str(sorted(skill_names)))
        check(side + " llm-as-a-verifier packaged", "llm-as-a-verifier" in skill_names)
        check(side + " skill count", len(skill_names) >= 27, str(len(skill_names)))
        check(side + " VM json example", (package / "skills/athena-vm/templates/vm.json.example").is_file())
        check(side + " VM schema", (package / "skills/athena-vm/references/vm.schema.json").is_file())
        check(side + " review prompt in skill", (package / "skills/athena-review/REVIEW.md").is_file())
        if side == "CC":
            check("CC REVIEW.md not at .claude root", not (package / "REVIEW.md").exists())
            agent_dir = package / "agents"
            invalid_turn_caps = []
            for agent in sorted(agent_dir.glob("*.md")):
                text = agent.read_text()
                frontmatter = text.split("---", 2)[1]
                caps = re.findall(r"(?m)^maxTurns: *(.*?)$", frontmatter)
                if caps != ["70"]:
                    invalid_turn_caps.append(agent.name)
            check("CC agents have maxTurns=70", not invalid_turn_caps, repr(invalid_turn_caps))
        else:
            check("CX fullstack-contract", (package / "skills/pace/references/fullstack-contract.md").is_file())
            check("CX state-contract", (package / "skills/pace/references/state-contract.md").is_file())
        bad_skills = []
        for skill in sorted(skill_names):
            path = package / "skills" / skill / "SKILL.md"
            if not path.is_file():
                bad_skills.append(skill + ": missing entry")
                continue
            text = path.read_text()
            parts = text.split("---", 2)
            if not text.startswith("---\n") or len(parts) < 3 or not re.search(r"(?m)^name:\s*\S", parts[1]) or not re.search(r"(?m)^description:\s*\S", parts[1]):
                bad_skills.append(skill + ": frontmatter")
        check(side + " skills have discoverable metadata", not bad_skills, repr(bad_skills))
        template = (package / "skills/pace/templates/_index.md").read_text()
        check(side + " new index version", bool(re.search(r'^version:\s*[\"\']9\.9\.9[\"\']', template, re.M)))
        try:
            if side == "CC":
                config = json.loads((package / "settings.json").read_text())
                identity = config.get("env", {}).get("VIBECODING_ATHENA_VERSION")
                hooks = config.get("hooks", {})
            else:
                config = tomllib.loads((package / "config.toml").read_text())
                identity = config.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION")
                hooks = json.loads((package / "hooks.json").read_text()).get("hooks", {})
            check(side + " config identity", identity == VERSION, repr(identity))
            hook_text = json.dumps(hooks)
            check(side + " no default local usage collector", "token-usage-collector" not in hook_text)
            check(side + " no nonexistent hook command", all((package / "hooks" / name).is_file() for name in re.findall(r"hooks/([A-Za-z_][A-Za-z0-9_.-]+\.(?:py|cjs))", hook_text)))
        except (OSError, ValueError) as exc:
            check(side + " config readable", False, str(exc))
        syntax(package, side, node)
    check("CC/CX skill coverage parity", skills_by_side.get("CC") == skills_by_side.get("CX"))


def behavior_tests():
    tests = ROOT / "vibeCoding/scripts/tests/athena999"
    for name in ("test_state_review.py", "test_vm_install.py", "test_fullstack_contract.py", "test_laav.py", "test_claude_rework.py"):
        path = tests / name
        check(name + " exists", path.is_file())
        if not path.is_file():
            continue
        result = command([sys.executable, str(path), "-v"], timeout=240)
        check(name + " behavior regressions", result.returncode == 0, (result.stdout + result.stderr)[-6000:])
        print((result.stdout + result.stderr).rstrip())


def install_matrix():
    cases = json.loads((ROOT / "vibeCoding/scripts/fixtures/athena-9.9.9/platform-install-cases.json").read_text())
    installer = ROOT / "vibeCoding/codex/9.9.9/.codex/skills/athena-setup/scripts/setup-athena.py"
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="athena999-install-matrix-") as tmp:
            home = Path(tmp)
            result = subprocess.run(
                [sys.executable, str(installer), "--home", str(home), "--repo-root", str(ROOT), "--only", case["only"]],
                cwd=ROOT, env={**os.environ, "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"},
                text=True, capture_output=True, timeout=120,
            )
            check(case["name"] + " installs", result.returncode == 0, (result.stdout + result.stderr)[-1600:])
            check(case["name"] + " respects selection", all((home / path).is_dir() for path in case["installed"]) and all(not (home / path).exists() for path in case["absent"]))
            for native in case["installed"]:
                if native == ".claude":
                    target = home / native / "settings.json"
                    version = json.loads(target.read_text()).get("env", {}).get("VIBECODING_ATHENA_VERSION") if target.exists() else None
                else:
                    target = home / native / "config.toml"
                    version = tomllib.loads(target.read_text()).get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION") if target.exists() else None
                check(case["name"] + " installs candidate " + native, version == VERSION, repr(version))


def main() -> int:
    package_contracts()
    install_matrix()
    behavior_tests()
    for name, passed, detail in OUTCOMES:
        print(("PASS " if passed else "FAIL ") + name)
        if not passed and detail:
            print(detail)
    passed = sum(ok for _, ok, _ in OUTCOMES)
    failed = len(OUTCOMES) - passed
    print(f"SUMMARY package_checks_pass={passed} fail={failed}; scope=candidate-code; release_acceptance=separate")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
