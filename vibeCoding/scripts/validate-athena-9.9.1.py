#!/usr/bin/env python3
"""Static/TDD release contract for Athena 9.9.1.

The first run against the untouched 9.9.0 copy is intentionally red. Runtime
fixtures are expanded by the validation sprint; this file keeps the release
identity and drift checks executable throughout implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

try:
    import yaml
except ImportError:  # Keep the release summary available on lean Python installs.
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
CX = ROOT / "vibeCoding/codex/9.9.1/.codex"
CC = ROOT / "vibeCoding/claude/9.9.1/.claude"
BASE = "5eb6189"
failures: list[str] = []
passes: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        passes.append(name)
    else:
        failures.append(f"{name}: {detail}" if detail else name)


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"read {path.relative_to(ROOT)}: {exc}")
        return ""


def all_text(root: Path, suffixes: tuple[str, ...]) -> list[tuple[Path, str]]:
    rows: list[tuple[Path, str]] = []
    if not root.is_dir():
        return rows
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes:
            rows.append((path, text(path)))
    return rows


def check_baseline() -> None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            BASE,
            "--",
            "vibeCoding/codex/9.9.0",
            "vibeCoding/claude/9.9.0",
        ],
        cwd=ROOT,
        check=False,
    )
    check("9.9.0 baseline unchanged", proc.returncode == 0, f"git diff exit={proc.returncode}")

    release_roots = (ROOT / "vibeCoding/codex/9.9.1", ROOT / "vibeCoding/claude/9.9.1", ROOT / "vibeCoding/scripts")
    junk = [
        path.relative_to(ROOT)
        for release_root in release_roots
        for path in release_root.rglob("*")
        if path.name in {"__pycache__", ".DS_Store", "tmp"} or path.suffix == ".pyc"
    ]
    check("release tree has no junk", not junk, ", ".join(map(str, junk[:8])))

    future_hits: list[str] = []
    text_suffixes = {".md", ".py", ".toml", ".json", ".yaml", ".yml", ".cjs", ".js", ".sh"}
    for release_root in release_roots:
        for path in release_root.rglob("*"):
            if not path.is_file() or path.suffix not in text_suffixes:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not re.search(r"(?i)Athena|VIBECODING(?:_ATHENA)?_VERSION|\b(?:FROM_|TO_)?VERSION\s*[:=]", line):
                    continue
                versions = re.findall(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])", line)
                if any((int(major), int(minor), int(patch)) > (9, 9, 1) for major, minor, patch in versions):
                    future_hits.append(str(path.relative_to(ROOT)))
                    break
    check("release tree has no future version marker", not future_hits, ", ".join(future_hits[:8]))

    diff_check = subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    check("git diff --check", diff_check.returncode == 0, f"exit={diff_check.returncode}")


def check_identity_and_config() -> None:
    check("CX package exists", CX.is_dir())
    check("CC package exists", CC.is_dir())
    cfg_path = CX / "config.toml"
    cfg_text = text(cfg_path)
    try:
        cfg = tomllib.loads(cfg_text)
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"CX config TOML: {exc}")
        cfg = {}

    check("config model_provider=openai", cfg.get("model_provider") == "openai", repr(cfg.get("model_provider")))
    check("config model=gpt-5.6-sol", cfg.get("model") == "gpt-5.6-sol", repr(cfg.get("model")))
    check("config has no manual context", "model_context_window" not in cfg)
    check("config has no manual compact", "model_auto_compact_token_limit" not in cfg)
    check("config has no model availability NUX", "tui" not in cfg or "model_availability_nux" not in cfg.get("tui", {}))
    providers = cfg.get("model_providers", {})
    empty_base = [name for name, value in providers.items() if isinstance(value, dict) and value.get("base_url") == ""]
    check("config has no empty provider endpoint", not empty_base, ",".join(empty_base))
    version = cfg.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION")
    check("config version=9.9.1", version == "9.9.1", repr(version))
    skill_paths = [entry.get("path", "") for entry in cfg.get("skills", {}).get("config", [])]
    check("config skills use ~/.agents/skills", bool(skill_paths) and all("/.agents/skills/" in path for path in skill_paths))
    check("AGENTS identity=9.9.1", "v9.9.1" in text(CX / "AGENTS.md"))
    check("CLAUDE identity=9.9.1", "v9.9.1" in text(CC / "CLAUDE.md"))


def check_hooks() -> None:
    evidence = text(CX / "hooks/evidence-collector.py")
    retry = text(CX / "hooks/subagent-retry.py")
    gate = text(CX / "hooks/delivery-gate.py")
    hooks_json = text(CX / "hooks.json")
    check("PostToolUse reads tool_response", "tool_response" in evidence and "tool_response" in retry)
    check("PostToolUse rejects legacy tool_output", "tool_output" not in evidence and "tool_output" not in retry)
    check("gate uses assignment JSONL", "subagent-assignments.jsonl" in gate)
    check("gate uses event JSONL", "subagent-events.jsonl" in gate)
    check("gate validates final PASS", "VERDICT" in gate and "PASS" in gate)
    check("SessionStart includes clear", bool(re.search(r'"matcher"\s*:\s*"[^"]*clear', hooks_json, re.I)))


def check_contract_text() -> None:
    cx_rows = all_text(CX, (".md", ".toml"))
    forbidden = {
        "spawn_agent --cwd": re.compile(r"spawn_agent\s+--cwd"),
        "assign_task": re.compile(r"\bassign_task\b"),
        "bare wait": re.compile(r"(?m)^\s*(?:[-*]\s*)?wait\s*$"),
    }
    for label, pattern in forbidden.items():
        hits = [str(path.relative_to(ROOT)) for path, body in cx_rows if pattern.search(body)]
        check(f"CX has no {label}", not hits, ", ".join(hits[:8]))

    details_hits = []
    for path, body in all_text(CX, (".md", ".toml", ".py")):
        if "athena-migrate" in path.parts:
            continue
        if ".ai_state/details" in body:
            details_hits.append(str(path.relative_to(ROOT)))
    check("non-migrate details refs removed", not details_hits, ", ".join(details_hits[:8]))

    bad_frontmatter = []
    for skill in sorted((CX / "skills").glob("*/SKILL.md")):
        body = text(skill)
        head = body.split("---", 2)[1] if body.startswith("---") and body.count("---") >= 2 else ""
        if re.search(r"(?m)^(effort|attach_to_stages):", head):
            bad_frontmatter.append(skill.parent.name)
    check("CX skill frontmatter official-only", not bad_frontmatter, ", ".join(bad_frontmatter))


def check_release_static() -> None:
    roots = (CX, CC, ROOT / "vibeCoding/scripts")
    python_files = sorted(path for root in roots for path in root.rglob("*.py"))
    compile_errors: list[str] = []
    for path in python_files:
        try:
            compile(path.read_bytes(), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            compile_errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
    check(f"Python compile no-pycache {len(python_files)}/{len(python_files)}", not compile_errors, ", ".join(compile_errors[:8]))

    for suffixes, label in (({ ".json" }, "JSON"), ({ ".toml" }, "TOML"), ({ ".yaml", ".yml" }, "YAML")):
        files = sorted(path for root in roots for path in root.rglob("*") if path.is_file() and path.suffix in suffixes)
        errors: list[str] = []
        if label == "YAML" and yaml is None:
            errors.append("PyYAML unavailable")
        else:
            for path in files:
                try:
                    if path.suffix == ".json":
                        json.loads(path.read_text(encoding="utf-8"))
                    elif path.suffix == ".toml":
                        tomllib.loads(path.read_text(encoding="utf-8"))
                    else:
                        yaml.safe_load(path.read_text(encoding="utf-8"))
                except Exception as exc:  # parser-specific errors still become a summarized FAIL
                    errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
        check(f"{label} parse {len(files)}/{len(files)}", not errors, ", ".join(errors[:8]))

    node = shutil.which("node")
    node_files = sorted([*CC.rglob("*.cjs"), *CC.rglob("*.js")])
    node_failures: list[str] = []
    if node:
        for path in node_files:
            run = subprocess.run([node, "--check", str(path)], cwd=ROOT, check=False, capture_output=True, text=True)
            if run.returncode != 0:
                node_failures.append(str(path.relative_to(ROOT)))
    check(
        f"CC Node syntax {len(node_files)}/{len(node_files)}",
        bool(node) and not node_failures,
        "node unavailable" if not node else ", ".join(node_failures[:8]),
    )

    quick_validate = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills/.system/skill-creator/scripts/quick_validate.py"
    skills = [
        *(path for path in sorted((CX / "skills").iterdir()) if path.is_dir()),
        *(path for path in sorted((CC / "skills").iterdir()) if path.is_dir()),
    ]
    skill_failures: list[str] = []
    if quick_validate.is_file():
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for skill in skills:
            run = subprocess.run(
                [sys.executable, str(quick_validate), str(skill)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            if run.returncode != 0:
                skill_failures.append(str(skill.relative_to(ROOT)))
    check(
        f"official quick_validate {len(skills)}/62",
        quick_validate.is_file() and len(skills) == 62 and not skill_failures,
        "official validator unavailable" if not quick_validate.is_file() else ", ".join(skill_failures[:8]),
    )

    junk_after = [path for root in roots for path in root.rglob("*") if path.name == "__pycache__" or path.suffix == ".pyc"]
    check("static validation leaves no bytecode", not junk_after, ", ".join(str(path.relative_to(ROOT)) for path in junk_after[:8]))


def tree_manifest(root: Path) -> dict[str, tuple[str, int]]:
    return {
        str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o111)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def check_package_parity() -> None:
    cx_skills = {path.name for path in (CX / "skills").iterdir() if path.is_dir()}
    cc_skills = {path.name for path in (CC / "skills").iterdir() if path.is_dir()}
    def declared_names(root: Path, names: set[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in names:
            try:
                body = (root / name / "SKILL.md").read_text(encoding="utf-8")
                frontmatter = body.split("---", 2)[1]
            except (OSError, IndexError):
                frontmatter = ""
            match = re.search(r"(?m)^name:\s*['\"]?([a-z0-9-]+)", frontmatter)
            result[name] = match.group(1) if match else ""
        return result

    cx_declared = declared_names(CX / "skills", cx_skills)
    cc_declared = declared_names(CC / "skills", cc_skills)
    check(
        "shared skill-name parity 31/31",
        cx_skills == cc_skills and len(cx_skills) == 31 and cx_declared == cc_declared,
    )
    for skill_name in ("athena-setup", "athena-migrate"):
        cx_tree = tree_manifest(CX / "skills" / skill_name)
        cc_tree = tree_manifest(CC / "skills" / skill_name)
        check(f"{skill_name} CC/CX parity", cx_tree == cc_tree)


def check_install_contract() -> None:
    setup = text(CX / "skills/athena-setup/SKILL.md")
    migrate = text(CX / "skills/athena-migrate/SKILL.md")
    setup_script = CX / "skills/athena-setup/scripts/setup-athena.py"
    migrate_script = CX / "skills/athena-migrate/scripts/migrate-9.9.0-to-9.9.1.py"
    check("setup installs AGENTS", "AGENTS.md" in setup)
    check("setup finds repo-root CX package", "vibeCoding/codex/9.9.1/.codex" in setup)
    check("setup finds repo-root CC package", "vibeCoding/claude/9.9.1/.claude" in setup)
    for state in ("fresh", "CC-only", "CX-only", "same-version", "old-version"):
        check(f"setup documents {state}", state in setup)
    check("migrate supports 9.9.0 to 9.9.1", "9.9.0" in migrate and "9.9.1" in migrate)
    check("migration orchestrator exists", migrate_script.is_file())
    check("migration orchestrator executable", os.access(migrate_script, os.X_OK))
    help_run = subprocess.run(
        [sys.executable, str(migrate_script), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    help_text = help_run.stdout + help_run.stderr
    check("migration orchestrator help runs", help_run.returncode == 0, help_text[-500:])
    for option in ("--home", "--repo-root", "--cc-package", "--cx-package", "--only", "--dry-run", "--backup-dir"):
        check(f"migration CLI {option}", option in help_text)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for label, test_path in (
        ("CX setup behavior suite", CX / "skills/athena-setup/tests/test_setup_991.py"),
        ("CC setup behavior suite", CC / "skills/athena-setup/tests/test_setup_991.py"),
        ("CX migration behavior suite", CX / "skills/athena-migrate/tests/test_migrate_991.py"),
        ("CC migration behavior suite", CC / "skills/athena-migrate/tests/test_migrate_991.py"),
    ):
        run = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        detail = (run.stdout + run.stderr)[-1200:]
        check(label, run.returncode == 0, detail)


def isolated_env(home: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    env.update(
        {
            "HOME": str(home),
            "CODEX_HOME": str(home / ".codex"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "NO_COLOR": "1",
        }
    )
    return env


def check_fresh_codex_runtime() -> None:
    setup_script = CX / "skills/athena-setup/scripts/setup-athena.py"
    codex = shutil.which("codex")
    if codex is None:
        check("temp HOME Codex doctor", False, "codex unavailable")
        check("temp HOME prompt-input", False, "codex unavailable")
        return
    with tempfile.TemporaryDirectory(prefix="athena-991-release-") as raw_home:
        home = Path(raw_home)
        env = isolated_env(home)
        setup = subprocess.run(
            [sys.executable, str(setup_script), "--home", str(home), "--repo-root", str(ROOT), "--only", "both"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        installed = setup.returncode == 0
        check("temp HOME fresh setup", installed, f"exit={setup.returncode}")
        if not installed:
            check("temp HOME Codex doctor", False, "setup failed")
            check("temp HOME prompt-input", False, "setup failed")
            return

        try:
            doctor = subprocess.run(
                [codex, "--strict-config", "doctor", "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
                env=env,
            )
            report = json.loads(doctor.stdout)
            checks = report.get("checks", {}) if isinstance(report, dict) else {}
            config_status = checks.get("config.load", {}).get("status")
            provider_status = checks.get("network.provider_reachability", {}).get("status")
            auth_status = checks.get("auth.credentials", {}).get("status", "unknown")
            doctor_ok = config_status == "ok" and provider_status == "ok"
            detail = f"config={config_status} provider={provider_status} auth={auth_status} (auth fail accepted)"
            if provider_status != "ok":
                detail += "; network unavailable or provider endpoint unreachable"
            check("temp HOME Codex doctor redacted JSON", doctor_ok, detail)
        except subprocess.TimeoutExpired:
            check("temp HOME Codex doctor redacted JSON", False, "network unavailable or doctor timed out")
        except (json.JSONDecodeError, OSError, AttributeError) as exc:
            check("temp HOME Codex doctor redacted JSON", False, f"invalid redacted JSON: {type(exc).__name__}")

        try:
            prompt = subprocess.run(
                [codex, "debug", "prompt-input", "release validation"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            prompt_data = json.loads(prompt.stdout)
            rendered = json.dumps(prompt_data, ensure_ascii=False)
            identity = "VibeCoding Athena v9.9.1" in rendered
            pace = "- pace:" in rendered and "/.agents/skills/pace/SKILL.md" in rendered
            agents_skills = "/.agents/skills/" in rendered
            check(
                "temp HOME prompt-input Athena/PACE/.agents",
                prompt.returncode == 0 and identity and pace and agents_skills,
                f"exit={prompt.returncode} identity={identity} pace={pace} agents_skills={agents_skills}",
            )
        except (json.JSONDecodeError, OSError) as exc:
            check("temp HOME prompt-input Athena/PACE/.agents", False, f"invalid JSON: {type(exc).__name__}")


def check_runtime_contract() -> None:
    runtime_suite = ROOT / "vibeCoding/scripts/test-athena-9.9.1-runtime.py"
    check("runtime behavior suite exists", runtime_suite.is_file())
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [sys.executable, str(runtime_suite)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    detail = (run.stdout + run.stderr)[-2000:]
    check("runtime behavior suite", run.returncode == 0, detail)


def main() -> int:
    check_baseline()
    check_identity_and_config()
    check_hooks()
    check_contract_text()
    check_release_static()
    check_package_parity()
    check_install_contract()
    check_runtime_contract()
    check_fresh_codex_runtime()
    for name in passes:
        print(f"PASS {name}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"SUMMARY pass={len(passes)} fail={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
