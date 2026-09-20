"""Content bindings, collected only for validation commands and review boundaries.

No raw environment or secret values enter hashes. Runtime recipes opt in with
public scalar fields; external/remote assertions retain their own runner evidence.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from _index_io import write_atomic

FIELDS = ('source_sha256', 'design_sha256', 'environment_sha256')
PUBLIC_ENV = {'system', 'release', 'machine', 'os', 'arch', 'image', 'runtime', 'version', 'scenario', 'seed', 'recipe', 'required'}
# Placeholder allowlist mirrors runtime-run.py: template values carry no live credential.
CREDENTIAL_KEY = re.compile(r'(?i:token|password|secret|api.key)\s*[=:]')
PLACEHOLDER_WORD = re.compile(r'YOUR|REPLACE|EXAMPLE|PLACEHOLDER|CHANGE[-_]?ME|DUMMY|SAMPLE|NOT[-_]A[-_]REAL|REDACTED', re.I)
ALNUM = re.compile(r'[A-Za-z0-9]')
HIGH_ENTROPY = re.compile(r'[A-Za-z0-9]{16,}')


def is_placeholder(value: str) -> bool:
    """Conservative allowlist over an environment credential value; unclear stays a credential.

    Unlike runtime-run.py, an empty body is a placeholder: a bare "password=" field holds no value.
    """
    body = value.strip()
    if not body or re.fullmatch(r'none|null|empty|TBD|TODO', body, re.I):
        return True
    if re.fullmatch(r'(.)\1{5,}', body):
        return True
    # A placeholder word always has non-alphanumeric borders, so vetoing the whole body
    # on a long alphanumeric run equals vetoing "the rest of the body". The veto runs before
    # the shape branches: ${A1b2C3d4E5f6G7h8I9j0} wraps a live key body, not a template name.
    if HIGH_ENTROPY.search(body):
        return False
    if re.fullmatch(r'\$\{[^{}]*\}|\{\{[^{}]*\}\}', body):
        return True
    if re.fullmatch(r'<[A-Za-z0-9_.-]*>', body) and len(body) <= 48:
        return True
    for match in PLACEHOLDER_WORD.finditer(body):
        before = body[match.start() - 1:match.start()] if match.start() else ''
        if not ALNUM.fullmatch(before) and not ALNUM.fullmatch(body[match.end():match.end() + 1]):
            return True
    return False


def credential_values(value: str) -> list:
    """Each credential separator owns the text up to the next credential key, so a trailing
    placeholder field cannot release the value in front of it; any non-placeholder raises."""
    hits = list(CREDENTIAL_KEY.finditer(value))
    return [value[hit.end():hits[i + 1].start() if i + 1 < len(hits) else len(value)]
            for i, hit in enumerate(hits)]
_COMMAND_PREFIX = r'(?:^|[;&|]\s*)\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*(?:npx\s+)?'
_VALIDATION_PATTERNS = [
    ('test', r'(?:python3?\s+-m\s+(?:pytest|unittest)|pytest|unittest|(?:npm|pnpm|yarn|bun)\s+(?:test|run\s+test)|cargo\s+test|go\s+test|mvn\s+(?:test|verify)|\./gradlew\s+test)'),
    ('lint', r'(?:eslint|prettier\s+--check|ruff|(?:npm|pnpm|yarn|bun)\s+run\s+lint|cargo\s+clippy|go\s+vet|node\s+--check|git\s+diff\s+--check)'),
    ('typecheck', r'(?:tsc|(?:npm|pnpm|yarn|bun)\s+run\s+(?:typecheck|check)|cargo\s+check)'),
    ('build', r'(?:(?:npm|pnpm|yarn|bun)\s+run\s+build|cargo\s+build|go\s+build|mvn\s+compile|\./gradlew\s+build|cmake\s+--build)'),
]
_VALIDATION_PATTERNS = [(kind,re.compile(_COMMAND_PREFIX + pattern + r'\b',re.I | re.M)) for kind,pattern in _VALIDATION_PATTERNS]

def classify_validation(command: str) -> str | None:
    """Single command classification consumed by both pre and post hooks."""
    return next((kind for kind,pattern in _VALIDATION_PATTERNS if pattern.search(command)),None)

def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def required(sprint: Path) -> bool:
    """Binding is on because these 9.9.9 hooks are installed, not because _index.version says so."""
    index = sprint.parents[1]/'_index.md'
    if not index.is_file():
        return False
    text = index.read_text()
    slug = re.search(r'^current_sprint_slug:\s*["\']?([A-Za-z0-9][A-Za-z0-9._-]*)',text,re.M)
    return bool(slug and slug.group(1) == sprint.name)

def digest(data: bytes | str) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()

def git(root: Path, *args: str) -> bytes:
    run = subprocess.run(['git', *args], cwd=root, capture_output=True, timeout=15)
    if run.returncode:
        raise ValueError('git input unavailable: ' + run.stderr.decode('utf-8', 'replace').strip())
    return run.stdout

def context(cwd: Path) -> tuple[Path, Path]:
    root = Path(git(Path(cwd), 'rev-parse', '--show-toplevel').decode().strip())
    text = (root/'.ai_state/_index.md').read_text()
    match = re.search(r'^current_sprint_slug:\s*["\']?([A-Za-z0-9][A-Za-z0-9._-]*)', text, re.M)
    if not match:
        raise ValueError('current sprint unavailable')
    return root, root/'.ai_state/sprints'/match.group(1)

def source_sha256(root: Path) -> str:
    names = sorted(set(n.decode('utf-8') for n in git(root, 'ls-files', '-z', '-c', '-o', '--exclude-standard').split(b'\0') if n))
    h = hashlib.sha256()
    for name in names:
        parts = Path(name).parts
        if parts[0] in {'.ai_state', '.runtime'}:
            continue
        if any(p.startswith('.env') or p.endswith(('.pem', '.key', '.p12')) or p.lower() in {'credentials', 'secrets'} for p in parts):
            continue
        target = root/name
        h.update(name.encode() + b'\0')
        if target.is_symlink():
            h.update(b'link\0' + os.readlink(target).encode())
        elif not target.exists():
            h.update(b'deleted')
        elif target.is_file():
            h.update((b'executable\0' if target.stat().st_mode & 0o111 else b'file\0') + target.read_bytes())
        elif target.is_dir():
            sys.stderr.write('[input-binding] skip gitlink/submodule: '+name+'\n')
            h.update(b'gitlink\0')
        else:
            raise ValueError('unsupported source directory/submodule: ' + name)
        h.update(b'\n')
    return h.hexdigest()

def environment(root: Path) -> dict:
    uname = os.uname()
    result = {'system': uname.sysname.lower(), 'release': uname.release, 'machine': uname.machine, 'recipe': []}
    for name in ('.ai_state/runtime-env.yaml', '.ai_state/conventions/runtime-env.yaml', '.ai_state/conventions/runtime-env.md'):
        file = root/name
        if not file.is_file():
            continue
        public = []
        for line in file.read_text().splitlines():
            match = re.match(r'^\s*([A-Za-z_]+):\s*(.*?)\s*$', line)
            if match and match.group(1) in PUBLIC_ENV:
                value = match.group(2)
                if re.search(r'://[^/\s]*@', value) or any(
                        not is_placeholder(item) for item in credential_values(value)):
                    raise ValueError('public environment field contains credential syntax')
                public.append([match.group(1), value])
        result['recipe'].append([name, public])
    return result

def snapshot(root: Path, sprint: Path) -> dict:
    return {'source_sha256': source_sha256(root), 'design_sha256': digest((sprint/'design.md').read_bytes()),
            'environment_sha256': digest(canonical(environment(root)))}

def command_of(payload) -> str:
    value = payload.get('tool_input') or {}
    return str(value.get('command') or value.get('cmd') or '')

def execution_cwd(payload) -> Path:
    tool_input = payload.get('tool_input') or {}
    return Path(tool_input.get('workdir') or payload.get('cwd') or Path.cwd())

def pre_path(root: Path, payload) -> Path:
    ident = payload.get('tool_use_id')
    if not isinstance(ident, str) or not ident:
        raise ValueError('native tool_use_id unavailable')
    return root/'.ai_state/.runtime/evidence-inputs'/(digest(ident) + '.json')

def capture_before(payload) -> None:
    if classify_validation(command_of(payload)) is None:
        return
    if re.search(r'(?:^|[;&|]\s*)cd\s', command_of(payload)):
        raise ValueError('use the tool workdir for validation; shell directory changes are not bound')
    root, sprint = context(execution_cwd(payload))
    path = pre_path(root, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, canonical(snapshot(root, sprint)))

def finish(payload, redacted_output: str) -> dict:
    try:
        root, sprint = context(execution_cwd(payload))
        path = pre_path(root, payload)
        before = json.loads(path.read_text())
        path.unlink()
        current = snapshot(root, sprint)
        if before != current:
            return {'binding_status': 'unverifiable'}
        output = sprint/'evidence'/(digest(payload['tool_use_id']) + '.txt')
        output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(output, redacted_output)
        return {**current, 'binding_status': 'current', 'output_artifact': output.relative_to(sprint).as_posix(),
                'artifact_sha256': digest(output.read_bytes())}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'binding_status': 'unverifiable'}

def current_record(record: dict, root: Path, sprint: Path, live: dict | None = None) -> bool:
    if record.get('binding_status') != 'current':
        return False
    try:
        current = live or snapshot(root, sprint)
        target = (sprint/record['output_artifact']).resolve()
        if not target.is_relative_to(sprint.resolve()):
            return False
        return all(record.get(k) == current[k] for k in FIELDS) and digest(target.read_bytes()) == record.get('artifact_sha256')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return False

def _words(text: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    quote = ''
    escaped = False
    def flush() -> None:
        if buf:
            out.append(''.join(buf))
            buf.clear()
    for ch in text:
        if escaped:
            buf.append(ch)
            escaped = False
            continue
        if ch == '\\' and quote != "'":
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = ''
            else:
                buf.append(ch)
            continue
        if ch in "'\"":
            quote = ch
            continue
        if ch.isspace():
            flush()
            continue
        buf.append(ch)
    flush()
    return out

def _set_pipefail_delta(text: str) -> bool | None:
    toks = _words(text)
    i = 0
    while i < len(toks) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i]):
        i += 1
    if i >= len(toks) or toks[i].rsplit('/', 1)[-1] != 'set':
        return None
    i += 1
    mentioned: bool | None = None
    while i < len(toks):
        arg = toks[i]
        i += 1
        if arg in ('-o', '+o'):
            if i < len(toks) and toks[i] == 'pipefail':
                mentioned = arg == '-o'
                i += 1
            continue
        if arg.startswith(('-', '+')) and not arg.startswith('--'):
            flags = arg[1:]
            o_at = flags.find('o')
            if o_at < 0:
                continue
            attached = flags[o_at + 1:]
            if attached:
                if attached == 'pipefail':
                    mentioned = arg[0] == '-'
            elif i < len(toks) and toks[i] == 'pipefail':
                mentioned = arg[0] == '-'
                i += 1
    return mentioned

def _pipefail_before(segments: list[dict[str, str]], v_index: int) -> bool:
    on = False
    for segment in segments[:v_index]:
        delta = _set_pipefail_delta(segment['text'])
        if delta is True:
            on = True
        elif delta is False:
            on = False
    return on

def _pipeline_end(segments: list[dict[str, str]], v_index: int) -> int:
    end = v_index
    while end < len(segments) and segments[end]['op'] in ('|', '|&'):
        end += 1
    return end

def _operators_after_pipeline(segments: list[dict[str, str]], end: int) -> list[str]:
    ops: list[str] = []
    for segment in segments[end:]:
        op = ';' if segment['op'] == '\n' else segment['op']
        if op and op not in ('|', '|&'):
            ops.append(op)
    return ops

def validation_status_policy(command: str) -> dict:
    """Decide whether an observed exit 0 proves the validation command succeeded.

    Exit 0 proves it only when every path to exit 0 runs the validation segment: its
    status reaches its pipeline (last element, or pipefail), the pipeline reaches the
    line (only ``&&`` after it), and the line is not backgrounded.

    Returns:
        ``{provable, reason}``; reason is one of ``pipeline_without_pipefail``,
        ``validation_status_not_reported``, ``validation_backgrounded``, else None.
    """
    # The import stays inside the function on purpose: delivery-gate imports this
    # module at load with no try, so a module-level import of a missing _shell_lex
    # would raise at gate import and turn the ship gate permissive. A load failure
    # here only downgrades evidence, which fails closed.
    try:
        from _shell_lex import scan
    except Exception:
        return {'provable': False, 'reason': 'validation_status_not_reported'}
    segments = scan(command)
    validations = [i for i, segment in enumerate(segments) if classify_validation(segment['text'])]
    if not validations:
        return {'provable': True, 'reason': None}
    if segments[-1]['op'] == '&':
        return {'provable': False, 'reason': 'validation_backgrounded'}
    for vi in validations:
        end = _pipeline_end(segments, vi)
        if any(op != '&&' for op in _operators_after_pipeline(segments, end)):
            return {'provable': False, 'reason': 'validation_status_not_reported'}
        if vi != end and not _pipefail_before(segments, vi):
            return {'provable': False, 'reason': 'pipeline_without_pipefail'}
    return {'provable': True, 'reason': None}
