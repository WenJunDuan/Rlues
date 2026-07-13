#!/usr/bin/env python3
"""Fresh-install or verify Athena v9.9.2 without overwriting an installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import tomllib


VERSION = "9.9.2"
JUNK_DIRS = {"__pycache__", "tmp"}
JUNK_FILES = {".DS_Store"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fresh-install missing Athena endpoints, or verify v9.9.2."
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--cc-package", type=Path)
    parser.add_argument("--cx-package", type=Path)
    parser.add_argument("--only", choices=("cc", "cx", "both"), default="both")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def package_marker(kind: str) -> str:
    return "settings.json" if kind == "cc" else "config.toml"


def normalize_package(path: Path, kind: str) -> Path | None:
    hidden = ".claude" if kind == "cc" else ".codex"
    path = path.expanduser().resolve()
    choices = (path, path / hidden)
    for candidate in choices:
        if (candidate / package_marker(kind)).is_file():
            return candidate
    return None


def package_candidates(kind: str, args: argparse.Namespace) -> list[Path]:
    explicit = args.cc_package if kind == "cc" else args.cx_package
    env_name = "ATHENA_CC_PKG" if kind == "cc" else "ATHENA_CX_PKG"
    family = "claude" if kind == "cc" else "codex"
    hidden = ".claude" if kind == "cc" else ".codex"
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get(env_name):
        candidates.append(Path(os.environ[env_name]))
    roots = [args.repo_root] if args.repo_root else []
    roots.extend([Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents])
    for root in roots:
        if root is None:
            continue
        candidates.extend(
            [
                root / "vibeCoding" / family / VERSION / hidden,
                root / family / VERSION / hidden,
                root / hidden,
            ]
        )
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.expanduser())
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    return deduped


def locate_package(kind: str, args: argparse.Namespace) -> Path | None:
    for candidate in package_candidates(kind, args):
        normalized = normalize_package(candidate, kind)
        if normalized:
            return normalized
    return None


def read_version(kind: str, home: Path) -> tuple[str, str | None]:
    config = home / (".claude/settings.json" if kind == "cc" else ".codex/config.toml")
    if not config.exists():
        return "fresh", None
    try:
        if kind == "cc":
            data = json.loads(config.read_text(encoding="utf-8"))
            version = data.get("env", {}).get("VIBECODING_ATHENA_VERSION")
        else:
            data = tomllib.loads(config.read_text(encoding="utf-8"))
            version = data.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION")
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return "occupied", None
    if version == VERSION:
        return "same", version
    if isinstance(version, str) and version:
        return "old", version
    return "occupied", None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_junk(relative: Path) -> bool:
    return (
        any(part in JUNK_DIRS for part in relative.parts)
        or relative.name in JUNK_FILES
        or relative.suffix == ".pyc"
    )


def validate_source(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"unsupported package symlink: {path}")
    if path.suffix == ".json":
        json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix == ".toml":
        tomllib.loads(path.read_text(encoding="utf-8"))
    elif path.suffix == ".py":
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def source_files(package: Path, kind: str) -> list[tuple[Path, Path]]:
    if kind == "cc":
        names = ("CLAUDE.md", "statusline-command.sh", "rules", "hooks", "agents", "skills")
        target_root = Path(".claude")
    else:
        names = ("hooks.json", "AGENTS.md", "hooks", "agents", "standards")
        target_root = Path(".codex")
    files: list[tuple[Path, Path]] = []
    for name in names:
        source = package / name
        if source.is_file():
            if not is_junk(Path(name)):
                validate_source(source)
                files.append((source, target_root / name))
        elif source.is_dir():
            for child in sorted(path for path in source.rglob("*") if path.is_file()):
                relative = child.relative_to(source)
                if is_junk(relative):
                    continue
                validate_source(child)
                files.append((child, target_root / name / relative))
    if kind == "cx":
        for skill in sorted(path for path in (package / "skills").iterdir() if path.is_dir()):
            for child in sorted(path for path in skill.rglob("*") if path.is_file()):
                relative = child.relative_to(skill)
                if is_junk(relative):
                    continue
                validate_source(child)
                files.append((child, Path(".agents/skills") / skill.name / relative))
    return files


def package_counts(package: Path, kind: str) -> dict[str, int]:
    extensions = {
        "cc": (("rules", "*.md"), ("hooks", "*.cjs"), ("agents", "*.md")),
        "cx": (("standards", "*.md"), ("hooks", "*.py"), ("agents", "*.toml")),
    }
    counts = {name: len(list((package / name).glob(pattern))) for name, pattern in extensions[kind]}
    counts["skills"] = len([path for path in (package / "skills").iterdir() if path.is_dir()])
    return counts


def render_cx_config(package: Path, home: Path) -> bytes:
    text = (package / "config.toml").read_text(encoding="utf-8")
    config_home = home.as_posix()
    rendered = text.replace("<USER_HOME>", config_home)
    rendered = rendered.replace(
        f"{config_home}/.codex/skills/", f"{config_home}/.agents/skills/"
    )
    tomllib.loads(rendered)
    return rendered.encode("utf-8")


def planned_destinations(package: Path, kind: str, home: Path) -> list[Path]:
    config = home / (".claude/settings.json" if kind == "cc" else ".codex/config.toml")
    return [config, *[home / relative for _, relative in source_files(package, kind)]]


def config_candidate(package: Path, kind: str, home: Path) -> bytes:
    if kind == "cc":
        content = (package / "settings.json").read_bytes()
        json.loads(content)
        return content
    return render_cx_config(package, home)


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def maybe_fail(point: str) -> None:
    if os.environ.get("ATHENA_TEST_FAIL_AT") == point:
        raise OSError(f"injected failure at {point}")


def collision_paths(package: Path, kind: str, home: Path) -> list[Path]:
    destinations = planned_destinations(package, kind, home)
    skill_root = home / (".claude/skills" if kind == "cc" else ".agents/skills")
    skill_collisions = {
        skill_root / skill.name
        for skill in (package / "skills").iterdir()
        if skill.is_dir() and not is_junk(Path(skill.name)) and (skill_root / skill.name).exists()
    }
    return sorted({path for path in destinations if path.exists()} | skill_collisions)


def install_fresh(package: Path, kind: str, home: Path, dry_run: bool) -> bool:
    destinations = planned_destinations(package, kind, home)
    skill_root = home / (".claude/skills" if kind == "cc" else ".agents/skills")
    skill_collisions = {
        skill_root / skill.name
        for skill in (package / "skills").iterdir()
        if skill.is_dir() and (skill_root / skill.name).exists()
    }
    collisions = sorted({path for path in destinations if path.exists()} | skill_collisions)
    if collisions:
        print(f"{kind.upper()}: blocked; {len(collisions)} managed destinations already exist")
        for path in collisions[:10]:
            print(f"  collision: {path}")
        return False
    print(f"{kind.upper()}: fresh install; files={len(destinations)} counts={package_counts(package, kind)}")
    if dry_run:
        return True
    config_dest = destinations[0]
    config_dest.parent.mkdir(parents=True, exist_ok=True)
    if kind == "cc":
        shutil.copy2(package / "settings.json", config_dest)
    else:
        config_dest.write_bytes(render_cx_config(package, home))
        shutil.copymode(package / "config.toml", config_dest)
    for source, relative in source_files(package, kind):
        destination = home / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for path in (home / (".claude/hooks" if kind == "cc" else ".codex/hooks")).glob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o100)
    print(f"{kind.upper()}: installed v{VERSION}")
    return True


def verify_same(package: Path, kind: str, home: Path) -> bool:
    missing: list[Path] = []
    drifted: list[Path] = []
    for source, relative in source_files(package, kind):
        destination = home / relative
        if not destination.is_file():
            missing.append(destination)
        elif sha256(source) != sha256(destination):
            drifted.append(destination)
    config = home / (".claude/settings.json" if kind == "cc" else ".codex/config.toml")
    try:
        state, version = read_version(kind, home)
        if state != "same" or version != VERSION:
            drifted.append(config)
        if kind == "cx":
            data = tomllib.loads(config.read_text(encoding="utf-8"))
            entries = data.get("skills", {}).get("config", [])
            expected_names = {
                path.name for path in (package / "skills").iterdir() if path.is_dir()
            }
            configured_names: set[str] = set()
            for item in entries:
                path = str(item.get("path", ""))
                name = Path(path).parent.name if path.endswith("/SKILL.md") else ""
                if name in expected_names:
                    configured_names.add(name)
                if "/.codex/skills/" in path or not path.endswith("/SKILL.md"):
                    drifted.append(config)
                    break
            if configured_names != expected_names:
                drifted.append(config)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        drifted.append(config)
    print(
        f"{kind.upper()}: verify v{VERSION}; counts={package_counts(package, kind)} "
        f"missing={len(missing)} drifted={len(set(drifted))}"
    )
    for label, paths in (("missing", missing), ("drift", sorted(set(drifted)))):
        for path in paths[:10]:
            print(f"  {label}: {path}")
    return not missing and not drifted


def main() -> int:
    args = parse_args()
    home = args.home.expanduser().resolve()
    kinds = ("cc", "cx") if args.only == "both" else (args.only,)
    records: list[tuple[str, Path, str]] = []
    refused = False
    try:
        for kind in kinds:
            package = locate_package(kind, args)
            if package is None:
                print(f"{kind.upper()}: package not found; pass its package path or --repo-root")
                refused = True
                continue
            state, _ = read_version(kind, home)
            print(f"{kind.upper()}: state={state} package={package}")
            if state == "old":
                print(f"{kind.upper()}: older Athena endpoint detected; run /athena-migrate")
                refused = True
            elif state == "occupied":
                print(f"{kind.upper()}: existing unversioned/invalid config; refusing overwrite")
                refused = True
            elif state == "same":
                if not verify_same(package, kind, home):
                    refused = True
                    state = "blocked"
            else:
                collisions = collision_paths(package, kind, home)
                if collisions:
                    print(f"{kind.upper()}: blocked; {len(collisions)} managed destinations exist")
                    for path in collisions[:10]:
                        print(f"  collision: {path}")
                    refused = True
                    state = "blocked"
                else:
                    config_candidate(package, kind, home)
                    source_files(package, kind)
            records.append((kind, package, state))
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"setup preflight failed: {exc}", file=sys.stderr)
        return 2

    fresh = [(kind, package) for kind, package, state in records if state == "fresh"]
    if args.dry_run:
        print(f"dry-run: fresh_endpoints={len(fresh)}; no files changed")
        print("hook trust: unchanged; review changed hook contents in Codex when prompted")
        return 2 if refused or len(records) != len(kinds) else 0
    if not fresh:
        label = "setup refused" if refused else "same-version: selected endpoints verified"
        print(f"{label}; no files changed")
        print("hook trust: unchanged; review changed hook contents in Codex when prompted")
        return 2 if refused or len(records) != len(kinds) else 0

    written: list[Path] = []
    roots = (home / ".claude", home / ".codex", home / ".agents")
    roots_existed = {root: root.exists() for root in roots}
    try:
        config_writes = 0
        for kind, package in fresh:
            destination = home / (".claude/settings.json" if kind == "cc" else ".codex/config.toml")
            source = package / ("settings.json" if kind == "cc" else "config.toml")
            atomic_write(
                destination,
                config_candidate(package, kind, home),
                stat.S_IMODE(source.stat().st_mode),
            )
            written.append(destination)
            config_writes += 1
            if config_writes == 1:
                maybe_fail("after-first-config")

        asset_writes = 0
        for kind, package in fresh:
            for source, relative in source_files(package, kind):
                destination = home / relative
                atomic_write(destination, source.read_bytes(), stat.S_IMODE(source.stat().st_mode))
                written.append(destination)
                asset_writes += 1
                if asset_writes == 1:
                    maybe_fail("asset-copy")

        if not all(verify_same(package, kind, home) for kind, package in fresh):
            raise OSError("post-install verification failed")
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        rollback_failures: list[str] = []
        for path in reversed(written):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                rollback_failures.append(str(path))
        for root in sorted(roots, key=lambda item: len(item.parts), reverse=True):
            if roots_existed[root]:
                continue
            try:
                for directory in sorted(
                    (path for path in root.rglob("*") if path.is_dir()),
                    key=lambda item: len(item.parts),
                    reverse=True,
                ) if root.exists() else []:
                    directory.rmdir()
                root.rmdir()
            except OSError:
                pass
        if rollback_failures:
            print(f"setup failed; rollback incomplete ({len(rollback_failures)} files): {exc}", file=sys.stderr)
            return 3
        print(f"setup failed; rollback complete: {exc}", file=sys.stderr)
        return 2

    print(f"setup complete: fresh_endpoints={len(fresh)} version={VERSION}")
    print("hook trust: unchanged; review changed hook contents in Codex when prompted")
    return 2 if refused or len(records) != len(kinds) else 0


if __name__ == "__main__":
    sys.exit(main())
