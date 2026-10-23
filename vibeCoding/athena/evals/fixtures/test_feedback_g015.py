"""G-015: no-ledger command targets fall back to the caller's active sprint."""
import json
import unittest

from gate_harness import athena, git, project, tmpdir
from test_feedback_ql import evidence
from test_state_cli import ok


class ExternalEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, name='links', sprint='links-sprint')

    def target(self, name='plugins', **kwargs):
        root = project(self.tmp, name=name, **kwargs)
        (root / 'package.json').write_text(json.dumps({'scripts': {'test': 'node --test check.test.cjs'}}))
        (root / 'check.test.cjs').write_text("require('node:test')('external', () => {});\n")
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'external test')
        return root

    def test_no_ledger_target_falls_back_and_records_target(self):
        target = self.target(stage=None)
        run = athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root)
        ok(self, run)
        rows = evidence(self.root, 'links-sprint')
        self.assertEqual(len(rows), 1, run.stderr)
        self.assertEqual((rows[0]['target'], rows[0]['kind'], rows[0]['provable'], rows[0]['covers']),
                         (str(target), 'test', True, ['AC1']))
        self.assertFalse((target / '.ai_state').exists())
        self.assertEqual(rows[0]['target_head'], git(target, 'rev-parse', 'HEAD').stdout.strip())
        self.assertFalse(rows[0]['target_dirty'])
        (target / 'unchanged-dirty.txt').write_text('dirty\n')
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        row = evidence(self.root, 'links-sprint')[-1]
        self.assertEqual((row['target_dirty'], row['provable']), (True, True))
        ok(self, athena('run', '--', 'npm', '--prefix', str(target), '--version', cwd=self.root))
        self.assertEqual((evidence(self.root, 'links-sprint')[-1]['kind'],
                          evidence(self.root, 'links-sprint')[-1]['provable']), ('other', False))

    def test_target_with_ledger_is_the_callers_evidence(self):
        # G-025 supersedes "a ledger target keeps its active sprint".
        target = self.target(name='agent', sprint='agent-sprint')
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        self.assertEqual(len(evidence(self.root, 'links-sprint')), 1)
        self.assertEqual(evidence(target, 'agent-sprint'), [])

    def test_idle_target_with_ledger_falls_back(self):
        target = self.target(name='agent', path='', stage='', sprint='')
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        self.assertEqual(len(evidence(self.root, 'links-sprint')), 1)

    def probe(self, target, body):
        (target / 'check.test.cjs').write_text("require('node:test')('external', () => {" + body + '});\n')
        git(target, 'add', '-A')
        git(target, 'commit', '-qm', 'probe')

    def test_target_head_change_during_run_is_unprovable(self):
        target = self.target(stage=None)
        self.probe(target, "require('child_process').execFileSync('git', ['commit', '--allow-empty', '-qm', 'during'], {cwd: __dirname});")
        before = git(target, 'rev-parse', 'HEAD').stdout.strip()
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        row = evidence(self.root, 'links-sprint')[-1]
        self.assertNotEqual(before, git(target, 'rev-parse', 'HEAD').stdout.strip())
        self.assertEqual((row['provable'], row['reason']), (False, 'tree_changed_during_run'))
        self.assertEqual(row['target_head'], git(target, 'rev-parse', 'HEAD').stdout.strip())
        self.assertFalse(row['target_dirty'])

    def test_target_porcelain_change_during_run_is_unprovable(self):
        for change in ('clean_to_dirty', 'dirty_to_clean', 'dirty_to_dirty'):
            with self.subTest(change=change):
                target = self.target(name=change, stage=None)
                body = "require('fs').unlinkSync('before.txt');" if change == 'dirty_to_clean' else "require('fs').writeFileSync('after.txt', 'changed');"
                self.probe(target, body)
                if change != 'clean_to_dirty':
                    (target / 'before.txt').write_text('before\n')
                ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
                row = evidence(self.root, 'links-sprint')[-1]
                self.assertEqual((row['provable'], row['reason']), (False, 'tree_changed_during_run'))
                self.assertEqual(row['target_dirty'], change != 'dirty_to_clean')

    def test_already_dirty_file_rewritten_during_run_is_unprovable(self):
        target = self.target(stage=None)
        self.probe(target, "require('fs').writeFileSync('app.js', 'after dirty rewrite\\n');")
        (target / 'app.js').write_text('before dirty rewrite\n')
        before = git(target, 'status', '--porcelain').stdout
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        self.assertEqual(git(target, 'status', '--porcelain').stdout, before)
        row = evidence(self.root, 'links-sprint')[-1]
        self.assertEqual((row['provable'], row['reason']), (False, 'tree_changed_during_run'))

    def test_subdirectory_run_detects_dirty_rewrite_outside_subdirectory(self):
        target = self.target(stage=None)
        subdir = target / 'tests'
        subdir.mkdir()
        (subdir / 'check.test.cjs').write_text("require('node:test')('external', () => { require('fs').writeFileSync('../app.js', 'after dirty rewrite\\n'); });\n")
        git(target, 'add', '-A')
        git(target, 'commit', '-qm', 'subdirectory probe')
        (target / 'app.js').write_text('before dirty rewrite\n')
        before = git(target, 'status', '--porcelain').stdout
        ok(self, athena('run', '--', f'cd {subdir} && node --test check.test.cjs', cwd=self.root))
        self.assertEqual(git(target, 'status', '--porcelain').stdout, before)
        row = evidence(self.root, 'links-sprint')[-1]
        self.assertEqual((row['provable'], row['reason']), (False, 'tree_changed_during_run'))

    def test_non_git_target_is_unprovable(self):
        target = self.tmp / 'plain'
        target.mkdir()
        (target / 'check.test.cjs').write_text("require('node:test')('plain', () => {});\n")
        ok(self, athena('run', '--', f'cd {target} && node --test check.test.cjs', cwd=self.root))
        row = evidence(self.root, 'links-sprint')[-1]
        self.assertEqual((row['target_tree'], row['target_head'], row['target_dirty'], row['provable']),
                         (None, None, None, False))
        self.assertEqual(row['reason'], 'target_tree_unknown')
