#!/usr/bin/env python3
"""Athena 9.9.9 controlled local/SSH runtime. Python 3.9+, stdlib only."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

MAX_BYTES = 256 * 1024 * 1024
MAX_LOG = 128 * 1024
SECRET = re.compile(
    rb'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'
    rb'|\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b'
    rb'|(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*["\x27]?\s*[:=]\s*["\x27][^\s"\x27]{12,}["\x27]',
    re.I,
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('invalid relative input path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or value == '.':
        raise ValueError('invalid relative input path')
    return path


def excluded_path(value):
    path = safe_path(value)
    parts = set(path.parts)
    return bool(parts & {'.git', '.ssh', '.aws', '.gnupg', '.athena', '.runtime', '__pycache__', 'node_modules'}
                or path.name == '.env' or path.name.startswith('.env.')
                or path.suffix.lower() in {'.key', '.pem', '.p12', '.pfx', '.pyc'}
                or path.name.lower() in {'credentials.json', 'credentials', 'id_rsa', 'id_ed25519'})


def git(repo, *args, input=None, allow_empty=False):
    result = subprocess.run(['git', '-C', str(repo), *args], input=input, capture_output=True)
    if result.returncode and not (allow_empty and result.returncode == 1):
        raise ValueError('Git input inspection failed: ' + args[0])
    return result.stdout


def collect(repo, allow_untracked, omitted):
    base = git(repo, 'rev-parse', 'HEAD').decode().strip()
    head = git(repo, 'ls-tree', '-rz', '--full-tree', 'HEAD').split(b'\0')
    tracked = set(git(repo, 'ls-files', '-z').decode().split('\0')) - {''}
    for item in head:
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        if metadata.split()[0] == b'160000':
            raise ValueError('submodules are not supported; use a separate controlled snapshot')
        tracked.add(name.decode())
    index = git(repo, 'ls-files', '--stage', '-z')
    if any(row.startswith(b'160000 ') for row in index.split(b'\0')):
        raise ValueError('submodules are not supported; use a separate controlled snapshot')
    allowed = set(allow_untracked)
    paths = sorted(tracked | allowed)
    for name in paths:
        safe_path(name)
    ignored = set(git(repo, 'check-ignore', '--no-index', '-z', '--stdin',
                      input=('\0'.join(paths) + '\0').encode(), allow_empty=True).decode().split('\0'))
    changed = set(git(repo, 'diff', '--name-only', '-z', 'HEAD').decode().split('\0')) | allowed
    rows, contents, exclusions = [], {}, []
    total = 0
    for name in paths:
        if name in omitted or excluded_path(name) or name in ignored:
            exclusions.append({'path': name, 'reason': 'excluded_path_or_ignored'})
            continue
        path = repo / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != repo and repo in p.parents):
            raise ValueError('symlinks are not supported in controlled inputs: ' + name)
        if not path.resolve().is_relative_to(repo):
            raise ValueError('input escapes repository')
        if not path.exists():
            if name in allowed and name not in tracked:
                raise ValueError('explicit untracked input missing: ' + name)
            rows.append({'path': name, 'type': 'deleted'})
            continue
        if not path.is_file():
            raise ValueError('unsupported input type: ' + name)
        data = path.read_bytes()
        if SECRET.search(data):
            exclusions.append({'path': name, 'reason': 'secret_pattern'})
            print('excluded secret pattern: ' + name, file=sys.stderr)
            continue
        total += len(data)
        if total > MAX_BYTES:
            raise ValueError('controlled input exceeds 256 MiB')
        contents[name] = data
        rows.append({'path': name, 'type': 'file', 'mode': stat.S_IMODE(path.stat().st_mode) & 0o777,
                     'size': len(data), 'sha256': digest(data)})
    manifest = {'schema': 1, 'base_commit': base, 'files': rows,
                'allowed_untracked': sorted(allowed), 'excluded': exclusions,
                'controlled_diff_sha256': digest(canonical([row for row in rows if row['path'] in changed]))}
    manifest['manifest_sha256'] = digest(canonical(manifest))
    return manifest, contents


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(data, handle, indent=2)
            handle.write('\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def snapshot(args):
    repo = args.repo.resolve()
    root = git(repo, 'rev-parse', '--show-toplevel').decode().strip()
    if Path(root).resolve() != repo:
        raise ValueError('--repo must be the Git repository root')
    output = args.output.resolve()
    omitted = {output.relative_to(repo).as_posix()} if output.is_relative_to(repo) else set()
    manifest, contents = collect(repo, args.allow_untracked, omitted)
    available = {row['path'] for row in manifest['files'] if row['type'] == 'file'}
    for required in args.required_input:
        safe_path(required)
        if required not in available:
            raise ValueError('required input missing or excluded: ' + required)
    repeated, _ = collect(repo, args.allow_untracked, omitted)
    if repeated != manifest:
        raise ValueError('source changed while snapshotting; regenerate input')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + output.name, dir=output.parent)
    os.close(fd)
    try:
        with tarfile.open(temporary, 'w:gz') as archive:
            for name, data, mode in [('manifest.json', canonical(manifest), 0o600)] + [
                    ('source/' + row['path'], contents[row['path']], row['mode'])
                    for row in manifest['files'] if row['type'] == 'file']:
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(data), mode
                archive.addfile(info, io.BytesIO(data))
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'status': 'snapshotted', 'bundle': str(output), 'input_manifest_sha256': manifest['manifest_sha256'],
            'files': len(contents), 'excluded': manifest['excluded']}


def inspect_bundle(data, destination=None):
    if len(data) > MAX_BYTES:
        raise ValueError('bundle exceeds 256 MiB')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or 'manifest.json' not in names:
            raise ValueError('duplicate or missing manifest')
        if any(not member.isfile() or member.size < 0 for member in members):
            raise ValueError('unsupported archive member type')
        if sum(member.size for member in members) > MAX_BYTES:
            raise ValueError('expanded bundle exceeds 256 MiB')
        manifest = json.load(archive.extractfile('manifest.json'))
        if not isinstance(manifest, dict) or set(manifest) != {'schema', 'base_commit', 'files', 'allowed_untracked', 'excluded', 'controlled_diff_sha256', 'manifest_sha256'}:
            raise ValueError('invalid manifest object schema')
        if not isinstance(manifest['files'], list) or not isinstance(manifest['allowed_untracked'], list) or not isinstance(manifest['excluded'], list):
            raise ValueError('invalid manifest arrays')
        if not isinstance(manifest['base_commit'], str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', manifest['base_commit']):
            raise ValueError('invalid manifest base commit')
        for field in ['controlled_diff_sha256', 'manifest_sha256']:
            if not isinstance(manifest[field], str) or not re.fullmatch(r'[0-9a-f]{64}', manifest[field]):
                raise ValueError('invalid manifest digest')
        for name in manifest['allowed_untracked']:
            safe_path(name)
        for exclusion in manifest['excluded']:
            if not isinstance(exclusion, dict) or set(exclusion) != {'path', 'reason'} or exclusion['reason'] not in ['excluded_path_or_ignored', 'secret_pattern']:
                raise ValueError('invalid input exclusion record')
            safe_path(exclusion['path'])
        stored = manifest.pop('manifest_sha256')
        if manifest.get('schema') != 1 or stored != digest(canonical(manifest)):
            raise ValueError('manifest hash mismatch')
        manifest['manifest_sha256'] = stored
        expected, seen = {'manifest.json'}, set()
        for row in manifest['files']:
            if not isinstance(row, dict) or row.get('type') not in ['file', 'deleted']:
                raise ValueError('invalid manifest file entry')
            fields = {'path', 'type'} if row['type'] == 'deleted' else {'path', 'type', 'mode', 'size', 'sha256'}
            if set(row) != fields:
                raise ValueError('invalid manifest file schema')
            name = row['path']
            safe_path(name)
            if name in seen or excluded_path(name):
                raise ValueError('duplicate or excluded manifest path')
            seen.add(name)
            if row['type'] == 'deleted':
                continue
            if row['type'] != 'file' or not isinstance(row['mode'], int) or row['mode'] & ~0o777:
                raise ValueError('invalid file type or mode')
            if not isinstance(row['size'], int) or row['size'] < 0 or not isinstance(row['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', row['sha256']):
                raise ValueError('invalid file size or digest')
            expected.add('source/' + name)
        if set(names) != expected:
            raise ValueError('archive file set differs from manifest')
        for row in manifest['files']:
            if row['type'] == 'deleted':
                continue
            member = archive.getmember('source/' + row['path'])
            content = archive.extractfile(member).read()
            if SECRET.search(content):
                raise ValueError('secret pattern in transferred input')
            if member.mode != row['mode'] or len(content) != row['size'] or digest(content) != row['sha256']:
                raise ValueError('input content or mode mismatch')
            if destination is not None:
                target = destination / row['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as handle:
                    handle.write(content)
                target.chmod(row['mode'])
    return manifest


def redacted(data):
    return b''.join(b'[REDACTED sensitive output]\n' if SECRET.search(line) else line
                    for line in data.splitlines(keepends=True)).decode(errors='replace')


def environment():
    return {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine(),
            'python': platform.python_version()}


def command_step(name, argv, cwd, seconds, env, process_groups):
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        start = time.monotonic()
        try:
            child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        except OSError:
            return {'name': name, 'status': 'failed', 'exit_code': None, 'stdout': '',
                    'stderr': 'command could not start', 'duration_seconds': 0}
        process_groups.append(child.pid)
        timed_out, interrupted = False, False
        try:
            child.wait(timeout=max(seconds, 0.001))
        except subprocess.TimeoutExpired:
            timed_out = True
        except KeyboardInterrupt:
            interrupted = True
        finally:
            if timed_out or interrupted:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            child.wait()
        result = {'name': name, 'status': 'interrupted' if interrupted else 'timed_out' if timed_out else ('passed' if child.returncode == 0 else 'failed'),
                  'exit_code': child.returncode, 'duration_seconds': round(time.monotonic() - start, 3)}
        for label, handle in [('stdout', stdout), ('stderr', stderr)]:
            handle.seek(0)
            raw = handle.read(MAX_LOG + 1)
            text = redacted(raw[:MAX_LOG])
            result[label] = text
            result[label + '_sha256'] = digest(text.encode())
            result[label + '_truncated'] = len(raw) > MAX_LOG
        return result


def validate_scenario(scenario):
    if not isinstance(scenario, dict):
        raise ValueError('scenario must be a JSON object')
    if set(scenario) - {'name', 'prepare', 'ready', 'command', 'teardown', 'required_os'}:
        raise ValueError('unknown scenario fields; commands use argv, with no inline secrets')
    if not isinstance(scenario.get('name'), str) or not scenario['name']:
        raise ValueError('scenario name is required')
    for name in ['prepare', 'ready', 'command', 'teardown']:
        argv = scenario.get(name)
        if argv is None and name != 'command':
            continue
        if not isinstance(argv, list) or not argv or any(not isinstance(value, str) or '\x00' in value for value in argv):
            raise ValueError('scenario ' + name + ' must be a nonempty argv array')
    if SECRET.search(canonical(scenario)):
        raise ValueError('scenario contains a secret pattern; use authorized external injection')


def new_result(request):
    return {'schema': 1, 'run_id': request['run_id'], 'runner': request['runner'],
            'requirement': request['requirement'], 'checked_at': now(), 'status': 'not_run',
            'configured': {'status': 'passed'}, 'transport': {'status': 'passed'},
            'scenario': {'status': 'not_run'}, 'cleanup': {'status': 'not_needed'}, 'steps': [],
            'input_manifest_sha256': request.get('input_manifest_sha256'),
            'contract_sha256': request.get('contract_sha256'), 'scenario_sha256': request.get('scenario_sha256')}


def execute(request, bundle, workdir=None):
    result = new_result(request)
    root = None
    process_groups = []
    phase = 'input'
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    previous_signals = {sig: signal.signal(sig, interrupt) for sig in [signal.SIGTERM, signal.SIGHUP]}
    try:
        manifest = inspect_bundle(bundle)
        if manifest['manifest_sha256'] != request['input_manifest_sha256']:
            raise ValueError('requested input differs from received bundle')
        validate_scenario(request['scenario'])
        if digest(canonical(request['scenario'])) != request['scenario_sha256']:
            raise ValueError('scenario hash mismatch')
        phase = 'prepare'
        root = Path(tempfile.mkdtemp(prefix='athena-run-' + request['run_id'] + '-', dir=workdir))
        root.chmod(0o700)
        result['resource_root'] = str(root)
        source = root / 'source'
        source.mkdir()
        inspect_bundle(bundle, source)
        result['environment'] = environment()
        result['environment_sha256'] = digest(canonical(result['environment']))
        required_os = request['scenario'].get('required_os')
        if required_os and str(result['environment']['system']).lower() != str(required_os).lower():
            result['status'] = 'environment_unsatisfied'
            result['scenario']['status'] = 'not_ready'
            result['failure'] = {'kind': 'environment_unsatisfied',
                                 'reason': 'required OS ' + str(required_os) + ' != ' + str(result['environment']['system'])}
            return result
        result['base_commit'] = manifest['base_commit']
        env = dict(os.environ, ATHENA_RUN_ID=request['run_id'], ATHENA_RUN_ROOT=str(root))
        deadline = time.monotonic() + request['timeout']
        result['scenario']['status'] = 'ready'
        result['status'] = 'passed'
        try:
            for name in ['prepare', 'ready', 'command']:
                if name not in request['scenario']:
                    continue
                step = command_step(name, request['scenario'][name], source, deadline - time.monotonic(), env, process_groups)
                result['steps'].append(step)
                if step['status'] != 'passed':
                    result['status'] = step['status'] if step['status'] in ['timed_out', 'interrupted'] else name + '_failed'
                    result['scenario']['status'] = 'failed' if name == 'command' else 'not_ready'
                    break
            else:
                result['scenario']['status'] = 'passed'
        finally:
            if 'teardown' in request['scenario']:
                cleanup = command_step('teardown', request['scenario']['teardown'], source, 15, env, process_groups)
                result['steps'].append(cleanup)
                if cleanup['status'] != 'passed':
                    result['cleanup'] = {'status': 'failed', 'reason': 'teardown_failed'}
                    result['status'] = 'teardown_failed'
    except (ValueError, KeyError, TypeError, OSError, tarfile.TarError) as exc:
        result['status'] = 'input_invalid' if phase == 'input' else 'prepare_failed'
        if phase == 'prepare':
            result['scenario']['status'] = 'not_ready'
        result['failure'] = {'kind': result['status'], 'reason': redacted(str(exc).encode())}
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
        result['scenario']['status'] = 'failed'
    finally:
        # Preserve prepare services for later steps, then stop only this run's process groups.
        # A reaped session leader pid is still the pgid of leftover members; dropping it
        # would leak those children. ProcessLookupError covers a fully empty group.
        for group in process_groups:
            try:
                os.killpg(group, 0)
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
        if root is not None:
            try:
                shutil.rmtree(root)
                if result['cleanup']['status'] != 'failed':
                    result['cleanup'] = {'status': 'passed'}
            except OSError:
                result['cleanup'] = {'status': 'failed', 'reason': 'run_directory_cleanup_failed', 'resource_root': str(root)}
                result['status'] = 'cleanup_failed'
        for sig, handler in previous_signals.items():
            signal.signal(sig, handler)
    result['blocks_delivery'] = result['requirement'] == 'required' and result['status'] != 'passed'
    if result['status'] != 'passed':
        result.setdefault('failure', {'kind': result['status']})
    return result


def ssh_target(config, name):
    if config.is_symlink() or stat.S_IMODE(config.stat().st_mode) & 0o077:
        raise ValueError('VM config must be a private regular file (0600)')
    data = json.loads(config.read_text())
    if not isinstance(data, dict) or not isinstance(data.get('vms'), list) or any(not isinstance(row, dict) for row in data['vms']):
        raise ValueError('invalid VM configuration schema')
    if re.search(r'"password"\s*:', config.read_text(), re.I):
        raise ValueError('plaintext password field is forbidden')
    matches = [row for row in data['vms'] if row.get('name') == name]
    if len(matches) != 1:
        raise ValueError('selected VM not configured uniquely')
    target = matches[0]
    for key in ['host', 'user']:
        if not re.fullmatch(r'[A-Za-z0-9_.:@-]+', target[key]) or target[key].startswith('-'):
            raise ValueError('invalid VM connection field')
    port = target.get('port', 22)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError('invalid SSH port')
    workdir = target.get('workdir', '/tmp')
    if not isinstance(workdir, str) or not workdir.startswith('/') or '..' in PurePosixPath(workdir).parts:
        raise ValueError('VM workdir must be an absolute path without traversal')
    auth = target.get('auth', {'method': 'key'})
    if not isinstance(auth, dict):
        raise ValueError('invalid VM authentication schema')
    method = auth.get('method', 'key')
    if method not in ['key', 'password_env']:
        raise ValueError('unsupported VM authentication method')
    env = os.environ.copy()
    alias = target.get('ssh_alias')
    if alias is not None and (not isinstance(alias, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', alias) or alias.startswith('-')):
        raise ValueError('invalid SSH alias')
    command = ['ssh', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=5']
    if alias is None:
        command += ['-p', str(port)]
    if method == 'password_env':
        variable = auth.get('password_env', '')
        if not variable or variable not in env:
            raise ValueError('configured password environment is unavailable')
        env['SSHPASS'] = env[variable]
        command = ['sshpass', '-e', *command]
    else:
        command += ['-o', 'BatchMode=yes']
        if auth.get('key_path'):
            command += ['-i', str(Path(auth['key_path']).expanduser())]
    command += [alias if alias is not None else target['user'] + '@' + target['host']]
    return target, command, env


def ssh_call(command, env, source, action, payload, timeout):
    remote = 'python3 -c ' + shlex.quote(source) + ' ' + action
    try:
        process = subprocess.run([*command, remote], input=canonical(payload), capture_output=True, env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if process.returncode:
        err = process.stderr.decode('utf-8', 'replace')
        if 'Traceback (most recent call last)' in err:
            return {'_athena_runner_crash': True, 'stderr': err[-2000:]}
        return None
    try:
        return json.loads(process.stdout)
    except (ValueError, UnicodeError):
        err = process.stderr.decode('utf-8', 'replace')
        if 'Traceback (most recent call last)' in err or not process.stdout:
            return {'_athena_runner_crash': True, 'stderr': err[-2000:]}
        return None


def doctor(args):
    result = {'checked_at': now(), 'runner': args.runner, 'configured': {'status': 'passed'},
              'transport': {'status': 'passed'}, 'scenario': {'status': 'not_run'}}
    if args.runner == 'local':
        result['environment'] = environment()
        return result
    try:
        _, command, env = ssh_target(args.config, args.vm)
    except (OSError, ValueError, KeyError, TypeError):
        result['configured']['status'] = 'failed'
        result['transport']['status'] = 'not_run'
        return result
    remote = ssh_call(command, env, Path(__file__).read_text(), '_doctor', {}, 10)
    result['transport']['status'] = 'passed' if remote else 'failed'
    if remote:
        result['environment'] = remote
    return result


def run(args):
    request = {'run_id': uuid.uuid4().hex, 'runner': args.runner, 'requirement': args.requirement, 'timeout': args.timeout}
    result = new_result(request)
    try:
        bundle = args.bundle.read_bytes()
        manifest = inspect_bundle(bundle)
        contract = args.contract.read_bytes()
        if SECRET.search(contract):
            raise ValueError('contract contains a secret pattern')
        scenario = json.loads(args.scenario.read_text())
        validate_scenario(scenario)
        request.update(input_manifest_sha256=manifest['manifest_sha256'], contract_sha256=digest(contract),
                       scenario_sha256=digest(canonical(scenario)), scenario=scenario)
        result = new_result(request)
        if args.runner == 'local':
            result = execute(request, bundle)
        else:
            try:
                target, command, env = ssh_target(args.config, args.vm)
            except (OSError, ValueError, KeyError, TypeError):
                result['configured']['status'] = 'failed'
                result['transport']['status'] = 'not_run'
                result['status'] = 'configuration_failed'
            else:
                budget = target.get('limits', {}).get('max_session_minutes', 30) * 60
                if not isinstance(budget, (int, float)) or budget <= 0:
                    raise ValueError('invalid VM session budget')
                request['timeout'] = min(request['timeout'], budget)
                request['workdir'] = target.get('workdir', '/tmp')
                request['bundle'] = base64.b64encode(bundle).decode()
                received = ssh_call(command, env, Path(__file__).read_text(), '_receive', request, request['timeout'] + 30)
                if isinstance(received, dict) and received.get('_athena_runner_crash'):
                    result['transport']['status'] = 'passed'
                    result['status'] = 'runner_failed'
                    result['scenario']['status'] = 'not_run'
                    result['failure'] = {'kind': 'runner_failed', 'reason': received.get('stderr', 'remote runner crashed')}
                elif not isinstance(received, dict) or received.get('run_id') != request['run_id']:
                    result['transport']['status'] = 'failed'
                    result['status'] = 'transport_failed'
                    result['cleanup'] = {'status': 'unknown', 'run_id': request['run_id'],
                                         'reason': 'remote result unavailable; inspect only directories with this run ID'}
                elif any(received.get(key) != request[key] for key in ['input_manifest_sha256', 'contract_sha256', 'scenario_sha256']):
                    result['status'] = 'input_invalid'
                else:
                    result = received
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError):
        result['status'] = 'input_invalid'
    result['blocks_delivery'] = args.requirement == 'required' and result['status'] != 'passed'
    if result['status'] != 'passed':
        result.setdefault('failure', {'kind': result['status']})
    atomic_json(args.output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    snap = commands.add_parser('snapshot', help='build a filtered final-worktree manifest and archive')
    snap.add_argument('--repo', type=Path, required=True)
    snap.add_argument('--output', type=Path, required=True, help='prefer .ai_state/.runtime/; always excludes this output')
    snap.add_argument('--allow-untracked', action='append', default=[], metavar='RELATIVE_PATH')
    snap.add_argument('--required-input', action='append', default=[], metavar='RELATIVE_PATH')
    for name in ['doctor', 'run']:
        command = commands.add_parser(name, help='check transport only' if name == 'doctor' else 'verify input, execute scenario, return evidence and clean up')
        command.add_argument('--runner', choices=['local', 'ssh'], default='local')
        command.add_argument('--vm', help='name in existing ~/.athena/vm.json; no configuration changes')
        command.add_argument('--config', type=Path, default=Path.home() / '.athena/vm.json')
        if name == 'run':
            command.add_argument('--bundle', type=Path, required=True)
            command.add_argument('--contract', type=Path, required=True)
            command.add_argument('--scenario', type=Path, required=True, help='JSON: name, command argv; optional prepare/ready/teardown argv')
            command.add_argument('--output', type=Path, required=True)
            command.add_argument('--requirement', choices=['required', 'advisory'], default='required')
            command.add_argument('--timeout', type=float, default=60, help='total scenario seconds; cleanup has a separate 15 seconds')
    args = parser.parse_args()
    if getattr(args, 'runner', '') == 'ssh' and not args.vm:
        parser.error('--vm is required for SSH')
    if not math.isfinite(getattr(args, 'timeout', 1)) or getattr(args, 'timeout', 1) <= 0:
        parser.error('--timeout must be positive')
    try:
        result = snapshot(args) if args.action == 'snapshot' else doctor(args) if args.action == 'doctor' else run(args)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        print('runtime input rejected: ' + redacted(str(exc).encode()), file=sys.stderr)
        return 2
    print(json.dumps(result if args.action != 'run' else {key: result[key] for key in ['run_id', 'status', 'blocks_delivery']}))
    if args.action == 'doctor':
        return 0 if result['transport']['status'] == 'passed' else 2
    return 0 if result['status'] in ['passed', 'snapshotted'] else 2


if __name__ == '__main__':
    if sys.argv[1:] == ['_doctor']:
        print(json.dumps(environment()))
    elif sys.argv[1:] == ['_receive']:
        request = json.load(sys.stdin)
        # Never invent a remote installation or shared workdir; it must already exist.
        print(json.dumps(execute(request, base64.b64decode(request['bundle'], validate=True), request['workdir'])))
    else:
        raise SystemExit(main())
