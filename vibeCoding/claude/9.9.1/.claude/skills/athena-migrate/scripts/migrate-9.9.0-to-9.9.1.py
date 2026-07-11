#!/usr/bin/env python3
"""Transactional Athena 9.9.0 -> 9.9.1 migration for CC and CX."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import sys
import tempfile
import tomllib
from typing import Any


FROM_VERSION = "9.9.0"
TO_VERSION = "9.9.1"
JUNK_DIRS = {"__pycache__", "tmp"}
JUNK_FILES = {".DS_Store"}
OLD_CUSTOM_PROVIDER = {
    "name": "custom_openai",
    "base_url": "",
    "wire_api": "responses",
    "requires_openai_auth": True,
}


class MigrationError(RuntimeError):
    """A refused or failed migration whose rollback, if needed, is complete."""


class InjectedFailure(MigrationError):
    """Test-only deterministic fault injection."""


@dataclass(frozen=True)
class AssetUnit:
    source: Path
    target: Path


@dataclass
class EndpointPlan:
    kind: str
    package: Path
    state: str
    file_candidates: dict[Path, bytes]
    units: list[AssetUnit]
    changed_files: list[Path] = field(default_factory=list)
    changed_units: list[AssetUnit] = field(default_factory=list)
    legacy_skill_dirs: list[Path] = field(default_factory=list)
    legacy_residue: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class Snapshot:
    target: Path
    existed: bool
    kind: str
    backup: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transactionally migrate Athena endpoints from 9.9.0 to 9.9.1."
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--cc-package", type=Path)
    parser.add_argument("--cx-package", type=Path)
    parser.add_argument("--only", choices=("cc", "cx", "both"), default="both")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Single transaction backup directory (must be absent or empty).",
    )
    return parser.parse_args()


def selected_kinds(only: str) -> tuple[str, ...]:
    return ("cc", "cx") if only == "both" else (only,)


def package_marker(kind: str) -> str:
    return "settings.json" if kind == "cc" else "config.toml"


def normalize_package(path: Path, kind: str) -> Path | None:
    hidden = ".claude" if kind == "cc" else ".codex"
    expanded = path.expanduser().resolve()
    for candidate in (expanded, expanded / hidden):
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
    roots: list[Path] = []
    if args.repo_root:
        roots.append(args.repo_root)
    roots.extend((Path.cwd(), *Path.cwd().parents, Path(__file__), *Path(__file__).parents))
    for root in roots:
        candidates.extend(
            (
                root / "vibeCoding" / family / TO_VERSION / hidden,
                root / family / TO_VERSION / hidden,
                root / hidden,
            )
        )
    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.expanduser())
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def locate_package(kind: str, args: argparse.Namespace) -> Path:
    for candidate in package_candidates(kind, args):
        normalized = normalize_package(candidate, kind)
        if normalized:
            return normalized
    option = "--cc-package" if kind == "cc" else "--cx-package"
    raise MigrationError(f"{kind.upper()} release package not found; pass {option} or --repo-root")


def locate_old_package(kind: str, args: argparse.Namespace, current: Path) -> Path | None:
    family = "claude" if kind == "cc" else "codex"
    hidden = ".claude" if kind == "cc" else ".codex"
    candidates: list[Path] = []
    if args.repo_root:
        candidates.append(args.repo_root / "vibeCoding" / family / FROM_VERSION / hidden)
    candidates.append(current.parent.parent / FROM_VERSION / hidden)
    for candidate in candidates:
        normalized = normalize_package(candidate, kind)
        if normalized is None:
            continue
        try:
            if kind == "cc":
                parsed = load_json_object(
                    normalized / "settings.json", "old CC package settings"
                )
            else:
                parsed = tomllib.loads(
                    (normalized / "config.toml").read_text(encoding="utf-8")
                )
        except (MigrationError, OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError):
            continue
        if endpoint_version(kind, parsed) == FROM_VERSION:
            return normalized
    return None


def is_junk(relative: Path) -> bool:
    return (
        any(part in JUNK_DIRS for part in relative.parts)
        or relative.name in JUNK_FILES
        or relative.suffix == ".pyc"
    )


def clean_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if is_junk(relative):
            continue
        if path.is_symlink():
            raise MigrationError(f"release package contains unsupported symlink: {path}")
        if path.is_file():
            files.append(path)
    return files


def validate_source(path: Path) -> None:
    try:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".toml":
            tomllib.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".py":
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (OSError, UnicodeError, ValueError, SyntaxError, tomllib.TOMLDecodeError) as exc:
        raise MigrationError(f"release source validation failed: {path}: {exc}") from exc


def source_units(package: Path, kind: str, home: Path) -> list[AssetUnit]:
    if kind == "cc":
        file_names = ("CLAUDE.md", "statusline-command.sh")
        directory_names = ("rules", "hooks", "agents", "skills")
        target_root = home / ".claude"
    else:
        file_names = ("AGENTS.md",)
        directory_names = ("hooks", "agents", "standards")
        target_root = home / ".codex"

    units: list[AssetUnit] = []
    for name in file_names:
        source = package / name
        if not source.is_file() or is_junk(Path(name)):
            continue
        validate_source(source)
        units.append(AssetUnit(source, target_root / name))

    for name in directory_names:
        source_root = package / name
        if not source_root.is_dir():
            continue
        for child in sorted(source_root.iterdir()):
            if is_junk(Path(child.name)):
                continue
            if child.is_symlink():
                raise MigrationError(f"release package contains unsupported symlink: {child}")
            if child.is_file():
                validate_source(child)
                units.append(AssetUnit(child, target_root / name / child.name))
            elif child.is_dir() and clean_files(child):
                for file in clean_files(child):
                    validate_source(file)
                units.append(AssetUnit(child, target_root / name / child.name))

    if kind == "cx":
        skill_root = package / "skills"
        if not skill_root.is_dir():
            raise MigrationError("CX release package has no skills directory")
        for skill in sorted(skill_root.iterdir()):
            if is_junk(Path(skill.name)) or not skill.is_dir():
                continue
            files = clean_files(skill)
            if not files:
                continue
            for file in files:
                validate_source(file)
            units.append(AssetUnit(skill, home / ".agents" / "skills" / skill.name))
    return units


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_signature(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in clean_files(root)
    }


def strict_tree_signature(root: Path | None) -> dict[str, str] | None:
    """Return every relative path and file hash, refusing links or special files."""
    if root is None or not root.is_dir() or root.is_symlink():
        return None
    signature: dict[str, str] = {".": "dir"}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            return None
        if path.is_dir():
            signature[relative] = "dir"
        elif path.is_file():
            signature[relative] = f"file:{sha256(path)}"
        else:
            return None
    return signature


def unit_matches(unit: AssetUnit) -> bool:
    if unit.source.is_file():
        return unit.target.is_file() and sha256(unit.source) == sha256(unit.target)
    return unit.target.is_dir() and tree_signature(unit.source) == tree_signature(unit.target)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def release_hook_allowlist(package: Path, kind: str) -> frozenset[str]:
    suffix = ".cjs" if kind == "cc" else ".py"
    hooks = package / "hooks"
    if not hooks.is_dir():
        raise MigrationError(f"{kind.upper()} release package has no hooks directory")
    names = {
        path.name
        for path in hooks.iterdir()
        if path.is_file() and not path.is_symlink() and path.suffix == suffix
    }
    if not names:
        raise MigrationError(f"{kind.upper()} release hook allowlist is empty")
    return frozenset(names)


def athena_hook(hook: Any, kind: str, allowlist: frozenset[str]) -> bool:
    if not isinstance(hook, dict) or not isinstance(hook.get("command"), str):
        return False
    marker = "/.claude/hooks/" if kind == "cc" else "/.codex/hooks/"
    try:
        tokens = shlex.split(hook["command"])
    except ValueError:
        return False
    for token in tokens:
        normalized = token.replace("\\", "/")
        if marker not in normalized:
            continue
        filename = normalized.rsplit("/", 1)[-1]
        if filename in allowlist and normalized.endswith(f"{marker}{filename}"):
            return True
    return False


def filtered_installed_group(
    group: Any, kind: str, allowlist: frozenset[str]
) -> tuple[Any, bool]:
    if not isinstance(group, dict):
        return copy.deepcopy(group), False
    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return copy.deepcopy(group), False
    remaining = [
        copy.deepcopy(hook)
        for hook in hooks
        if not athena_hook(hook, kind, allowlist)
    ]
    preserved = copy.deepcopy(group)
    preserved["hooks"] = remaining
    return preserved, len(remaining) != len(hooks)


def packaged_athena_group(
    group: Any, kind: str, allowlist: frozenset[str]
) -> dict[str, Any] | None:
    if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
        return None
    owned = [
        copy.deepcopy(hook)
        for hook in group["hooks"]
        if athena_hook(hook, kind, allowlist)
    ]
    if not owned:
        return None
    result = copy.deepcopy(group)
    result["hooks"] = owned
    return result


def merge_hook_maps(
    installed: Any,
    packaged: Any,
    kind: str,
    allowlist: frozenset[str],
) -> dict[str, Any]:
    if not isinstance(installed, dict) or not isinstance(packaged, dict):
        raise MigrationError(f"{kind.upper()} hooks must be JSON objects")
    merged: dict[str, Any] = copy.deepcopy(installed)
    for event in sorted(set(installed) | set(packaged)):
        current_groups = installed.get(event, [])
        package_groups = packaged.get(event, [])
        if not isinstance(current_groups, list) or not isinstance(package_groups, list):
            raise MigrationError(f"{kind.upper()} hook event {event} must be an array")
        groups: list[Any] = []
        emptied_owned_groups: set[int] = set()
        for group in current_groups:
            preserved, removed_owned = filtered_installed_group(group, kind, allowlist)
            groups.append(preserved)
            if (
                removed_owned
                and isinstance(preserved, dict)
                and isinstance(preserved.get("hooks"), list)
                and not preserved["hooks"]
            ):
                emptied_owned_groups.add(id(preserved))
        for group in package_groups:
            owned = packaged_athena_group(group, kind, allowlist)
            if owned is None:
                continue
            matcher = owned.get("matcher")
            destination = next(
                (
                    existing
                    for existing in groups
                    if isinstance(existing, dict)
                    and existing.get("matcher") == matcher
                    and isinstance(existing.get("hooks"), list)
                ),
                None,
            )
            if destination is None:
                groups.append(owned)
            else:
                destination["hooks"].extend(owned["hooks"])
        groups = [
            group
            for group in groups
            if not (
                id(group) in emptied_owned_groups
                and isinstance(group, dict)
                and not group.get("hooks")
            )
        ]
        if groups:
            merged[event] = groups
        else:
            merged.pop(event, None)
    return merged


def merge_cc_settings(
    installed: dict[str, Any],
    old: dict[str, Any],
    packaged: dict[str, Any],
    allowlist: frozenset[str],
) -> dict[str, Any]:
    merged = copy.deepcopy(installed)

    # Three-way scalar merge: update only values that still equal 9.9.0's
    # shipped default. User values that differ from the baseline are retained.
    for key in ("model", "effortLevel", "fallbackModel", "worktree", "statusLine"):
        if key in old:
            if installed.get(key) == old.get(key) and key in packaged:
                merged[key] = copy.deepcopy(packaged[key])
        elif key not in installed and key in packaged:
            merged[key] = copy.deepcopy(packaged[key])

    old_env = old.get("env") if isinstance(old.get("env"), dict) else {}
    target_env = packaged.get("env") if isinstance(packaged.get("env"), dict) else {}
    installed_env = installed.get("env") if isinstance(installed.get("env"), dict) else {}
    env = copy.deepcopy(installed_env)
    for key, old_value in old_env.items():
        if installed_env.get(key) != old_value:
            continue
        if key in target_env:
            env[key] = copy.deepcopy(target_env[key])
        else:
            env.pop(key, None)
    for key, target_value in target_env.items():
        if key not in old_env and key not in installed_env:
            env[key] = copy.deepcopy(target_value)
    env["VIBECODING_ATHENA_VERSION"] = TO_VERSION
    merged["env"] = env

    old_permissions = old.get("permissions") if isinstance(old.get("permissions"), dict) else {}
    target_permissions = packaged.get("permissions") if isinstance(packaged.get("permissions"), dict) else {}
    installed_permissions = installed.get("permissions") if isinstance(installed.get("permissions"), dict) else {}
    permissions = copy.deepcopy(installed_permissions)
    if installed_permissions.get("defaultMode") == old_permissions.get("defaultMode"):
        permissions["defaultMode"] = target_permissions.get("defaultMode", installed_permissions.get("defaultMode"))
    for list_key in ("allow", "deny"):
        old_items = old_permissions.get(list_key) if isinstance(old_permissions.get(list_key), list) else []
        target_items = target_permissions.get(list_key) if isinstance(target_permissions.get(list_key), list) else []
        installed_items = installed_permissions.get(list_key) if isinstance(installed_permissions.get(list_key), list) else []
        user_items = [item for item in installed_items if item not in old_items]
        permissions[list_key] = list(dict.fromkeys([*copy.deepcopy(target_items), *copy.deepcopy(user_items)]))
    merged["permissions"] = permissions
    merged["hooks"] = merge_hook_maps(
        installed.get("hooks", {}), packaged.get("hooks", {}), "cc", allowlist
    )
    return merged


def merge_cx_hooks(
    installed: dict[str, Any],
    packaged: dict[str, Any],
    allowlist: frozenset[str],
) -> dict[str, Any]:
    merged = copy.deepcopy(installed)
    merged["hooks"] = merge_hook_maps(
        installed.get("hooks", {}), packaged.get("hooks", {}), "cx", allowlist
    )
    return merged


def decode_string(value: str) -> str:
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    raise MigrationError("expected a quoted TOML string")


def assignment(line: str, key: str) -> tuple[str, str, str] | None:
    pattern = rf"^(\s*{re.escape(key)}\s*=\s*)(\"(?:[^\"\\]|\\.)*\"|'[^']*')(\s*(?:#.*)?(?:\r?\n)?)$"
    match = re.match(pattern, line)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def replace_string(line: str, key: str, value: str) -> str:
    parts = assignment(line, key)
    if parts is None:
        raise MigrationError(f"cannot safely rewrite {key}")
    prefix, _, suffix = parts
    return f"{prefix}{json.dumps(value)}{suffix}"


def numeric_value(line: str, key: str) -> int | None:
    match = re.match(rf"^\s*{re.escape(key)}\s*=\s*(\d+)\s*(?:#.*)?(?:\r?\n)?$", line)
    return int(match.group(1)) if match else None


def skill_name(path: str) -> str | None:
    pure = PurePosixPath(path.replace("\\", "/"))
    if pure.name != "SKILL.md" or len(pure.parts) < 2:
        return None
    return pure.parent.name


def managed_skill_order(package: Path) -> tuple[str, ...]:
    config = tomllib.loads((package / "config.toml").read_text(encoding="utf-8"))
    available = {
        path.name
        for path in (package / "skills").iterdir()
        if path.is_dir() and not is_junk(Path(path.name))
    }
    ordered: list[str] = []
    for entry in config.get("skills", {}).get("config", []):
        name = skill_name(str(entry.get("path", "")))
        if name in available and name not in ordered:
            ordered.append(name)
    ordered.extend(sorted(available - set(ordered)))
    return tuple(ordered)


def migrate_text(
    source: str,
    parsed: dict[str, Any],
    fallback_skill_root: str,
    managed_order: tuple[str, ...],
) -> tuple[str, dict[str, int]]:
    current = (
        parsed.get("shell_environment_policy", {})
        .get("set", {})
        .get("VIBECODING_VERSION")
    )
    if current not in {FROM_VERSION, TO_VERSION}:
        raise MigrationError("CX endpoint is not on a supported migration version")

    managed_skills = frozenset(managed_order)
    custom_value = parsed.get("model_providers", {}).get("custom_openai", {})
    custom_provider = custom_value if isinstance(custom_value, dict) else {}
    replace_old_defaults = (
        parsed.get("model_provider") == "custom_openai"
        and isinstance(custom_value, dict)
        and custom_provider.get("base_url") == ""
        and parsed.get("model") == "gpt-5.5"
    )
    nux_value = parsed.get("tui", {}).get("model_availability_nux", {})
    nux = nux_value if isinstance(nux_value, dict) else {}
    remove_nux_entry = replace_old_defaults and nux.get("gpt-5.5") == 4
    remove_nux_table = remove_nux_entry and nux == {"gpt-5.5": 4}
    remove_custom_provider = replace_old_defaults and custom_provider == OLD_CUSTOM_PROVIDER

    stats = {
        "model": 0,
        "defaults_removed": 0,
        "version": 0,
        "skill_paths": 0,
        "skill_entries": 0,
        "nux_entries_removed": 0,
        "provider_tables_removed": 0,
    }
    lines = source.splitlines(keepends=True)
    output: list[str] = []
    table = ""
    seen_version = 0
    configured_managed: set[str] = set()
    skill_root: str | None = None
    skip_table = False

    for line in lines:
        header = re.match(r"^\s*(\[\[?[^]]+\]\]?)\s*(?:#.*)?(?:\r?\n)?$", line)
        if header:
            table = header.group(1)
            skip_table = (
                table == "[tui.model_availability_nux]" and remove_nux_table
            ) or (
                table == "[model_providers.custom_openai]" and remove_custom_provider
            )
            if skip_table:
                key = "nux_entries_removed" if "model_availability" in table else "provider_tables_removed"
                stats[key] += 1
                continue
            output.append(line)
            continue
        if skip_table:
            continue

        if table == "":
            if assignment(line, "model_provider") and replace_old_defaults:
                line = replace_string(line, "model_provider", "openai")
                stats["model"] += 1
            elif assignment(line, "model") and replace_old_defaults:
                line = replace_string(line, "model", "gpt-5.6-sol")
                stats["model"] += 1
            elif replace_old_defaults and numeric_value(line, "model_context_window") == 1_000_000:
                stats["defaults_removed"] += 1
                continue
            elif replace_old_defaults and numeric_value(line, "model_auto_compact_token_limit") == 900_000:
                stats["defaults_removed"] += 1
                continue

        if table == "[shell_environment_policy.set]" and assignment(line, "VIBECODING_VERSION"):
            seen_version += 1
            parts = assignment(line, "VIBECODING_VERSION")
            assert parts is not None
            if decode_string(parts[1]) != TO_VERSION:
                line = replace_string(line, "VIBECODING_VERSION", TO_VERSION)
                stats["version"] += 1

        if (
            table == "[tui.model_availability_nux]"
            and remove_nux_entry
            and numeric_value(line, '"gpt-5.5"') == 4
        ):
            stats["nux_entries_removed"] += 1
            continue

        if table == "[[skills.config]]" and assignment(line, "path"):
            parts = assignment(line, "path")
            assert parts is not None
            path = decode_string(parts[1])
            name = skill_name(path)
            if name in managed_skills:
                configured_managed.add(name)
                normalized = path.replace("\\", "/")
                if "/.codex/skills/" in normalized:
                    new_path = normalized.replace("/.codex/skills/", "/.agents/skills/")
                    line = replace_string(line, "path", new_path)
                    stats["skill_paths"] += 1
                    normalized = new_path
                marker = f"/.agents/skills/{name}/SKILL.md"
                if normalized.endswith(marker):
                    skill_root = normalized[: -len(f"/{name}/SKILL.md")]
        output.append(line)

    if seen_version != 1:
        raise MigrationError("Athena CX version marker is missing or duplicated")

    missing = [name for name in managed_order if name not in configured_managed]
    if missing:
        root = skill_root or fallback_skill_root
        last_header = max(
            (index for index, line in enumerate(output) if line.strip() == "[[skills.config]]"),
            default=-1,
        )
        insert_at = len(output)
        for index in range(last_header + 1 if last_header >= 0 else 0, len(output)):
            if output[index].lstrip().startswith("["):
                insert_at = index
                break
        additions: list[str] = []
        if insert_at > 0 and output[insert_at - 1].strip():
            additions.append("\n")
        for name in missing:
            additions.extend(
                ("[[skills.config]]\n", f'path = "{root}/{name}/SKILL.md"\n', "enabled = true\n\n")
            )
        output[insert_at:insert_at] = additions
        stats["skill_entries"] = len(missing)

    migrated = "".join(output)
    try:
        tomllib.loads(migrated)
    except tomllib.TOMLDecodeError as exc:
        raise MigrationError(f"generated CX TOML failed validation: {exc}") from exc
    return migrated, stats


def endpoint_version(kind: str, parsed: dict[str, Any]) -> str | None:
    if kind == "cc":
        value = parsed.get("env", {}).get("VIBECODING_ATHENA_VERSION")
    else:
        value = (
            parsed.get("shell_environment_policy", {})
            .get("set", {})
            .get("VIBECODING_VERSION")
        )
    return value if isinstance(value, str) else None


def exact_legacy_skill_dirs(
    parsed: dict[str, Any], home: Path, managed_names: set[str]
) -> list[Path]:
    root = (home / ".codex" / "skills").resolve()
    result: list[Path] = []
    for entry in parsed.get("skills", {}).get("config", []):
        raw = str(entry.get("path", ""))
        name = skill_name(raw)
        if name not in managed_names:
            continue
        if raw.startswith("~/"):
            candidate = home / raw[2:]
        else:
            candidate = Path(raw.replace("<USER_HOME>", home.as_posix()))
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        expected = root / name / "SKILL.md"
        if resolved == expected:
            result.append(expected.parent)
    return sorted(set(result))


def classify_legacy_skill_dirs(
    parsed: dict[str, Any],
    home: Path,
    managed_names: set[str],
    old_package: Path | None,
) -> tuple[list[Path], list[Path]]:
    """Add unregistered old skills only when their complete old-package signature matches."""
    registered = exact_legacy_skill_dirs(parsed, home, managed_names)
    registered_set = set(registered)
    legacy_root = home / ".codex" / "skills"
    removable = list(registered)
    residue: list[Path] = []
    for name in sorted(managed_names):
        installed = (legacy_root / name).resolve()
        if installed in registered_set or not installed.exists():
            continue
        counterpart = old_package / "skills" / name if old_package else None
        installed_signature = strict_tree_signature(installed)
        package_signature = strict_tree_signature(counterpart)
        if installed_signature is not None and installed_signature == package_signature:
            removable.append(installed)
        else:
            residue.append(installed)
    return sorted(set(removable)), sorted(set(residue))


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise MigrationError(f"{label} is unreadable or invalid") from exc
    if not isinstance(value, dict):
        raise MigrationError(f"{label} must be a JSON object")
    return value


def make_plan(
    kind: str, package: Path, home: Path, old_package: Path | None = None
) -> EndpointPlan:
    units = source_units(package, kind, home)
    if not units:
        raise MigrationError(f"{kind.upper()} release manifest is empty")

    if kind == "cc":
        if old_package is None:
            raise MigrationError("CC 9.9.0 package baseline is required for safe three-way migration")
        config = home / ".claude" / "settings.json"
        installed = load_json_object(config, "CC settings")
        packaged = load_json_object(package / "settings.json", "CC package settings")
        old_defaults = load_json_object(old_package / "settings.json", "old CC package settings")
        hook_allowlist = release_hook_allowlist(package, kind) | release_hook_allowlist(old_package, kind)
        version = endpoint_version(kind, installed)
        if version not in {FROM_VERSION, TO_VERSION}:
            raise MigrationError("CC endpoint is not on a supported migration version")
        files = {
            config: json_bytes(
                merge_cc_settings(installed, old_defaults, packaged, hook_allowlist)
            )
        }
        legacy: list[Path] = []
        residue: list[Path] = []
    else:
        config = home / ".codex" / "config.toml"
        hooks = home / ".codex" / "hooks.json"
        try:
            source = config.read_text(encoding="utf-8")
            installed = tomllib.loads(source)
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            raise MigrationError("CX config is unreadable or invalid") from exc
        version = endpoint_version(kind, installed)
        if version not in {FROM_VERSION, TO_VERSION}:
            raise MigrationError("CX endpoint is not on a supported migration version")
        order = managed_skill_order(package)
        migrated, _ = migrate_text(
            source, installed, (home / ".agents" / "skills").as_posix(), order
        )
        installed_hooks = load_json_object(hooks, "CX hooks")
        package_hooks = load_json_object(package / "hooks.json", "CX package hooks")
        hook_allowlist = release_hook_allowlist(package, kind)
        files = {
            config: migrated.encode("utf-8"),
            hooks: json_bytes(
                merge_cx_hooks(installed_hooks, package_hooks, hook_allowlist)
            ),
        }
        legacy, residue = classify_legacy_skill_dirs(
            installed, home, set(order), old_package
        )

    state = "old" if version == FROM_VERSION else "current"
    changed_files = [path for path, content in files.items() if not path.is_file() or path.read_bytes() != content]
    changed_units = [unit for unit in units if not unit_matches(unit)]
    existing_legacy = [path for path in legacy if path.exists()]
    plan = EndpointPlan(
        kind=kind,
        package=package,
        state=state,
        file_candidates=files,
        units=units,
        changed_files=changed_files,
        changed_units=changed_units,
        legacy_skill_dirs=existing_legacy,
        legacy_residue=residue,
    )
    if state == "current" and (changed_files or changed_units or existing_legacy):
        raise MigrationError(f"{kind.upper()} v9.9.1 verification found drift; refusing repair")
    return plan


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def dedupe_targets(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    for path in sorted(set(paths), key=lambda item: (len(item.parts), str(item))):
        if any(path == parent or parent in path.parents for parent in result):
            continue
        result.append(path)
    return result


def transaction_backup_dir(args: argparse.Namespace, home: Path) -> Path:
    if args.backup_dir:
        return args.backup_dir.expanduser().resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return home / ".athena-backups" / TO_VERSION / stamp


def make_backups(targets: list[Path], backup_root: Path) -> list[Snapshot]:
    if backup_root.exists() and any(backup_root.iterdir()):
        raise MigrationError("backup directory must be absent or empty")
    backup_root.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_root, 0o700)
    snapshots: list[Snapshot] = []
    manifest: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        existed = target.exists() or target.is_symlink()
        kind = "dir" if target.is_dir() and not target.is_symlink() else "file"
        backup = backup_root / f"item-{index:04d}" if existed else None
        if existed:
            if kind == "dir":
                shutil.copytree(target, backup, symlinks=True)
            else:
                assert backup is not None
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup, follow_symlinks=False)
        snapshots.append(Snapshot(target, existed, kind, backup))
        manifest.append({"target": str(target), "existed": existed, "kind": kind, "backup": backup.name if backup else None})
    (backup_root / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "items": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    return snapshots


def rollback(snapshots: list[Snapshot]) -> list[str]:
    failures: list[str] = []
    for snapshot in reversed(snapshots):
        try:
            remove_path(snapshot.target)
            if snapshot.existed:
                assert snapshot.backup is not None
                snapshot.target.parent.mkdir(parents=True, exist_ok=True)
                if snapshot.kind == "dir":
                    shutil.copytree(snapshot.backup, snapshot.target, symlinks=True)
                else:
                    shutil.copy2(snapshot.backup, snapshot.target, follow_symlinks=False)
        except OSError:
            failures.append(str(snapshot.target))
    return failures


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
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


def copy_clean_directory(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for file in clean_files(source):
        relative = file.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)


def sync_unit(unit: AssetUnit) -> None:
    unit.target.parent.mkdir(parents=True, exist_ok=True)
    if unit.source.is_file():
        atomic_write(unit.target, unit.source.read_bytes())
        os.chmod(unit.target, stat.S_IMODE(unit.source.stat().st_mode))
        return

    staging_root = Path(tempfile.mkdtemp(prefix=f".{unit.target.name}.stage-", dir=unit.target.parent))
    payload = staging_root / "payload"
    displaced = staging_root / "displaced"
    try:
        copy_clean_directory(unit.source, payload)
        if unit.target.exists() or unit.target.is_symlink():
            os.replace(unit.target, displaced)
        try:
            os.replace(payload, unit.target)
        except OSError:
            if displaced.exists() and not unit.target.exists():
                os.replace(displaced, unit.target)
            raise
        remove_path(displaced)
    finally:
        remove_path(staging_root)


def maybe_fail(point: str) -> None:
    if os.environ.get("ATHENA_TEST_FAIL_AT") == point:
        raise InjectedFailure(f"injected failure at {point}")


def verify_plan(plan: EndpointPlan) -> None:
    for path, expected in plan.file_candidates.items():
        if not path.is_file() or path.read_bytes() != expected:
            raise MigrationError(f"{plan.kind.upper()} post-verify config mismatch")
    for unit in plan.units:
        if not unit_matches(unit):
            raise MigrationError(f"{plan.kind.upper()} post-verify asset mismatch: {unit.target}")
    if plan.kind == "cc":
        parsed = load_json_object(next(iter(plan.file_candidates)), "CC settings")
    else:
        config_path = next(path for path in plan.file_candidates if path.name == "config.toml")
        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if endpoint_version(plan.kind, parsed) != TO_VERSION:
        raise MigrationError(f"{plan.kind.upper()} post-verify version mismatch")


def changed_targets(plans: list[EndpointPlan]) -> list[Path]:
    paths: list[Path] = []
    for plan in plans:
        paths.extend(plan.changed_files)
        paths.extend(unit.target for unit in plan.changed_units)
        paths.extend(plan.legacy_skill_dirs)
    return dedupe_targets(paths)


def main() -> int:
    args = parse_args()
    home = args.home.expanduser().resolve()
    try:
        plans: list[EndpointPlan] = []
        for kind in selected_kinds(args.only):
            package = locate_package(kind, args)
            old_package = locate_old_package(kind, args, package)
            plans.append(make_plan(kind, package, home, old_package))
    except (MigrationError, OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"migration refused: {exc}", file=sys.stderr)
        return 2

    old_plans = [plan for plan in plans if plan.state == "old"]
    for plan in plans:
        print(
            f"{plan.kind.upper()}: state={plan.state} files={len(plan.changed_files)} "
            f"assets={len(plan.changed_units)} legacy={len(plan.legacy_skill_dirs)} "
            f"residue={len(plan.legacy_residue)}"
        )
        for residue in plan.legacy_residue:
            print(f"  preserved legacy residue: {residue}")
    if not old_plans:
        print("already current: selected endpoints verified; no backup or write")
        return 0
    if args.dry_run:
        print("dry-run: preflight passed; no backup or write")
        return 0

    targets = changed_targets(old_plans)
    backup_root = transaction_backup_dir(args, home)
    snapshots: list[Snapshot] = []
    try:
        snapshots = make_backups(targets, backup_root)
        maybe_fail("after-backup")

        config_writes = 0
        for plan in old_plans:
            for path in plan.changed_files:
                atomic_write(path, plan.file_candidates[path])
                config_writes += 1
                if config_writes == 1:
                    maybe_fail("after-first-config")

        asset_writes = 0
        for plan in old_plans:
            for unit in plan.changed_units:
                sync_unit(unit)
                asset_writes += 1
                if asset_writes == 1:
                    maybe_fail("asset-copy")

        for plan in plans:
            verify_plan(plan)
        maybe_fail("post-verify")

        for plan in old_plans:
            for legacy in plan.legacy_skill_dirs:
                remove_path(legacy)
        if any(path.exists() for plan in old_plans for path in plan.legacy_skill_dirs):
            raise MigrationError("legacy Athena skill cleanup did not complete")
    except (MigrationError, OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        failures = rollback(snapshots) if snapshots else []
        if failures:
            print(
                f"migration failed and rollback is incomplete ({len(failures)} paths): {exc}",
                file=sys.stderr,
            )
            return 3
        print(f"migration failed; rollback complete: {exc}", file=sys.stderr)
        return 2

    print(
        f"migration complete: endpoints={len(old_plans)} backup={backup_root} "
        "hook-trust=unchanged-review-updated-hooks-when-prompted"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
