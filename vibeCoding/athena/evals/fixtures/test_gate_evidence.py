"""Evidence: `athena run`, the fallback collector, provability, redaction, tree binding
(athena-10-1 S2 AC5, AC6). The provability matrix is read from the frozen 9.9.9 suite and
checked against both the frozen implementation and the new core.
"""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from gate_harness import green, red, ENV, GATE, GOOD_DESIGN, PLATFORMS, VIBE, athena, call, git, project, sprint_dir, tmpdir

FROZEN_BINDING = VIBE / 'old/04-athena-8.9-9.9.9/claude/9.9.9/.claude/hooks/_input-binding.cjs'
LEGACY_SUITE = VIBE / 'old/04-athena-8.9-9.9.9/scripts/tests/athena999/test_state_review.py'
SPRINT = '2026-09-24-s'


def legacy_matrix():
    tree = ast.parse(LEGACY_SUITE.read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('POLICY_MATRIX', 'POLICY_EXTRAS'):
            found[node.targets[0].id] = ast.literal_eval(node.value)
    return list(found['POLICY_MATRIX']) + list(found['POLICY_EXTRAS'])


def node_json(code, module, data):
    proc = subprocess.run(['node', '-e', code, str(module)], input=json.dumps(data), text=True, capture_output=True, env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


def records(root):
    path = Path(root) / '.ai_state/.runtime/evidence' / f'{SPRINT}.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class Provability(unittest.TestCase):
    def test_legacy_matrix_on_frozen_and_new(self):
        matrix = legacy_matrix()
        self.assertGreaterEqual(len(matrix), 19)
        commands = [c for c, _, _ in matrix]
        frozen = node_json("const m=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                           "process.stdout.write(JSON.stringify(cs.map(c=>m.validationStatusPolicy(c))))", FROZEN_BINDING, commands)
        new = node_json("const m=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                        "process.stdout.write(JSON.stringify(cs.map(c=>m.policy(c))))", GATE / 'lib/evidence.cjs', commands)
        for (command, provable, reason), old, cur in zip(matrix, frozen, new):
            with self.subTest(command=command):
                self.assertEqual((bool(old['provable']), old.get('reason')), (provable, reason), 'frozen drifted')
                self.assertEqual((bool(cur['provable']), cur.get('reason')), (provable, reason))

    def test_masked_pipeline_beyond_4000_chars(self):
        command = 'npm test ' + ('-v ' * 1400) + '| tail -8'
        cur = node_json("const m=require(process.argv[1]);process.stdout.write(JSON.stringify(m.policy(JSON.parse(require('fs').readFileSync(0,'utf8')))))",
                        GATE / 'lib/evidence.cjs', command)
        self.assertEqual(cur, {'provable': False, 'reason': 'pipeline_without_pipefail'})


class Redaction(unittest.TestCase):
    CASES = (
        ('token=abc123', 'abc123'), ('PASSWORD: hunter2', 'hunter2'), ('--api-key sk-live-xyz', 'sk-live-xyz'),
        ('Authorization: Bearer eyJhbGciOi', 'eyJhbGciOi'), ('postgres://u:pw@db/x', 'u:pw'), ('https://bob:s3cr3t@h/x', 's3cr3t'),
        ('sk-abcdefgh12345678', 'sk-abcdefgh12345678'), ('ghp_ABCDEFGHijkl1234', 'ghp_ABCDEFGHijkl1234'),
        ('AWS_SECRET_ACCESS_KEY=AbCd/123', 'AbCd/123'), ('AKIAABCDEFGHIJKLMNOP', 'AKIAABCDEFGHIJKLMNOP'),
        ('database_url=mysql://a:b@c', 'a:b@c'), ('client-secret: zzz', 'zzz'),
    )

    def test_redaction_and_truncation(self):
        texts = [text for text, _ in self.CASES] + ['head ' + 'x' * 2000 + ' TAIL-MARKER']
        out = node_json("const m=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                        "process.stdout.write(JSON.stringify(cs.map(c=>m.redact(c))))", GATE / 'lib/evidence.cjs', texts)
        for (text, secret), red in zip(self.CASES, out):
            with self.subTest(text=text):
                self.assertNotIn(secret, red)
                self.assertIn('[REDACTED]', red)
        self.assertIn('…[truncated ', out[-1])
        self.assertTrue(out[-1].endswith('TAIL-MARKER'))


class AthenaRun(unittest.TestCase):
    def test_records_real_exit_kind_provable_and_tree(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        self.assertEqual(athena('run', '--', 'node', '-e', 'process.exit(3)', cwd=root).returncode, 3)
        self.assertEqual(athena('run', '--covers', 'AC1', '--', 'python3 -m unittest --help | cat', cwd=root).returncode, 0)
        self.assertEqual(athena('run', '--', 'python3 -m unittest --help; true', cwd=root).returncode, 0)
        rows = records(root)
        self.assertEqual([r['exit'] for r in rows], [3, 0, 0])
        self.assertEqual([r['kind'] for r in rows], ['other', 'test', 'test'])
        self.assertEqual([r['provable'] for r in rows], [False, True, False], 'athena run adds pipefail; `;` stays unprovable')
        self.assertEqual(rows[1]['covers'], ['AC1'])
        self.assertEqual(rows[2]['reason'], 'validation_status_not_reported')
        self.assertTrue(all(len(r['tree_sha']) == 40 for r in rows))
        self.assertEqual(len({r['tree_sha'] for r in rows}), 1)

    def test_worktree_run_lands_in_main_checkout(self):
        tmp = tmpdir(self)
        root = project(tmp, design=GOOD_DESIGN)
        git(root, 'worktree', 'add', '-q', str(tmp / 'wt'))
        green(root, cwd=tmp / 'wt')
        self.assertEqual(len(records(root)), 1)
        self.assertFalse((tmp / 'wt/.ai_state/.runtime').exists())

    def test_output_redacted_command_bounded_and_no_sprint(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        athena('run', '--', 'echo token=fixture-secret; ' + 'echo ' + 'y' * 600, cwd=root)
        row = records(root)[0]
        self.assertNotIn('fixture-secret', row['output'] + row['command'])
        self.assertLessEqual(len(row['command']), 500)
        idle = project(tmpdir(self), path='', stage='')
        run = athena('run', '--', 'node', '-e', 'process.exit(4)', cwd=idle)
        self.assertEqual(run.returncode, 4)
        self.assertIn('not recorded', run.stderr)

    def test_bad_arguments(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        for args in (('run',), ('run', '--covers', 'x', '--', 'ls'), ('run', '--kind', 'test', '--', 'ls'), ('run', 'ls'), ('nope',)):
            with self.subTest(args=args):
                self.assertEqual(athena(*args, cwd=root).returncode, 2)


class RunExplicitEnvAndCounts(unittest.TestCase):
    """G-005: explicit env is replayable; a successful empty test run proves nothing."""

    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, design=GOOD_DESIGN)
        self.target = self.tmp / 'env.test.cjs'
        self.marker = "spaces 'quotes' a=b $dollar; $(exit 9)"
        self.target.write_text(
            "const assert = require('node:assert/strict');\n"
            "require('node:test')('explicit env', () => {\n"
            "  assert.equal(process.env.ATHENA_TEST_ENABLED, '1');\n"
            f"  assert.equal(process.env.ATHENA_TEST_MARK, {json.dumps(self.marker)});\n"
            "});\n", encoding='utf-8')

    def test_explicit_env_record_and_argv_replay(self):
        run = athena('run', '--env', 'ATHENA_TEST_ENABLED=0', '--env', 'ATHENA_TEST_ENABLED=1',
                     '--env', f'ATHENA_TEST_MARK={self.marker}', '--covers', 'AC1', '--',
                     'node', '--test', str(self.target), cwd=self.root,
                     env={'ATHENA_TEST_IMPLICIT': 'do not record'})
        self.assertEqual(run.returncode, 0, run.stderr)
        row = records(self.root)[0]
        self.assertTrue(row['provable'])
        self.assertEqual(row['env'], {'ATHENA_TEST_ENABLED': '1', 'ATHENA_TEST_MARK': self.marker})
        self.assertIn('ATHENA_TEST_ENABLED=1', row['command'])
        self.assertIn('ATHENA_TEST_MARK=', row['command'])
        self.assertNotIn('ATHENA_TEST_IMPLICIT', json.dumps(row))
        self.assertEqual(row['covers'], ['AC1'])
        replay = subprocess.run(['bash', '-o', 'pipefail', '-c', row['command']], cwd=self.root,
                                env=ENV, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)

    def test_explicit_env_shell_replay_applies_to_all_segments(self):
        command = f'node --test {self.target} && node --test {self.target}'
        run = athena('run', '--env', 'ATHENA_TEST_ENABLED=1', '--env', f'ATHENA_TEST_MARK={self.marker}',
                     '--', command, cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        row = records(self.root)[0]
        self.assertTrue(row['provable'])
        replay = subprocess.run(['bash', '-o', 'pipefail', '-c', row['command']], cwd=self.root,
                                env=ENV, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
        self.assertEqual(replay.stdout.count('explicit env'), 2)

    def test_long_explicit_env_is_not_truncated_for_replay(self):
        value = 'z' * 2200 + self.marker
        self.target.write_text(self.target.read_text().replace(json.dumps(self.marker), json.dumps(value)))
        run = athena('run', '--env', 'ATHENA_TEST_ENABLED=1', '--env', f'ATHENA_TEST_MARK={value}',
                     '--', 'node', '--test', str(self.target), cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        row = records(self.root)[0]
        self.assertTrue(row['provable'])
        self.assertEqual(row['env']['ATHENA_TEST_MARK'], value)
        replay = subprocess.run(['bash', '-o', 'pipefail', '-c', row['command']], cwd=self.root,
                                env=ENV, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)

    def test_explicit_path_keeps_existing_shadow_policy(self):
        for cmd in (('node', '--test', str(self.target)), (f'node --test {self.target}',)):
            run = athena('run', '--env', f"PATH={ENV['PATH']}", '--env', 'ATHENA_TEST_ENABLED=1',
                         '--env', f'ATHENA_TEST_MARK={self.marker}', '--', *cmd, cwd=self.root)
            self.assertEqual(run.returncode, 0, run.stderr)
            row = records(self.root)[-1]
            self.assertFalse(row['provable'])
            self.assertEqual(row['reason'], 'validation_shadowable')

    def test_readonly_shell_env_name_replays(self):
        self.target.write_text("require('node:test')('UID env', () => {\n"
                               "  require('node:assert/strict').equal(process.env.UID, '123');\n});\n")
        run = athena('run', '--env', 'UID=123', '--', 'node', '--test', str(self.target), cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        row = records(self.root)[0]
        self.assertTrue(row['provable'])
        replay = subprocess.run(['bash', '-o', 'pipefail', '-c', row['command']], cwd=self.root,
                                env=ENV, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)

    def test_sensitive_names_rejected_without_execution_or_record(self):
        for name in ('API_KEY', 'github_token', 'MY_SECRET', 'PASSWORD', 'DATABASE_URL', 'PASSWD'):
            with self.subTest(name=name):
                run = athena('run', '--env', f'{name}=fixture-private-value', '--',
                             'node', '-e', 'process.exit(9)', cwd=self.root)
                self.assertEqual(run.returncode, 2)
                self.assertIn('env 文件', run.stderr)
                self.assertNotIn('fixture-private-value', run.stderr + run.stdout)
        self.assertEqual(records(self.root), [])

    def test_credential_value_under_ordinary_name_is_rejected(self):
        value = 'sk-abcdefgh12345678'
        run = athena('run', '--env', f'ATHENA_TEST_MARK={value}', '--',
                     'node', '-e', 'process.exit(9)', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('env 文件', run.stderr)
        self.assertNotIn(value, run.stderr + run.stdout)
        self.assertEqual(records(self.root), [])

    def test_env_validation_and_no_implicit_capture(self):
        for value in ('missing-equals', '1INVALID=value', '=value'):
            self.assertEqual(athena('run', '--env', value, '--', 'node', '--test', str(self.target),
                                    cwd=self.root).returncode, 2)
        run = green(self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(records(self.root)[0]['provable'])
        self.assertFalse(records(self.root)[0].get('env'))

    def test_node_zero_tests_in_both_reporters(self):
        no_files = str(self.tmp / 'unmatched/*.test.cjs')
        for reporter in ('spec', 'tap'):
            run = athena('run', '--', 'node', '--test', f'--test-reporter={reporter}', no_files, cwd=self.root)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('tests 0', run.stdout)
            row = records(self.root)[-1]
            self.assertEqual((row['kind'], row['exit'], row['provable']), ('test', 0, False))
            self.assertIn('零用例', row['reason'])

    def test_pytest_zero_and_nonzero_cases(self):
        target = self.tmp / 'pytest-cases'
        target.mkdir()
        # Model a wrapper/plugin that turns pytest's empty-suite status into exit 0.
        (target / 'conftest.py').write_text('def pytest_sessionfinish(session):\n    session.exitstatus = 0\n')
        env = {'PATH': f"{Path(sys.executable).parent}{os.pathsep}{ENV['PATH']}"}
        run = athena('run', '--', 'python3', '-m', 'pytest', str(target), cwd=self.root, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('collected 0 items', run.stdout)
        row = records(self.root)[-1]
        self.assertFalse(row['provable'])
        self.assertIn('零用例', row['reason'])
        (target / 'test_case.py').write_text('def test_ok():\n    assert 1 + 1 == 2\n')
        run = athena('run', '--', 'python3', '-m', 'pytest', '-q', str(target), cwd=self.root, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(records(self.root)[-1]['provable'])

    def test_npm_test_wrapping_empty_node_suite(self):
        (self.root / 'package.json').write_text(json.dumps({'scripts': {
            'test': f'node --test "{self.tmp}/unmatched/*.test.cjs"'}}))
        run = athena('run', '--', 'npm', 'test', cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('tests 0', run.stdout)
        row = records(self.root)[-1]
        self.assertFalse(row['provable'])
        self.assertIn('零用例', row['reason'])

    def test_zero_detection_only_matches_runner_summaries(self):
        outputs = ['ℹ tests 0\n', '# tests 0\n', 'collected 0 items\n', 'no tests ran in 0.01s\n',
                   '\x1b[34mℹ tests 0\x1b[39m\n',
                   '===== no tests ran in 0.01s =====\n', 'no tests ran in 60.00s (0:01:00)\n',
                   '===== no tests ran in 86400.00s (1 day, 0:00:00) =====\n', '# tests 10\n', 'ℹ tests 2\n',
                   'zero tests might run', 'example: # tests 0', 'tests 0', '1 passed in 0.01s']
        actual = node_json("const m=require(process.argv[1]);const xs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                           "process.stdout.write(JSON.stringify(xs.map(x=>m.zeroTests(x))))", GATE / 'cli/run.cjs', outputs)
        self.assertEqual(actual, [True] * 8 + [False] * 6)


class RunOverSsh(unittest.TestCase):
    """G-002: ssh to a VM registered in ~/.athena/vm.json proves like the remote command would locally."""

    def setUp(self):
        tmp = tmpdir(self)
        self.root = project(tmp, design=GOOD_DESIGN)
        home = tmp / 'home'
        (home / '.athena').mkdir(parents=True)
        (home / '.athena/vm.json').write_text(json.dumps({'version': 1, 'vms': [
            {'name': 'dev', 'host': '10.0.0.5', 'port': 22, 'user': 'root', 'auth': {'method': 'key', 'key_path': '~/.ssh/x'}},
            {'name': 'dev2', 'host': 'vm2.example.invalid', 'port': 2222, 'user': 'ci'}]}), encoding='utf-8')
        bin_dir = tmp / 'bin'
        bin_dir.mkdir()
        (bin_dir / 'ssh').write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        (bin_dir / 'ssh').chmod(0o755)
        import os
        self.env = {'HOME': str(home), 'PATH': f"{bin_dir}{os.pathsep}{ENV['PATH']}"}

    def run_ssh(self, *argv):
        self.assertEqual(athena('run', '--', 'ssh', *argv, cwd=self.root, env=self.env).returncode, 0)
        return records(self.root)[-1]

    def test_registered_vm_with_provable_remote_command(self):
        row = self.run_ssh('-o', 'BatchMode=yes', 'root@10.0.0.5', 'cd /opt/w && npm test')
        self.assertEqual((row['kind'], row['provable'], row['reason']), ('test', True, None))
        self.assertEqual((row['vm'], row['remote']), ('dev', 'cd /opt/w && npm test'))
        row = self.run_ssh('-p', '2222', '-l', 'ci', 'vm2.example.invalid', 'go', 'test', './...')
        self.assertEqual((row['kind'], row['provable'], row['vm']), ('test', True, 'dev2'))

    def test_remote_command_follows_local_rules(self):
        row = self.run_ssh('root@10.0.0.5', 'npm test | tail -3')
        self.assertEqual((row['kind'], row['provable'], row['reason']), ('test', False, 'pipeline_without_pipefail'))
        row = self.run_ssh('root@10.0.0.5', 'uname -a')
        self.assertEqual((row['kind'], row['provable']), ('other', False))

    def test_unregistered_or_redirected_ssh_stays_unprovable(self):
        for argv in (('root@10.0.0.6', 'npm test'),                      # host not registered
                     ('admin@10.0.0.5', 'npm test'),                     # user mismatch
                     ('10.0.0.5', 'npm test'),                           # user unknown
                     ('-p', '2200', 'root@10.0.0.5', 'npm test'),        # port mismatch
                     ('-o', 'HostName=10.0.0.6', 'root@10.0.0.5', 'npm test'),
                     ('-o', 'ProxyCommand=sh -c x', 'root@10.0.0.5', 'npm test'),
                     ('-F', '/tmp/cfg', 'root@10.0.0.5', 'npm test'),
                     ('-f', 'root@10.0.0.5', 'npm test')):
            with self.subTest(argv=argv):
                row = self.run_ssh(*argv)
                self.assertFalse(row['provable'])
                self.assertNotIn('vm', row)


class Collector(unittest.TestCase):
    """Fallback: a validation command seen by post_tool is recorded with each platform's exit semantics."""

    def test_platform_exit_semantics(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        call('cc', 'post_bash', root, command='npm test')                       # CC: no exit_code, not interrupted → 0
        call('cc', 'post_bash_fail', root, command='npm test')                  # PostToolUseFailure → 1
        call('cx', 'post_bash', root, command='cargo test', exit=2)
        call('pi', 'post_bash', root, command='go test ./...')                  # isError false → 0
        call('pi', 'post_bash_fail', root, command='go test ./...')             # isError true → 1
        call('cc', 'post_bash', root, command='ls -la')                         # not a validation command
        call('cc', 'post_bash', root, command='node ~/.athena/current/cli.cjs run -- npm test')  # recorded by athena run itself
        rows = records(root)
        self.assertEqual([(r['platform'], r['exit'], r['source']) for r in rows],
                         [('cc', 0, 'collector'), ('cc', 1, 'collector'), ('cx', 2, 'collector'), ('pi', 0, 'collector'), ('pi', 1, 'collector')])
        self.assertEqual([r['provable'] for r in rows], [True, True, True, True, True])

    def test_unprovable_shapes_are_recorded_unprovable(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        for platform in PLATFORMS:
            call(platform, 'post_bash', root, command='npm test | tail -3', exit=0)
        rows = records(root)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r['provable'] is False and r['reason'] == 'pipeline_without_pipefail' for r in rows))


if __name__ == '__main__':
    unittest.main()
