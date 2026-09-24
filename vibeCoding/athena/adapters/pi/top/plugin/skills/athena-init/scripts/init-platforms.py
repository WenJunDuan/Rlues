#!/usr/bin/env python3
"""Initialize Athena 9.9.9 platform intent; probe only selected local CLI versions."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def normalize(value):
    if value == ['both'] or value == 'both':
        return ['cc', 'cx']
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not value or any(item not in ['cc', 'cx'] for item in value):
        raise ValueError('platforms must contain cc/cx, or legacy both')
    return [kind for kind in ['cc', 'cx'] if kind in value]


def replace_field(text, name, value):
    line = name + ': ' + json.dumps(value, ensure_ascii=False)
    pattern = r'^' + re.escape(name) + r':[^\n]*$(?:\n[ \t]+-[^\n]*)*'
    if re.search(pattern, text, re.M):
        return re.sub(pattern, lambda match: line, text, count=1, flags=re.M)
    return line + '\n' + text


def frontmatter(text):
    match = re.match(r'\A---[^\S\n]*\n(.*?)(?=^---[^\S\n]*(?:\n|$))', text, re.M | re.S)
    if not match:
        raise ValueError('index needs valid frontmatter; existing content preserved')
    return text[:match.start(1)], match.group(1), text[match.end(1):]


def intent(text):
    if text is None:
        return None
    _, body, _ = frontmatter(text)
    match = re.search(r'^platforms_enabled:\s*(\[[^\n]*?\])', body, re.M)
    if match:
        return normalize(json.loads(match.group(1)))
    match = re.search(r'^platforms_enabled:\s*(?:#.*)?\n((?:[ \t]+-\s+\S+[^\n]*\n)+)', body, re.M)
    if not match:
        return None
    items = re.findall(r'-\s+(\S+)', match.group(1))
    return normalize([item.strip().strip('"\'') for item in items])


def merge_latest(request, latest):
    """Called with the native shared index lock held, after all CLI probes finish."""
    selected = request['selected']
    if request['existed']:
        if latest is None:
            raise ValueError('index removed during probe; initialization must be retried')
        if intent(latest) != request['observed_intent']:
            raise ValueError('platform intent changed during probe; retry for the current selection')
    elif latest is not None and intent(latest) != selected:
        raise ValueError('platform intent changed during initial probe; current index preserved')
    fresh = latest is None
    prefix, body, suffix = frontmatter(request['template'] if fresh else latest)
    body = replace_field(body, 'platforms_enabled', selected)
    for kind in ['cc', 'cx']:
        body = replace_field(body, kind + '_version', request['capabilities'].get(kind, {}).get('version', ''))
    # Capability fields belong to platform_features, never markdown examples or other sections.
    def clear_unobserved(match):
        block = match.group(2)
        for kind in ['cc', 'cx']:
            if fresh or kind not in selected:
                block = re.sub(r'^([ \t]+' + kind + r'_[A-Za-z0-9_]+:)[ \t]*(?:true|false)([^\n]*)$',
                               lambda field: field.group(1) + ' false' + field.group(2), block, flags=re.M)
        return match.group(1) + block
    body = re.sub(r'(^platform_features:[^\n]*\n)((?:[ \t]+[^\n]*(?:\n|$)|\n)*)',
                  clear_unobserved, body, flags=re.M)
    updated = prefix + body + suffix
    if intent(updated) != selected:
        raise ValueError('index write would produce invalid platforms_enabled')
    return updated


def commit_discovery(index, request):
    script = Path(__file__).resolve()
    index.parent.mkdir(parents=True, exist_ok=True)
    if '.claude' in script.parts:
        # CC keeps its existing native Node lock. Python is used only by this init CLI.
        result = subprocess.run(['node', str(script.with_name('commit-index.cjs')),
                   str(script.parents[3] / 'hooks/_index-io.cjs'), str(index), sys.executable, str(script)],
                   input=json.dumps(request), capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr.strip() or 'native index commit failed; original preserved')
        return
    package = script.parents[3]
    hooks = package / 'hooks' if package.name == '.codex' else Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'hooks'
    module_path = hooks / '_index_io.py'
    if not module_path.is_file():
        raise ValueError('native shared index writer unavailable; no unlocked fallback')
    spec = importlib.util.spec_from_file_location('athena_init_index_io', module_path)
    writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(writer)
    if not writer.acquire(index):
        raise ValueError('shared index lock unavailable; initialization did not commit')
    try:
        latest = index.read_text() if index.exists() else None
        updated = merge_latest(request, latest)
        writer.write_atomic(index, updated)
        cache = index.parent / '.runtime/platform-capabilities.json'
        cache.parent.mkdir(exist_ok=True)
        writer.write_atomic(cache, json.dumps(request['capabilities'], indent=2) + '\n')
    finally:
        writer.release(index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--platforms', choices=['cc', 'cx', 'both'], help='user intent; absence preserves existing selection')
    parser.add_argument('--template', type=Path, default=Path(__file__).resolve().parents[2] / 'pace/templates/_index.md')
    parser.add_argument('--refresh', action='store_true', help='rebuild selected CLI cache; does not authenticate')
    args = parser.parse_args()
    repo = args.repo.resolve()
    if subprocess.run(['git', '-C', str(repo), 'rev-parse', '--git-dir'], capture_output=True).returncode:
        parser.error('Athena requires a Git repository')
    state = repo / '.ai_state'
    index = state / '_index.md'
    try:
        text = index.read_text()
    except FileNotFoundError:
        text = None
    observed_intent = intent(text)
    selected = args.platforms if args.platforms is not None else observed_intent
    if selected is None:
        selected = 'cc' if '.claude' in Path(__file__).parts else 'cx'
    selected = normalize(selected)
    cache_path = state / '.runtime/platform-capabilities.json'
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
            if not isinstance(cache, dict) or any(not isinstance(value, dict) for value in cache.values()):
                cache = {}
        except (ValueError, OSError):
            cache = {}  # Rebuildable capability cache is not project truth.
    capabilities = {}
    for kind in selected:
        executable = shutil.which('claude' if kind == 'cc' else 'codex')
        marker = None
        if executable:
            info = Path(executable).stat()
            marker = {'path': executable, 'mtime_ns': info.st_mtime_ns, 'size': info.st_size}
        previous = cache.get(kind)
        if previous and previous.get('executable') == marker and not args.refresh:
            capabilities[kind] = previous
            continue
        version, status = '', 'unavailable'
        if executable:
            try:
                result = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                status = 'unknown'
            else:
                if result.returncode == 0:
                    version, status = result.stdout.strip()[:160], 'available'
                else:
                    status = 'unknown'
        capabilities[kind] = {'version': version, 'status': status, 'executable': marker,
                              'checked_at': datetime.now(timezone.utc).isoformat(),
                              'native_capabilities': 'require current interface observation; version alone is insufficient'}
    commit_discovery(index, {'existed': text is not None, 'observed_intent': observed_intent,
                            'selected': selected, 'capabilities': capabilities,
                            'template': args.template.read_text() if text is None else None})
    for name in ['sprints', 'roadmap', 'architecture', 'requirements', 'compound']:
        (state / name).mkdir(exist_ok=True)
    # Local Git exclusion keeps the rebuildable cache out of commits without touching project policy.
    exclusion = Path(subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--git-path', 'info/exclude'], text=True).strip())
    if not exclusion.is_absolute():
        exclusion = repo / exclusion
    existing = exclusion.read_text() if exclusion.exists() else ''
    if '.ai_state/.runtime/' not in existing.splitlines():
        atomic(exclusion, existing.rstrip('\n') + '\n.ai_state/.runtime/\n')
    print(json.dumps({'platforms_enabled': selected, 'capabilities': {kind: record['status'] for kind, record in capabilities.items()},
                      'vm': 'not_probed; runtime doctor reports configuration and transport separately'}))
    return 0


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['_merge_locked']:
            request = json.load(sys.stdin)
            print(json.dumps({'content': merge_latest(request, request['latest'])}))
        else:
            raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print('init failed: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
