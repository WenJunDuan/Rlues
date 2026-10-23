"""G-019: review accept refused a findings-free `VERDICT: PASS` because another run had accepted the same text.

A PASS without findings is the same bytes every time; given with --file written after this run's
packet it is not a replay. Outputs with findings, or a findings-free PASS on stdin, keep the guard.
"""
import subprocess
import unittest

from gate_harness import CLI, ENV, athena, check_file, tmpdir
from test_review_cli import accept, ready
from test_state_cli import ok, v2project

EMPTY_PASS = 'VERDICT: PASS\n'


def second_run(testcase):
    root = v2project(tmpdir(testcase))
    ready(testcase, root)
    ok(testcase, athena('review', 'prepare', cwd=root))
    ok(testcase, accept(root, EMPTY_PASS))
    (root / 'app.js').write_text('module.exports = 2; // rework\n', encoding='utf-8')
    ok(testcase, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
    ok(testcase, athena('review', 'prepare', cwd=root))
    return root


class FindingsFreePass(unittest.TestCase):
    def test_same_empty_pass_for_new_run_via_file_is_accepted(self):
        root = second_run(self)
        ok(self, accept(root, EMPTY_PASS))

    def test_empty_pass_on_stdin_is_still_a_replay(self):
        root = second_run(self)
        run = subprocess.run(['node', str(CLI), 'review', 'accept', '--run', 'latest'], input=EMPTY_PASS,
                             capture_output=True, text=True, cwd=str(root), env=ENV)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertIn('already accepted', run.stderr)

    def test_output_with_findings_is_still_a_replay(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        out = '- [P3] app.js:1 — naming nit\nVERDICT: PASS\n'
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, out))
        (root / 'app.js').write_text('module.exports = 2; // rework\n', encoding='utf-8')
        ok(self, athena('review', 'prepare', cwd=root))
        replay = accept(root, out)
        self.assertEqual(replay.returncode, 2)
        self.assertIn('already accepted', replay.stderr)


if __name__ == '__main__':
    unittest.main()
