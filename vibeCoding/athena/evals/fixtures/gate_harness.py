"""Shared fixture harness for the 10.1 gate core (athena-10-1 S2).

Every intent (bash / write / agent / stop / post_bash / session) is rendered as the
platform's own hook payload and sent through `gate/hook.cjs` exactly as the platform would:
cc and cx as a subprocess with the payload on stdin, pi in-process through `run('pi', …)`.
`Verdict.blocked` is decoded from the platform's own blocking protocol, so one expectation
table checks all three adapters.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

ATHENA = Path(__file__).resolve().parents[2]
VIBE = ATHENA.parent
GATE = ATHENA / 'gate'
HOOK = GATE / 'hook.cjs'
CLI = GATE / 'cli.cjs'
PLATFORMS = ('cc', 'cx', 'pi')
ENV = {**os.environ,
       'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
       'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
       'PYTHONDONTWRITEBYTECODE': '1'}

PI_DRIVER = ("const {run}=require(process.argv[1]);"
             "const p=JSON.parse(require('fs').readFileSync(0,'utf8'));"
             "process.stdout.write(JSON.stringify(run('pi',p).output));")
CC_EVENTS = {'bash': 'PreToolUse', 'write': 'PreToolUse', 'agent': 'PreToolUse', 'stop': 'Stop',
             'post_bash': 'PostToolUse', 'post_bash_fail': 'PostToolUseFailure', 'session': 'SessionStart',
             'prompt': 'UserPromptSubmit', 'subagent_start': 'SubagentStart'}
PI_EVENTS = {'bash': 'tool_call', 'write': 'tool_call', 'stop': 'agent_end', 'post_bash': 'tool_result',
             'post_bash_fail': 'tool_result', 'session': 'session_start', 'prompt': 'before_agent_start'}


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], check=check, capture_output=True, text=True, env=ENV)


class Verdict:
    def __init__(self, blocked, reason, raw, context=''):
        self.blocked, self.reason, self.raw, self.context = blocked, reason, raw, context

    def __repr__(self):
        return f'Verdict(blocked={self.blocked}, reason={self.reason!r})'


def payload(platform, intent, cwd, **kw):
    cwd = str(cwd)
    if platform == 'pi':
        body = {'type': PI_EVENTS[intent], 'cwd': cwd}
        if intent == 'bash':
            body.update(toolName='bash', input={'command': kw['command']})
        elif intent == 'write':
            body.update(toolName='edit', input={'path': str(kw['file'])})
        elif intent in ('post_bash', 'post_bash_fail'):
            body.update(toolName='bash', input={'command': kw['command']}, isError=intent == 'post_bash_fail',
                        exitCode=kw.get('exit'))
        if kw.get('session'):
            body['session_id'] = kw['session']
        return body
    body = {'hook_event_name': CC_EVENTS[intent], 'cwd': cwd, 'session_id': kw.get('session', 'fixture-session')}
    if intent == 'bash':
        command = kw['command']
        body.update(tool_name='Bash', tool_input={'command': ['bash', '-lc', command] if platform == 'cx' else command})
    elif intent == 'write':
        files = kw['file'] if isinstance(kw['file'], (list, tuple)) else [kw['file']]
        if platform == 'cx':
            patch = '*** Begin Patch\n' + ''.join(f'*** Update File: {f}\n@@\n-a\n+b\n' for f in files) + '*** End Patch\n'
            body.update(tool_name='apply_patch', tool_input={'command': patch})
        else:
            body.update(tool_name='Write', tool_input={'file_path': str(files[0]), 'content': 'x'})
    elif intent == 'agent':
        if platform == 'cx':
            body.update(tool_name='spawn_agent', tool_input={'agent_type': kw['type'], 'message': kw.get('task', '')})
        else:
            tool_input = {'subagent_type': kw['type'], 'prompt': kw.get('task', '')}
            if kw.get('isolation'):
                tool_input['isolation'] = kw['isolation']
            body.update(tool_name='Agent', tool_input=tool_input)
    elif intent in ('post_bash', 'post_bash_fail'):
        command = kw['command']
        body.update(tool_name='Bash', tool_input={'command': command}, tool_use_id='fixture-tool-use')
        if kw.get('exit') is not None:
            body['tool_response'] = {'exit_code': kw['exit'], 'stdout': 'ok'}
        elif intent == 'post_bash':
            body['tool_response'] = {'stdout': 'ok', 'stderr': '', 'interrupted': False}
    elif intent == 'subagent_start':
        body.update(agent_type=kw['type'], agent_id='fixture-agent')
    return body


def call(platform, intent, cwd, env=None, **kw):
    body = payload(platform, intent, cwd, **kw)
    run_env = {**ENV, **(env or {})}
    if platform == 'pi':
        proc = subprocess.run(['node', '-e', PI_DRIVER, str(HOOK)], input=json.dumps(body), text=True,
                              capture_output=True, cwd=str(cwd), env=run_env)
        if proc.returncode:
            raise AssertionError(proc.stderr)
        out = json.loads(proc.stdout or '{}')
        return Verdict(bool(out.get('block') or out.get('stop')), out.get('reason', ''), out, out.get('context', ''))
    proc = subprocess.run(['node', str(HOOK), CC_EVENTS[intent], '--platform', platform], input=json.dumps(body),
                          text=True, capture_output=True, cwd=str(cwd), env=run_env)
    blocked, reason, context = proc.returncode == 2, proc.stderr, ''
    for line in proc.stdout.splitlines():
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if data.get('decision') == 'block':
            blocked, reason = True, data.get('reason', '')
        context = (data.get('hookSpecificOutput') or {}).get('additionalContext', context)
    if proc.returncode not in (0, 2):
        raise AssertionError(f'hook exited {proc.returncode}: {proc.stderr}')
    return Verdict(blocked, reason, proc, context)


def athena(*args, cwd, env=None):
    return subprocess.run(['node', str(CLI), *args], capture_output=True, text=True, cwd=str(cwd), env={**ENV, **(env or {})})


def check_file(root, passing=True):
    """A node:test file OUTSIDE the repository (so it never changes the source tree)."""
    target = Path(root).parent / ('athena-green.test.cjs' if passing else 'athena-red.test.cjs')
    body = "require('node:test')('ok', () => {});\n" if passing else "require('node:test')('bad', () => { throw new Error('red'); });\n"
    target.write_text(body, encoding='utf-8')
    return str(target)


def green(root, cwd=None):
    """Record a provable passing test run (`athena run -- node --test <file>`)."""
    return athena('run', '--', 'node', '--test', check_file(root), cwd=cwd or root)


def red(root, cwd=None):
    return athena('run', '--', 'node', '--test', check_file(root, passing=False), cwd=cwd or root)


def project(base, name='proj', *, path='Feature', stage='impl', sprint='2026-09-24-s', design=None, extra_index='', commit=True):
    """A git repo with an Athena _index (stage None = no .ai_state; path/stage '' = idle)."""
    root = Path(base) / name
    root.mkdir(parents=True)
    git(root, 'init', '-q')
    (root / 'app.js').write_text('module.exports = 1;\n', encoding='utf-8')
    if stage is not None:
        state = root / '.ai_state'
        (state / 'sprints' / sprint).mkdir(parents=True)
        slug = sprint if (path or stage) else ''
        (state / '_index.md').write_text(
            f'---\nversion: "10.1"\npath: "{path}"\nstage: "{stage}"\ncurrent_sprint_slug: "{slug}"\n{extra_index}---\n',
            encoding='utf-8')
        if design is not None:
            (state / 'sprints' / sprint / 'design.md').write_text(design, encoding='utf-8')
    if commit:
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'base')
    return root


def set_index(root, **fields):
    """Rewrite scalar _index fields (quoted)."""
    index = Path(root) / '.ai_state/_index.md'
    lines = index.read_text(encoding='utf-8').split('\n')
    for key, value in fields.items():
        rendered = value if isinstance(value, str) and value.startswith(('[', '{')) else json.dumps(value, ensure_ascii=False)
        for i, line in enumerate(lines):
            if line.startswith(f'{key}:'):
                lines[i] = f'{key}: {rendered}'
                break
        else:
            lines.insert(1, f'{key}: {rendered}')
    index.write_text('\n'.join(lines), encoding='utf-8')


def sprint_dir(root, sprint='2026-09-24-s'):
    return Path(root) / '.ai_state/sprints' / sprint


GOOD_DESIGN = '---\nbase_commit: ""\n---\n# Design\n\n## 验收标准\n\n- AC1: `add(1,1)` returns 2\n'


def tmpdir(testcase):
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    return Path(tmp.name).resolve()
