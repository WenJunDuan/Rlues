"""G-021 (quantum-agent): Quick ship passed while AC1's `--covers` evidence had exited 1.

Any other provable PASS on the tree satisfied H2, so a failing AC check was only an advisory.
The latest `--covers` record per AC on the current tree now has to pass.
"""
import unittest

from gate_harness import GOOD_DESIGN, athena, call, check_file, green, project, set_index, tmpdir


class FailedCoverBlocksShip(unittest.TestCase):
    def setUp(self):
        self.root = project(tmpdir(self), path='Quick', stage='impl', design=GOOD_DESIGN)
        set_index(self.root, stage='ship')

    def covers(self, passing):
        return athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(self.root, passing=passing), cwd=self.root)

    def test_failed_cover_refuses_even_with_another_pass(self):
        self.assertEqual(self.covers(False).returncode, 1)
        self.assertEqual(green(self.root).returncode, 0)
        verdict = call('cc', 'stop', self.root, session='s')
        self.assertTrue(verdict.blocked)
        self.assertIn('AC1', verdict.reason)
        ship = athena('ship', '--dry-run', cwd=self.root)
        self.assertEqual(ship.returncode, 1, ship.stdout)
        self.assertIn('AC1', ship.stderr)

    def test_later_passing_cover_clears_it(self):
        self.assertEqual(self.covers(False).returncode, 1)
        self.assertEqual(self.covers(True).returncode, 0)
        self.assertFalse(call('cc', 'stop', self.root, session='s').blocked)
        self.assertEqual(athena('ship', '--dry-run', cwd=self.root).returncode, 0)


if __name__ == '__main__':
    unittest.main()
