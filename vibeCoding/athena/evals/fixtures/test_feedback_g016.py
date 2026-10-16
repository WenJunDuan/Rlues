"""G-016: external-only changes can supply H2 evidence through a no-ledger target."""
import unittest

from gate_harness import athena, git, project, tmpdir
from test_feedback_ql import evidence
from test_review_cli import accept
from test_state_cli import ok, v2project


class ExternalOnlyShip(unittest.TestCase):
    def test_external_only_change_can_pass_h2_and_ship(self):
        tmp = tmpdir(self)
        root = v2project(tmp)
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'external-only', cwd=root))
        design = root / '.ai_state/sprints/external-only/design.md'
        design.write_text(design.read_text() + '\n- AC1: external test passes\n')
        target = project(tmp, name='plugins', stage=None)
        (target / 'check.test.cjs').write_text("require('node:test')('external', () => {});\n")
        source_before = git(root, 'diff', '--', 'app.js').stdout
        run = athena('run', '--covers', 'AC1', '--', f'cd {target} && node --test check.test.cjs', cwd=root)
        ok(self, run)
        self.assertEqual(len(evidence(root, 'external-only')), 1, run.stderr)
        row = evidence(root, 'external-only')[0]
        self.assertEqual((row['target'], row['provable']), (str(target), True))
        self.assertEqual(git(root, 'diff', '--', 'app.js').stdout, source_before)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, 'VERDICT: PASS\n'))
        ok(self, athena('ship', cwd=root))
