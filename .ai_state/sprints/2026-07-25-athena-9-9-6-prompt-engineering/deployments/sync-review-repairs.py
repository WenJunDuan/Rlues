#!/usr/bin/env python3
"""Transactionally sync Athena 9.9.6 review repairs into local endpoints."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import tomllib


REPO = Path(__file__).resolve().parents[4]
HOME = Path.home()
CC_SOURCE = REPO / "vibeCoding/claude/9.9.6/.claude"
CX_SOURCE = REPO / "vibeCoding/codex/9.9.6/.codex"
CC_TARGET = HOME / ".claude"
CX_TARGET = HOME / ".codex"
SKILLS_TARGET = HOME / ".agents/skills"
BACKUP_ROOT = HOME / ".athena/backups"
BACKUP_PREFIX = "athena-9.9.6-review-repair-"

CC_TOP = ("CLAUDE.md",)
CC_DIRS = ("rules", "hooks", "agents", "skills")
CX_TOP = ("hooks.json", "AGENTS.md")
CX_DIRS = ("hooks", "agents", "standards")
SAFE_NPX = (
    "Bash(npx playwright)",
    "Bash(npx playwright *)",
    "Bash(npx ecc-agentshield)",
    "Bash(npx ecc-agentshield *)",
)
UNSAFE_NPX = (
    "Bash(npx playwright*)",
    "Bash(npx ecc-agentshield*)",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name not in {".DS_Store"} and "__pycache__" not in path.parts
    )


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(fd)
    temp_path = Path(temporary)
    try:
        shutil.copyfile(source, temp_path)
        shutil.copymode(source, temp_path)
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_json(data: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = target.stat().st_mode if target.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_path, mode)
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)


def preflight() -> None:
    if not (CC_SOURCE.is_dir() and CX_SOURCE.is_dir()):
        raise RuntimeError("release sources are missing")
    package_settings = json.loads((CC_SOURCE / "settings.json").read_text())
    installed_settings = json.loads((CC_TARGET / "settings.json").read_text())
    package_config_text = (CX_SOURCE / "config.toml").read_text()
    installed_config_text = (CX_TARGET / "config.toml").read_text()
    tomllib.loads(package_config_text)
    tomllib.loads(installed_config_text)
    if "openai_base_url" in package_config_text:
        raise RuntimeError("fresh release config unexpectedly contains openai_base_url")
    if package_settings.get("env", {}).get("VIBECODING_ATHENA_VERSION") != "9.9.6":
        raise RuntimeError("release settings version mismatch")
    if installed_settings.get("env", {}).get("VIBECODING_ATHENA_VERSION") != "9.9.6":
        raise RuntimeError("installed settings version mismatch")
    for path in source_files(CC_SOURCE) + source_files(CX_SOURCE):
        if path.suffix == ".py":
            ast.parse(path.read_text(), filename=str(path))
        elif path.suffix == ".json":
            json.loads(path.read_text())
        elif path.suffix == ".toml":
            tomllib.loads(path.read_text())


def run_rsync(source: Path, target: Path, *, delete: bool = False) -> None:
    command = ["/usr/bin/rsync", "-a", "--exclude=ipc/ipc.sock"]
    if delete:
        command.append("--delete")
    command.extend([f"{source}/", f"{target}/"])
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def make_backup() -> Path:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = BACKUP_ROOT / f"{BACKUP_PREFIX}{timestamp}"
    if backup.exists():
        raise RuntimeError(f"backup path already exists: {backup}")
    backup.mkdir(parents=True, mode=0o700)
    for source, name in (
        (CC_TARGET, "claude"),
        (CX_TARGET, "codex"),
        (SKILLS_TARGET, "agents-skills"),
    ):
        destination = backup / name
        destination.mkdir()
        run_rsync(source, destination)
    (backup / ".complete").write_text("Athena 9.9.6 review-repair backup complete\n")
    return backup


def restore(backup: Path) -> None:
    if backup.parent != BACKUP_ROOT or not backup.name.startswith(BACKUP_PREFIX):
        raise RuntimeError("refusing to restore from an unexpected backup path")
    if not (backup / ".complete").is_file():
        raise RuntimeError("refusing to restore from an incomplete backup")
    for name, target in (
        ("claude", CC_TARGET),
        ("codex", CX_TARGET),
        ("agents-skills", SKILLS_TARGET),
    ):
        run_rsync(backup / name, target, delete=True)


def copy_tree(source: Path, target: Path) -> int:
    count = 0
    for path in source_files(source):
        atomic_copy(path, target / path.relative_to(source))
        count += 1
    return count


def merge_cc_settings() -> None:
    package = json.loads((CC_SOURCE / "settings.json").read_text())
    installed = json.loads((CC_TARGET / "settings.json").read_text())
    installed.setdefault("env", {})["VIBECODING_ATHENA_VERSION"] = "9.9.6"
    installed["hooks"] = package["hooks"]
    permissions = installed.setdefault("permissions", {})
    allow = [item for item in permissions.get("allow", []) if item not in UNSAFE_NPX]
    for item in SAFE_NPX:
        if item not in allow:
            allow.append(item)
    permissions["allow"] = allow
    atomic_json(installed, CC_TARGET / "settings.json")


def sync_managed() -> dict[str, int]:
    counts = {"cc": 0, "cx": 0, "skills": 0}
    for name in CC_TOP:
        atomic_copy(CC_SOURCE / name, CC_TARGET / name)
        counts["cc"] += 1
    for name in CC_DIRS:
        counts["cc"] += copy_tree(CC_SOURCE / name, CC_TARGET / name)
    merge_cc_settings()
    counts["cc"] += 1

    for name in CX_TOP:
        atomic_copy(CX_SOURCE / name, CX_TARGET / name)
        counts["cx"] += 1
    for name in CX_DIRS:
        counts["cx"] += copy_tree(CX_SOURCE / name, CX_TARGET / name)
    counts["skills"] += copy_tree(CX_SOURCE / "skills", SKILLS_TARGET)
    return counts


def assert_tree_matches(source: Path, target: Path) -> int:
    count = 0
    for path in source_files(source):
        destination = target / path.relative_to(source)
        if not destination.is_file() or digest(path) != digest(destination):
            raise RuntimeError(f"managed file mismatch: {destination}")
        count += 1
    return count


def parse_histories() -> tuple[int, int]:
    files = 0
    rows = 0
    for path in (CC_TARGET / "history.jsonl", CX_TARGET / "history.jsonl"):
        if not path.is_file():
            continue
        files += 1
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                json.loads(line)
                rows += 1
    return files, rows


def sqlite_checks() -> int:
    checked = 0
    candidates: set[Path] = set()
    for root in (CC_TARGET, CX_TARGET):
        for pattern in ("*.db", "*.sqlite", "*.sqlite3"):
            candidates.update(path for path in root.rglob(pattern) if path.is_file())
    for path in sorted(candidates):
        try:
            connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        except sqlite3.DatabaseError:
            continue
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()
            if not result or result[0] != "ok":
                raise RuntimeError(f"SQLite quick_check failed: {path}")
        except sqlite3.DatabaseError:
            # Some products use a .db suffix for non-SQLite caches.
            continue
        finally:
            connection.close()
        checked += 1
    return checked


def verify(config_digest_before: str) -> dict[str, int]:
    if digest(CX_TARGET / "config.toml") != config_digest_before:
        raise RuntimeError("user Codex config.toml changed during sync")
    installed_config = tomllib.loads((CX_TARGET / "config.toml").read_text())
    if installed_config.get("model_provider") != "openai":
        raise RuntimeError("installed Codex provider changed")
    if installed_config.get("openai_base_url") == "":
        raise RuntimeError("installed Codex gateway is blank")

    settings = json.loads((CC_TARGET / "settings.json").read_text())
    package_settings = json.loads((CC_SOURCE / "settings.json").read_text())
    if settings.get("hooks") != package_settings.get("hooks"):
        raise RuntimeError("Claude hooks were not synchronized")
    allow = settings.get("permissions", {}).get("allow", [])
    if any(item in allow for item in UNSAFE_NPX) or any(item not in allow for item in SAFE_NPX):
        raise RuntimeError("Claude npx permission boundaries are incorrect")

    matched = 0
    for name in CC_TOP:
        if digest(CC_SOURCE / name) != digest(CC_TARGET / name):
            raise RuntimeError(f"managed file mismatch: {CC_TARGET / name}")
        matched += 1
    for name in CC_DIRS:
        matched += assert_tree_matches(CC_SOURCE / name, CC_TARGET / name)
    for name in CX_TOP:
        if digest(CX_SOURCE / name) != digest(CX_TARGET / name):
            raise RuntimeError(f"managed file mismatch: {CX_TARGET / name}")
        matched += 1
    for name in CX_DIRS:
        matched += assert_tree_matches(CX_SOURCE / name, CX_TARGET / name)
    matched += assert_tree_matches(CX_SOURCE / "skills", SKILLS_TARGET)

    if "background: true" in (CC_TARGET / "agents/reviewer.md").read_text():
        raise RuntimeError("installed reviewer still forces background mode")
    if "background: true" in (CC_TARGET / "agents/spec-compliance.md").read_text():
        raise RuntimeError("installed spec-compliance still forces background mode")
    hooks = json.loads((CX_TARGET / "hooks.json").read_text())
    pretool = json.dumps(hooks.get("hooks", {}).get("PreToolUse", []))
    if "spawn_agent|Agent" not in pretool:
        raise RuntimeError("installed Codex spawn guard is missing")
    if not (CX_TARGET / "hooks/subagent-worktree-audit.py").is_file():
        raise RuntimeError("installed worktree audit hook is missing")

    history_files, history_rows = parse_histories()
    return {
        "managed_hash_matches": matched,
        "history_files": history_files,
        "history_rows": history_rows,
        "sqlite_databases": sqlite_checks(),
    }


def remove_backup(backup: Path) -> None:
    resolved_root = BACKUP_ROOT.resolve()
    resolved = backup.resolve()
    if resolved.parent != resolved_root or not resolved.name.startswith(BACKUP_PREFIX):
        raise RuntimeError("refusing to delete an unexpected backup path")
    if not (resolved / ".complete").is_file():
        raise RuntimeError("refusing to delete an incomplete backup")
    shutil.rmtree(resolved)
    if resolved.exists():
        raise RuntimeError("backup deletion did not complete")


def main() -> int:
    preflight()
    config_digest_before = digest(CX_TARGET / "config.toml")
    backup: Path | None = None
    try:
        reuse = os.environ.get("ATHENA_REUSE_BACKUP")
        if reuse:
            backup = Path(reuse).resolve()
            if backup.parent != BACKUP_ROOT.resolve() or not backup.name.startswith(BACKUP_PREFIX):
                raise RuntimeError("refusing to reuse an unexpected backup path")
            if not (backup / ".complete").is_file():
                raise RuntimeError("requested backup is incomplete")
        else:
            backup = make_backup()
        counts = sync_managed()
        verification = verify(config_digest_before)
    except Exception:
        if backup is not None and (backup / ".complete").is_file():
            restore(backup)
        raise

    remove_backup(backup)
    print(json.dumps({
        "status": "ok",
        "synced": counts,
        "verified": verification,
        "codex_config_unchanged": True,
        "backup": str(backup),
        "backup_deleted": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
