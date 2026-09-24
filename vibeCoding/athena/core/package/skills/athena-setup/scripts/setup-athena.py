#!/usr/bin/env python3
"""Install or migrate selected Athena 9.9.9 assets while preserving user settings."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import sys
import re
import uuid
from datetime import datetime, timezone

if sys.version_info < (3, 9):
    raise SystemExit(
        f"Athena setup 需要 Python 3.9+, 当前 {sys.version.split()[0]}。\n"
        "macOS 自带 python3 常为 3.9 以下, 请用 `brew install python@3.12` 后重试, "
        "或显式指定解释器: python3.12 setup-athena.py ..."
    )

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # 3.9 / 3.10 回退
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        raise SystemExit(
            "缺少 TOML 解析器。Python 3.11+ 自带 tomllib; 3.9/3.10 请先 `pip install tomli`。\n"
            "Athena 用它校验 config.toml, 跳过校验会让坏配置直接落到 ~/.codex/。"
        )


VERSION = "9.9.9"
JUNK_DIRS = {"__pycache__", "tmp"}
JUNK_FILES = {".DS_Store"}
# Never install over chat history. Fresh or already-installed machines keep these.
PRESERVED_SESSION_PREFIXES = (
    ".claude/sessions/",
    ".claude/file-history/",
    ".claude/projects/",
    ".claude/history.jsonl",
    ".claude/legacy-sessions/",
    ".codex/sessions/",
    ".codex/archived_sessions/",
    ".codex/history.jsonl",
)


class SetupError(ValueError):
    """Policy diagnostic containing only paths or fixed text, never configuration values."""



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--cc-package", type=Path)
    parser.add_argument("--cx-package", type=Path)
    parser.add_argument("--only", choices=("cc", "cx", "both"),
                        default="cc" if ".claude" in Path(__file__).parts else "cx")
    parser.add_argument("--migrate", action="store_true", help="upgrade managed files using a baseline; preserve user overrides")
    parser.add_argument("--baseline-cc-package", type=Path)
    parser.add_argument("--baseline-cx-package", type=Path)
    parser.add_argument("--rollback", type=Path, help="restore a recorded transaction after checking later user edits")
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


MANAGED_DENY = (
    "Agent(critic)",
    "Agent(evaluator)",
    "Agent(spec-compliance)",
)
REQUIRED_ASSETS = {
    "cc": (
        ".claude/hooks/delivery-gate.cjs",
        ".claude/hooks/_review-binding.cjs",
        ".claude/hooks/_input-binding.cjs",
        ".claude/hooks/pre-bash-guard.cjs",
    ),
    "cx": (
        ".codex/hooks/delivery-gate.py",
        ".codex/hooks/_review_binding.py",
        ".codex/hooks/_input_binding.py",
        ".agents/skills/pace/scripts/review-binding.py",
    ),
}


def managed_complete(kind: str, home: Path) -> bool:
    return all((home / relative).is_file() for relative in REQUIRED_ASSETS[kind])


def read_version(kind: str, home: Path) -> tuple[str, str | None]:
    config = home / (".claude/settings.json" if kind == "cc" else ".codex/config.toml")
    if not config.exists():
        return "fresh", None
    try:
        if kind == "cc":
            data = json.loads(config.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("env", {}), dict):
                return "occupied", None
            version = data.get("env", {}).get("VIBECODING_ATHENA_VERSION")
        else:
            data = tomllib.loads(config.read_text(encoding="utf-8"))
            version = data.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION")
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return "occupied", None
    if version == VERSION:
        if not managed_complete(kind, home):
            return "incomplete", version
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
        raise SetupError(f"unsupported package symlink: {path}")
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
        if source.is_symlink():
            raise SetupError('package symlink is unsupported')
        if source.is_file():
            if not is_junk(Path(name)):
                validate_source(source)
                files.append((source, target_root / name))
        elif source.is_dir():
            if any(path.is_symlink() for path in source.rglob('*')):
                raise SetupError('package directory contains symlink')
            for child in sorted(path for path in source.rglob("*") if path.is_file()):
                relative = child.relative_to(source)
                if is_junk(relative):
                    continue
                validate_source(child)
                files.append((child, target_root / name / relative))
    if kind == "cx":
        for skill in sorted(path for path in (package / "skills").iterdir() if path.is_dir()):
            if skill.is_symlink() or any(path.is_symlink() for path in skill.rglob('*')):
                raise SetupError('package skill contains symlink')
            for child in sorted(path for path in skill.rglob("*") if path.is_file()):
                relative = child.relative_to(skill)
                if is_junk(relative):
                    continue
                validate_source(child)
                files.append((child, Path(".agents/skills") / skill.name / relative))
    return files


def render_cx_config(package: Path, home: Path) -> bytes:
    text = (package / "config.toml").read_text(encoding="utf-8")
    config_home = home.as_posix()
    rendered = text.replace("<USER_HOME>", config_home)
    rendered = rendered.replace(
        f"{config_home}/.codex/skills/", f"{config_home}/.agents/skills/"
    )
    tomllib.loads(rendered)
    return rendered.encode("utf-8")


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


def merged_hooks(current, baseline, proposed):
    """Three-way JSON merge only for managed hook configuration."""
    if current == baseline:
        return proposed
    if isinstance(current, dict) and isinstance(proposed, dict):
        result = dict(current)
        old = baseline if isinstance(baseline, dict) else {}
        for key, value in proposed.items():
            if key not in current:
                result[key] = value
            else:
                result[key] = merged_hooks(current[key], old.get(key), value)
        for key in old.keys() - proposed.keys():
            if current.get(key) == old[key]:
                result.pop(key, None)
        return result
    if isinstance(current, list) and isinstance(proposed, list):
        old = baseline if isinstance(baseline, list) else []
        # A removed or modified managed group is user-owned; preserve that choice.
        if any(item not in current for item in old):
            return current
        def commands(value):
            if isinstance(value, dict):
                result = {value['command']} if isinstance(value.get('command'), str) else set()
                for child in value.values():
                    result.update(commands(child))
                return result
            if isinstance(value, list):
                return set().union(*(commands(child) for child in value))
            return set()
        result = [item for item in current if item not in old]
        for item in proposed:
            if item not in result and not any(commands(item) & commands(existing) for existing in result):
                result.append(item)
        return result
    return current


def apply_managed_cc_policy(current, old, proposed):
    """Apply 9.9.9 managed deny/plugin diffs without rewriting user-owned keys."""
    deny = current.setdefault('permissions', {}).setdefault('deny', [])
    if not isinstance(deny, list):
        raise SetupError('existing CC permissions.deny must be a list')
    proposed_deny = proposed.get('permissions', {}).get('deny', []) if isinstance(proposed.get('permissions'), dict) else []
    for item in MANAGED_DENY:
        if item in proposed_deny and item not in deny:
            deny.append(item)
    proposed_plugins = proposed.get('enabledPlugins') if isinstance(proposed.get('enabledPlugins'), dict) else {}
    old_plugins = old.get('enabledPlugins') if isinstance(old.get('enabledPlugins'), dict) else {}
    current_plugins = current.setdefault('enabledPlugins', {})
    if not isinstance(current_plugins, dict):
        raise SetupError('existing CC enabledPlugins must be an object')
    for key, value in proposed_plugins.items():
        if key not in current_plugins or current_plugins.get(key) == old_plugins.get(key):
            current_plugins[key] = value


def config_merge(package, baseline, kind, home):
    target = home / ('.claude/settings.json' if kind == 'cc' else '.codex/config.toml')
    if not target.exists():
        return config_candidate(package, kind, home)
    if kind == 'cc':
        current = json.loads(target.read_text())
        if not isinstance(current, dict) or not isinstance(current.get('env', {}), dict):
            raise SetupError('existing CC configuration must be an object with an env object')
        proposed = json.loads((package / 'settings.json').read_text())
        old = json.loads((baseline / 'settings.json').read_text()) if baseline else {}
        current.setdefault('env', {})['VIBECODING_ATHENA_VERSION'] = VERSION
        if baseline:
            current['hooks'] = merged_hooks(current.get('hooks', {}), old.get('hooks', {}), proposed.get('hooks', {}))
            apply_managed_cc_policy(current, old, proposed)
        return (json.dumps(current, indent=2, ensure_ascii=False) + '\n').encode()
    content = target.read_text()
    before = tomllib.loads(content)
    sections = list(re.finditer(r'^\[([^\]\n]+)\]\s*$', content, re.M))
    section = next((match for match in sections if match.group(1).strip() == 'shell_environment_policy.set'), None)
    if section:
        end = next((match.start() for match in sections if match.start() > section.start()), len(content))
        body = content[section.end():end]
        if re.search(r'^VIBECODING_VERSION\s*=', body, re.M):
            body = re.sub(r'^VIBECODING_VERSION\s*=.*$', 'VIBECODING_VERSION = "' + VERSION + '"', body, count=1, flags=re.M)
        else:
            body = '\nVIBECODING_VERSION = "' + VERSION + '"\n' + body
        content = content[:section.end()] + body + content[end:]
    else:
        content = content.rstrip() + '\n\n[shell_environment_policy.set]\nVIBECODING_VERSION = "' + VERSION + '"\n'
    after = tomllib.loads(content)
    expected = json.loads(json.dumps(before))
    expected.setdefault('shell_environment_policy', {}).setdefault('set', {})['VIBECODING_VERSION'] = VERSION
    if after != expected:
        raise SetupError('TOML version update affected a user-owned field')
    return content.encode()


def is_preserved_session(relative: Path) -> bool:
    posix = relative.as_posix()
    return any(posix == prefix.rstrip('/') or posix.startswith(prefix) for prefix in PRESERVED_SESSION_PREFIXES)


def prune_old_installer_backups(home: Path, keep: Path | None, platforms: list[str], install_kind: str) -> None:
    """Drop older same-platform fresh/redeploy backups. Never auto-delete migrate backups."""
    if install_kind == 'migrate':
        return
    root = home / '.athena/backups'
    if not root.is_dir() or root.is_symlink():
        return
    keep_resolved = keep.resolve() if keep else None
    wanted = set(platforms)
    to_delete = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        if keep_resolved and child.resolve() == keep_resolved:
            continue
        journal = child / 'transaction.json'
        if not journal.is_file():
            continue
        try:
            record = json.loads(journal.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict):
            continue
        if record.get('install_kind') == 'migrate':
            continue
        recorded = record.get('platforms')
        if not isinstance(recorded, list) or set(recorded) != wanted:
            continue
        if record.get('install_kind', 'redeploy') != install_kind:
            continue
        to_delete.append(child)
    if not to_delete:
        return
    print('pruning installer backups:')
    for child in to_delete:
        print('  ' + str(child))
        shutil.rmtree(child)


def check_destination(home, path):
    if not path.is_relative_to(home):
        raise SetupError('managed destination escapes selected home')
    if is_preserved_session(path.relative_to(home)):
        raise SetupError('refusing to overwrite preserved session history: ' + str(path.relative_to(home)))
    cursor = path
    while cursor != home:
        if cursor.is_symlink():
            raise SetupError('managed destination uses a symlink: ' + str(path.relative_to(home)))
        cursor = cursor.parent
    if path.exists() and not path.is_file():
        raise SetupError('managed file destination is not a file: ' + str(path.relative_to(home)))


def baseline_for(kind, args):
    explicit = getattr(args, 'baseline_' + kind + '_package')
    if explicit:
        result = normalize_package(explicit, kind)
        if result is None:
            raise SetupError('baseline package missing selected platform config')
        return result
    if args.repo_root:
        candidate = args.repo_root / 'vibeCoding' / ('claude' if kind == 'cc' else 'codex') / '9.9.8'
        return normalize_package(candidate, kind)
    return None


def install_plan(args, home):
    kinds = ['cc', 'cx'] if args.only == 'both' else [args.only]
    changes, overrides = [], []
    for kind in kinds:
        package = locate_package(kind, args)
        if package is None:
            raise SetupError('selected ' + kind + ' package not found')
        marker = json.loads((package / 'settings.json').read_text()).get('env', {}).get('VIBECODING_ATHENA_VERSION') if kind == 'cc' else tomllib.loads((package / 'config.toml').read_text()).get('shell_environment_policy', {}).get('set', {}).get('VIBECODING_VERSION')
        if marker != VERSION:
            raise SetupError('selected package version does not match installer')
        state, installed_version = read_version(kind, home)
        config = home / ('.claude/settings.json' if kind == 'cc' else '.codex/config.toml')
        check_destination(home, config)
        if state == 'old' and not args.migrate:
            raise SetupError('selected endpoint needs --migrate; no files changed')
        baseline = baseline_for(kind, args) if args.migrate else None
        if state == 'old' and baseline is None:
            raise SetupError('migration needs selected platform baseline package')
        if state == 'old':
            baseline_version = json.loads((baseline / 'settings.json').read_text()).get('env', {}).get('VIBECODING_ATHENA_VERSION') if kind == 'cc' else tomllib.loads((baseline / 'config.toml').read_text()).get('shell_environment_policy', {}).get('set', {}).get('VIBECODING_VERSION')
            if baseline_version != installed_version:
                raise SetupError('baseline must match installed version')
        source_map = {str(relative): source for source, relative in source_files(baseline, kind)} if baseline else {}
        entries = [(config, config_merge(package, baseline, kind, home), 0o600, 'config')]
        for source, relative in source_files(package, kind):
            destination = home / relative
            check_destination(home, destination)
            content = source.read_bytes()
            if destination.exists() and destination.read_bytes() != content:
                old = source_map.get(str(relative))
                if kind == 'cx' and relative == Path('.codex/hooks.json') and old is not None:
                    current = json.loads(destination.read_text())
                    proposed = json.loads(content)
                    previous = json.loads(old.read_text())
                    content = (json.dumps(merged_hooks(current, previous, proposed), indent=2) + '\n').encode()
                elif old is None or destination.read_bytes() != old.read_bytes():
                    overrides.append(str(relative))
                    continue
            entries.append((destination, content, stat.S_IMODE(source.stat().st_mode), 'asset'))
        for target, content, mode, category in entries:
            if not target.exists() or target.read_bytes() != content:
                changes.append((target, content, mode, category))
    return changes, overrides


def restore_backup(home, backup):
    backup = backup.resolve()
    record = json.loads((backup / 'transaction.json').read_text())
    if Path(record['home']) != home or not backup.is_relative_to(home / '.athena/backups'):
        raise SetupError('rollback belongs to another selected home')
    entries = record['files']
    for row in entries:
        relative = Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise SetupError('invalid rollback path')
        destination = home / relative
        check_destination(home, destination)
        if destination.is_file() and sha256(destination) != row['after_sha256']:
            raise SetupError('later user edit prevents rollback: ' + row['path'])
        if row['existed']:
            original = backup / 'files' / relative
            if original.is_symlink() or sha256(original) != row['before_sha256']:
                raise SetupError('backup content mismatch')
    for row in reversed(entries):
        destination = home / row['path']
        if row['existed']:
            atomic_write(destination, (backup / 'files' / row['path']).read_bytes(), row['before_mode'])
        else:
            destination.unlink(missing_ok=True)
    print('rollback complete; preserved files restored')


def apply_transaction(home, changes, platforms=None, install_kind='redeploy'):
    if not changes:
        return None
    for folder in [home / '.athena', home / '.athena/backups']:
        if folder.is_symlink():
            raise SetupError('backup directory must not be a symlink')
    label = '+'.join(platforms or []) or 'unknown'
    backup = home / '.athena/backups' / (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '-' + uuid.uuid4().hex[:8] + '-' + label + '-' + install_kind
    )
    backup.mkdir(parents=True, mode=0o700)
    backup.parent.chmod(0o700)
    backup.parent.parent.chmod(0o700)
    record = {
        'schema': 1,
        'home': str(home),
        'version': VERSION,
        'platforms': list(platforms or []),
        'install_kind': install_kind,
        'files': [],
    }
    for target, content, _, _ in changes:
        existed = target.exists()
        row = {'path': target.relative_to(home).as_posix(), 'existed': existed, 'after_sha256': hashlib.sha256(content).hexdigest()}
        if existed:
            row.update(before_sha256=sha256(target), before_mode=stat.S_IMODE(target.stat().st_mode))
            atomic_write(backup / 'files' / row['path'], target.read_bytes(), 0o600)
        record['files'].append(row)
    atomic_write(backup / 'transaction.json', (json.dumps(record, indent=2) + '\n').encode(), 0o600)
    written = []
    try:
        for target, content, mode, category in changes:
            # Preflight is not permission to overwrite an intervening user edit.
            row = record['files'][len(written)]
            if target.exists() != row['existed'] or (row['existed'] and sha256(target) != row['before_sha256']):
                raise OSError('destination changed since transaction preview')
            atomic_write(target, content, mode)
            written.append(row)
            if category == 'config':
                maybe_fail('after-first-config')
            else:
                maybe_fail('asset-copy')
        for target, content, _, _ in changes:
            if target.read_bytes() != content:
                raise OSError('post-write readback mismatch')
    except (OSError, ValueError):
        failures = []
        for row in reversed(written):
            target = home / row['path']
            try:
                if row['existed']:
                    atomic_write(target, (backup / 'files' / row['path']).read_bytes(), row['before_mode'])
                else:
                    target.unlink(missing_ok=True)
            except OSError:
                failures.append(row['path'])
        if failures:
            raise OSError('rollback incomplete; inspect recorded backup ' + str(backup))
        raise OSError('transaction failed; rollback complete; backup ' + str(backup))
    return backup


def main():
    args = parse_args()
    home = args.home.expanduser().resolve()
    try:
        if args.rollback:
            if args.dry_run:
                raise SetupError('rollback --dry-run is unsupported; rollback checks all destinations before writing')
            restore_backup(home, args.rollback)
            return 0
        changes, overrides = install_plan(args, home)
        kinds = ['cc', 'cx'] if args.only == 'both' else [args.only]
        print(json.dumps({'version': VERSION, 'platforms_enabled': kinds,
                          'changed_paths': [target.relative_to(home).as_posix() for target, _, _, _ in changes],
                          'preserved_user_overrides': overrides, 'dry_run': args.dry_run}))
        if args.dry_run:
            print('dry-run: no files changed')
            return 0
        state_before = [read_version(kind, home)[0] for kind in kinds]
        if args.migrate:
            install_kind = 'migrate'
        elif all(state == 'fresh' for state in state_before):
            install_kind = 'fresh'
        else:
            install_kind = 'redeploy'
        backup = apply_transaction(home, changes, kinds, install_kind)
        if backup is not None and not args.dry_run:
            prune_old_installer_backups(home, backup, kinds, install_kind)
        print('setup complete; backup=' + str(backup) if backup else 'same-version: no files changed')
        print('sessions preserved: .claude/sessions .codex/sessions history.jsonl file-history projects')
        print('hook trust: unchanged; changed hooks may require native review')
        return 0
    except SetupError as exc:
        print('setup refused: ' + str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError, tomllib.TOMLDecodeError):
        # Config parser diagnostics can contain secrets; never echo them.
        print('setup refused or failed; user configuration values withheld; inspect preview and private backup', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
