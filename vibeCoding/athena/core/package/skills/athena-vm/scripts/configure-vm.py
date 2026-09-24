#!/usr/bin/env python3
"""Configure an Athena VM target without connecting or changing SSH configuration."""
import argparse
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile


def identifier(value, label, pattern=r'[A-Za-z0-9_.:-]+'):
    if not isinstance(value, str) or not re.fullmatch(pattern, value) or value.startswith('-'):
        raise ValueError('invalid ' + label)
    return value


def contains_inline_credentials(value):
    if isinstance(value, dict):
        return any(key.lower() in {'password', 'private_key', 'private_key_pem'} or contains_inline_credentials(child)
                   for key, child in value.items())
    if isinstance(value, list):
        return any(contains_inline_credentials(child) for child in value)
    return isinstance(value, str) and bool(re.search(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----', value))


def read_config(path):
    if path.is_symlink():
        raise ValueError('VM config must not be a symlink')
    if not path.exists():
        return {'version': 1, 'vms': []}
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError('existing VM config must be a private regular file (0600)')
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('vms'), list):
        raise ValueError('existing VM config must use version 1 with a vms array')
    if any(not isinstance(target, dict) for target in data['vms']):
        raise ValueError('invalid VM target object')
    if contains_inline_credentials(data):
        raise ValueError('inline password/private key is forbidden; existing file preserved')
    return data


def connection(args):
    if args.ssh_alias:
        identifier(args.ssh_alias, 'SSH alias', r'[A-Za-z0-9_.-]+')
        if args.user is not None or args.port is not None:
            raise ValueError('SSH alias uses its existing user/port; omit --user and --port')
        # -G evaluates the existing SSH configuration; it does not open a connection.
        result = subprocess.run(['ssh', '-G', args.ssh_alias], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise ValueError('could not resolve selected SSH alias with ssh -G')
        resolved = {}
        for line in result.stdout.splitlines():
            key, _, value = line.partition(' ')
            if key in {'hostname', 'user', 'port'} and key not in resolved:
                resolved[key] = value.strip()
        if not all(resolved.get(key) for key in ['hostname', 'user', 'port']):
            raise ValueError('SSH alias did not resolve host, user and port')
        target = {'host': resolved['hostname'], 'user': resolved['user'],
                  'port': int(resolved['port']), 'ssh_alias': args.ssh_alias}
    else:
        if not args.user:
            raise ValueError('--user is required with --host')
        target = {'host': args.host, 'user': args.user, 'port': args.port or 22}
    identifier(target['host'], 'VM hostname')
    identifier(target['user'], 'VM user', r'[A-Za-z0-9_.-]+')
    if not 1 <= target['port'] <= 65535:
        raise ValueError('SSH port must be between 1 and 65535')
    return target


def validate_target(target):
    for key in ('name', 'host', 'user', 'workdir'):
        if not isinstance(target.get(key), str) or not target[key]:
            raise ValueError('VM target missing required field: ' + key)
    auth = target.get('auth')
    if not isinstance(auth, dict) or auth.get('method') not in {'key', 'password_env'}:
        raise ValueError('VM auth.method must be key or password_env')
    if 'password' in target or 'password' in auth:
        raise ValueError('inline password is forbidden')
    if auth.get('method') == 'password_env' and not auth.get('password_env'):
        raise ValueError('password_env auth requires password_env')


def proposed_config(data, args, endpoint):
    matches = [i for i, target in enumerate(data['vms']) if target.get('name') == args.name]
    if len(matches) > 1:
        raise ValueError('target name is not unique; existing config preserved')
    previous = data['vms'][matches[0]] if matches else {}
    target = dict(previous)
    target.update(endpoint, name=args.name, workdir=args.workdir)
    if not args.ssh_alias:
        target.pop('ssh_alias', None)
    if args.key_path:
        key = Path(args.key_path).expanduser()
        if not key.is_file():
            raise ValueError('key path must reference an existing file; configure does not create keys')
        target['auth'] = {'method': 'key', 'key_path': args.key_path}
    elif args.password_env:
        identifier(args.password_env, 'password environment variable name', r'[A-Za-z_][A-Za-z0-9_]*')
        target['auth'] = {'method': 'password_env', 'password_env': args.password_env}
    elif 'auth' not in target:
        target['auth'] = {'method': 'key'}
    target.setdefault('purpose', ['runtime-verify', 'e2e'])
    target.setdefault('limits', {'max_session_minutes': 30})
    if args.max_session_minutes is not None:
        if args.max_session_minutes <= 0:
            raise ValueError('session budget must be positive')
        if not isinstance(target['limits'], dict):
            raise ValueError('existing limits must be an object')
        target['limits'] = dict(target['limits'], max_session_minutes=args.max_session_minutes)
    if matches and target != previous and not args.replace:
        raise ValueError('target already exists; use --replace to change this named target')
    result = dict(data, vms=list(data['vms']))
    if matches:
        result['vms'][matches[0]] = target
    else:
        result['vms'].append(target)
    validate_target(target)
    return result


def write_private(path, content):
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Next: runtime-run.py doctor --runner ssh --vm NAME; configuration alone does not prove transport or scenario readiness.')
    parser.add_argument('--config', type=Path, default=Path.home() / '.athena/vm.json')
    parser.add_argument('--name', required=True)
    endpoint = parser.add_mutually_exclusive_group(required=True)
    endpoint.add_argument('--host', help='explicit hostname/address; requires --user')
    endpoint.add_argument('--ssh-alias', help='existing SSH alias; resolved locally with ssh -G')
    parser.add_argument('--user')
    parser.add_argument('--port', type=int)
    parser.add_argument('--workdir', required=True, help='existing absolute remote workspace; not created or probed')
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument('--key-path', help='existing private key path only; key contents are never read or copied')
    auth.add_argument('--password-env', help='environment variable name only; value is never read by configure')
    parser.add_argument('--max-session-minutes', type=int)
    parser.add_argument('--replace', action='store_true', help='explicitly update only the named target, retaining unknown fields')
    parser.add_argument('--dry-run', action='store_true', help='validate and preview without creating any files')
    args = parser.parse_args()
    try:
        identifier(args.name, 'VM name', r'[A-Za-z0-9_.-]+')
        if not args.workdir.startswith('/') or '..' in PurePosixPath(args.workdir).parts or '\x00' in args.workdir:
            raise ValueError('workdir must be absolute and contain no traversal')
        target = connection(args)
        path = args.config.expanduser()
        if path.parent.is_symlink():
            raise ValueError('VM config directory must not be a symlink')
        data = read_config(path)
        proposed_config(data, args, target)  # Complete validation before creating the directory/lock.
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Separate from the project index protocol: this stable OS lock only serializes vm.json edits.
            lock = os.open(path.with_name('.' + path.name + '.configure.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                current = read_config(path)
                candidate = proposed_config(current, args, target)
                if not path.exists() or candidate != current:
                    write_private(path, json.dumps(candidate, indent=2) + '\n')
            finally:
                os.close(lock)
        print(json.dumps({'name': args.name, 'config': str(path), 'dry_run': args.dry_run,
                          'configured': {'status': 'planned' if args.dry_run else 'passed'},
                          'transport': {'status': 'not_run'}, 'scenario': {'status': 'not_run'}}))
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired):
        # Parser/SSH diagnostics can contain local configuration; keep credentials and values out of output.
        print('VM configuration rejected: check explicit target arguments, existing private schema, or --replace; no connection attempted', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
