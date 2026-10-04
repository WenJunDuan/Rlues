"""`athena run --rebind` (athena-10-1-5 S1 AC3): after an edit the sprint's latest provable PASS
test/typecheck commands are RE-RUN on the current tree and recorded anew with the same covers and
env. A PASS is never copied: every new PASS record corresponds to a real execution."""
import json
import os
from pathlib import Path
import unittest

from gate_harness import ENV, GOOD_DESIGN, athena, check_file, project, tmpdir

SPRINT = '2026-09-24-s'


def records(root):
    path = Path(root) / '.ai_state/.runtime/evidence' / f'{SPRINT}.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class Rebind(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, design=GOOD_DESIGN)

    def probe(self, name):
        """A node:test file outside the repo: counts its executions, fails when app.js exports 3."""
        target, counter = self.tmp / f'{name}.test.cjs', self.tmp / f'{name}.count'
        target.write_text(
            "const fs = require('fs');\n"
            f"fs.appendFileSync({json.dumps(str(counter))}, (process.env.ATHENA_MARK || '-') + '\\n');\n"
            f"require('node:test')('app', () => {{ if (require({json.dumps(str(self.root / 'app.js'))}) === 3) throw new Error('red'); }});\n",
            encoding='utf-8')
        return str(target), counter

    def edit(self, value=2):
        (self.root / 'app.js').write_text(f'module.exports = {value};\n', encoding='utf-8')

    def rebind(self, *extra, cwd=None):
        return athena('run', '--rebind', *extra, cwd=cwd or self.root)

    def test_reruns_on_the_current_tree_with_same_covers_and_env(self):
        target, counter = self.probe('a')
        run = athena('run', '--covers', 'AC1', '--env', 'ATHENA_MARK=m1', '--', 'node', '--test', target, cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        old = records(self.root)[-1]
        self.edit()
        run = self.rebind()
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = records(self.root)
        new = rows[-1]
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(new['tree_sha'], old['tree_sha'])
        self.assertNotEqual(new['id'], old['id'])
        self.assertEqual((new['command'], new['covers'], new['env'], new['exit'], new['provable'], new['kind']),
                         (old['command'], ['AC1'], {'ATHENA_MARK': 'm1'}, 0, True, 'test'))
        self.assertEqual(counter.read_text().split(), ['m1', 'm1'], 'the command really ran a second time, with its env')
        self.assertIn('1 re-run, 0 already on this tree, 0 failed', run.stderr)
        # the rebound record is what `athena run` itself would have written for this tree
        check = athena('run', '--', 'node', '--test', check_file(self.root), cwd=self.root)
        self.assertEqual(records(self.root)[-1]['tree_sha'], new['tree_sha'], check.stderr)

    def test_failed_rerun_records_no_pass_and_exits_nonzero(self):
        target, counter = self.probe('a')
        self.assertEqual(athena('run', '--covers', 'AC1', '--', 'node', '--test', target, cwd=self.root).returncode, 0)
        old_tree = records(self.root)[-1]['tree_sha']
        self.edit(3)
        run = self.rebind()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn('rebind FAILED', run.stderr)
        self.assertIn(f'node --test {target}', run.stderr.split('rebind FAILED')[1])
        self.assertEqual(run.stderr.strip().splitlines()[-1], 'next: fix the failure, then `athena run --rebind`')
        rows = records(self.root)
        self.assertEqual(len(counter.read_text().split()), 2)
        self.assertEqual([(r['exit'] == 0, r['tree_sha'] == old_tree) for r in rows], [(True, True), (False, False)])
        # after the fix the failed command is still picked up (its last PASS is the old one)
        self.edit(4)
        self.assertEqual(self.rebind().returncode, 0)
        self.assertEqual((records(self.root)[-1]['exit'], records(self.root)[-1]['covers']), (0, ['AC1']))

    def test_each_distinct_command_once_and_only_provable_pass_test_records(self):
        a, count_a = self.probe('a')
        b, count_b = self.probe('b')
        c, count_c = self.probe('c')
        for args in (('--covers', 'AC1', '--', 'node', '--test', a), ('--', 'node', '--test', a),   # same command twice
                     ('--covers', 'AC2', '--', f'node --test {b}'),                                 # shell form
                     ('--', f'node --test {c}; echo done'),                                         # unprovable PASS
                     ('--', 'echo', 'hi'), ('--', 'node', '--check', str(self.root / 'app.js'))):   # other, lint
            self.assertEqual(athena('run', *args, cwd=self.root).returncode, 0)
        self.assertNotEqual(athena('run', '--', 'node', '--test', check_file(self.root, passing=False), cwd=self.root).returncode, 0)
        before = len(records(self.root))
        self.edit()
        run = self.rebind()
        self.assertEqual(run.returncode, 0, run.stderr)
        new = records(self.root)[before:]
        self.assertEqual([(r['command'], r['covers']) for r in new], [(f'node --test {a}', ['AC1']), (f'node --test {b}', ['AC2'])])
        self.assertTrue(all(r['provable'] and r['exit'] == 0 and r['tree_sha'] == new[0]['tree_sha'] for r in new))
        self.assertEqual([len(p.read_text().split()) for p in (count_a, count_b, count_c)], [3, 2, 1])

    def test_unchanged_tree_runs_nothing(self):
        target, counter = self.probe('a')
        self.assertEqual(athena('run', '--', 'node', '--test', target, cwd=self.root).returncode, 0)
        run = self.rebind()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('0 re-run, 1 already on this tree', run.stderr)
        self.assertEqual((len(records(self.root)), len(counter.read_text().split())), (1, 1))

    def test_later_failure_on_same_tree_requires_a_real_rerun(self):
        target, counter = self.probe('external')
        script = Path(target)
        passing = script.read_text()
        command = ('run', '--covers', 'AC1', '--', 'node', '--test', target)
        self.assertEqual(athena(*command, cwd=self.root).returncode, 0)
        old_tree = records(self.root)[-1]['tree_sha']
        script.write_text(passing.replace('=== 3', '=== 1'))
        self.assertNotEqual(athena(*command, cwd=self.root).returncode, 0)
        self.assertEqual(records(self.root)[-1]['tree_sha'], old_tree)
        run = self.rebind()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn('1 re-run, 0 already on this tree, 1 failed', run.stderr)
        self.assertEqual(len(counter.read_text().split()), 3)
        script.write_text(passing)
        self.assertEqual(self.rebind().returncode, 0)
        self.assertEqual((records(self.root)[-1]['exit'], records(self.root)[-1]['covers']), (0, ['AC1']))
        self.assertEqual(len(counter.read_text().split()), 4)
        self.assertEqual(self.rebind().returncode, 0)
        self.assertEqual(len(counter.read_text().split()), 4, 'a newer PASS permits skipping again')

    def test_current_pass_without_covers_reruns_to_restore_ac_coverage(self):
        target, counter = self.probe('coverage')
        self.assertEqual(athena('run', '--covers', 'AC1', '--', 'node', '--test', target, cwd=self.root).returncode, 0)
        self.edit()
        self.assertEqual(athena('run', '--', 'node', '--test', target, cwd=self.root).returncode, 0)
        run = self.rebind()
        self.assertEqual(run.returncode, 0, run.stderr)
        status = json.loads(athena('status', '--json', cwd=self.root).stdout)
        self.assertEqual(status['acs'][0]['state'], 'covered')
        self.assertEqual(records(self.root)[-1]['covers'], ['AC1'])
        self.assertEqual(len(counter.read_text().split()), 3, 'restoring coverage must execute the check')

    def test_later_unregistered_ssh_attempt_cannot_reuse_a_registered_pass(self):
        bin_dir, task_home = self.tmp / 'bin', self.tmp / 'home'
        bin_dir.mkdir()
        (task_home / '.athena').mkdir(parents=True)
        vm_file = task_home / '.athena/vm.json'
        vm_json = json.dumps({'vms': [{'name': 'dev', 'host': '10.0.0.5', 'user': 'root'}]})
        vm_file.write_text(vm_json)
        ssh, counter = bin_dir / 'ssh', self.tmp / 'ssh.count'
        script = '#!/usr/bin/env node\n' + f"require('fs').appendFileSync({json.dumps(str(counter))}, 'run\\n');\n"
        ssh.write_text(script + 'process.exit(0);\n')
        ssh.chmod(0o755)
        env = {'HOME': str(task_home), 'PATH': f"{bin_dir}{os.pathsep}{ENV['PATH']}"}
        command = ('run', '--covers', 'AC1', '--', 'ssh', 'root@10.0.0.5', 'npm test')
        self.assertEqual(athena(*command, cwd=self.root, env=env).returncode, 0)
        old_tree = records(self.root)[-1]['tree_sha']
        vm_file.unlink()
        ssh.write_text(script + 'process.exit(1);\n')
        self.assertEqual(athena(*command, cwd=self.root, env=env).returncode, 1)
        self.assertEqual((records(self.root)[-1]['kind'], records(self.root)[-1]['tree_sha']), ('other', old_tree))
        run = athena('run', '--rebind', cwd=self.root, env=env)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn('1 re-run, 0 already on this tree, 1 failed', run.stderr)
        ssh.write_text(script + 'process.exit(0);\n')
        self.assertEqual(athena('run', '--rebind', cwd=self.root, env=env).returncode, 1, 'unregistered exit 0 is still unprovable')
        vm_file.write_text(vm_json)
        self.assertEqual(athena('run', '--rebind', cwd=self.root, env=env).returncode, 0)
        self.assertEqual(len(counter.read_text().split()), 5)

    def test_record_without_argv_is_not_replayed_or_copied(self):
        target, counter = self.probe('a')
        self.assertEqual(athena('run', '--covers', 'AC1', '--', 'node', '--test', target, cwd=self.root).returncode, 0)
        path = self.root / '.ai_state/.runtime/evidence' / f'{SPRINT}.jsonl'
        row = json.loads(path.read_text())
        self.assertEqual(row.pop('argv'), ['node', '--test', target])
        path.write_text(json.dumps(row) + '\n')  # a record written before 10.1.5
        self.edit()
        run = self.rebind()
        self.assertEqual(run.returncode, 1)
        self.assertIn(f'athena run --covers AC1 -- node --test {target}', run.stderr)
        self.assertEqual((len(records(self.root)), len(counter.read_text().split())), (1, 1))

    def test_long_commands_do_not_merge_distinct_checks(self):
        long_dir = self.tmp.joinpath(*(['segment-' + 'x' * 170] * 3))
        long_dir.mkdir(parents=True)
        counters = []
        for name, ac in [('a', 'AC1'), ('b', 'AC2')]:
            original, counter = self.probe(name)
            target = long_dir / f'{name}.test.cjs'
            target.write_text(Path(original).read_text())
            counters.append(counter)
            self.assertEqual(athena('run', '--covers', ac, '--', 'node', '--test', str(target), cwd=self.root).returncode, 0)
        self.edit()
        run = self.rebind()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual([len(p.read_text().split()) for p in counters], [2, 2])
        self.assertEqual([r['covers'] for r in records(self.root)[-2:]], [['AC1'], ['AC2']])

    def test_usage(self):
        target, _ = self.probe('a')
        for extra in (('--', 'node', '--test', target), ('--covers', 'AC1'), ('--env', 'A=1')):
            with self.subTest(extra=extra):
                run = self.rebind(*extra)
                self.assertEqual(run.returncode, 2)
                self.assertIn('sample: athena run --rebind', run.stderr)
        run = self.rebind()
        self.assertEqual(run.returncode, 2)
        self.assertIn('no provable PASS', run.stderr)
        self.assertEqual(records(self.root), [])
        idle = project(self.tmp, name='idle', path='', stage='')
        self.assertEqual(self.rebind(cwd=idle).returncode, 2)
        self.assertIn('--rebind', (Path(__file__).resolve().parents[2] / 'gate/cli/run.cjs').read_text().split("const fs")[0])


if __name__ == '__main__':
    unittest.main()
