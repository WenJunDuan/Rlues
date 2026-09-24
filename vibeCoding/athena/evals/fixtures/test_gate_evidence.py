"""Evidence: `athena run`, the fallback collector, provability, redaction, tree binding
(athena-10-1 S2 AC5, AC6). The provability matrix is read from the frozen 9.9.9 suite and
checked against both the frozen implementation and the new core.
"""
import ast
import json
from pathlib import Path
import subprocess
import unittest

from gate_harness import green, red, ENV, GATE, GOOD_DESIGN, PLATFORMS, VIBE, athena, call, git, project, sprint_dir, tmpdir

FROZEN_BINDING = VIBE / 'claude/9.9.9/.claude/hooks/_input-binding.cjs'
LEGACY_SUITE = VIBE / 'scripts/tests/athena999/test_state_review.py'
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
