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
        ok(self, athena('run', '--', 'npm', '--prefix', str(target), '--version', cwd=self.root))
        self.assertEqual((evidence(self.root, 'links-sprint')[-1]['kind'],
                          evidence(self.root, 'links-sprint')[-1]['provable']), ('other', False))

    def test_target_with_ledger_keeps_its_active_sprint(self):
        target = self.target(name='agent', sprint='agent-sprint')
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        self.assertEqual(evidence(self.root, 'links-sprint'), [])
        self.assertEqual(len(evidence(target, 'agent-sprint')), 1)

    def test_idle_target_with_ledger_does_not_fall_back(self):
        target = self.target(name='agent', path='', stage='', sprint='')
        run = athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root)
        ok(self, run)
        self.assertIn('no active sprint', run.stderr)
        self.assertEqual(evidence(self.root, 'links-sprint'), [])
