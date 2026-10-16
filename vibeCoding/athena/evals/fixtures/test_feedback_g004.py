"""G-004: cherry-pick ownership uses integration time, never author time."""
import subprocess
import unittest

from gate_harness import ENV, athena, git, tmpdir
from test_feedback_g003 import commit_at, packet
from test_state_cli import ok, v2project


class CherryPickCommitterDate(unittest.TestCase):
    def test_resumed_cherry_pick_keeps_rework_with_paused_author_date(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        base = git(root, 'rev-parse', 'HEAD').stdout.strip()
        git(root, 'checkout', '-qb', 'writer')
        writer = commit_at(root, 'rework.js', '2026-10-01T10:00:00Z', '2026-10-01T10:00:00Z')
        git(root, 'checkout', '-q', '-')
        other = commit_at(root, 'other.js', '2026-09-30T08:00:00Z', '2026-10-01T10:30:00Z')
        run = subprocess.run(['git', '-C', str(root), 'cherry-pick', writer],
                             env={**ENV, 'GIT_COMMITTER_DATE': '2026-10-01T12:00:00Z'},
                             text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        picked = git(root, 'rev-parse', 'HEAD').stdout.strip()
        # Timestamp boundaries take precedence even if recorded HEAD boundaries are stale.
        (root / '.ai_state/sprints/s-x/log.md').write_text(
            f'- 2026-10-01T09:00:00.000Z paused at impl (head {base})\n'
            f'- 2026-10-01T11:00:00.000Z resumed at impl (head {picked})\n')
        text, changes = packet(self, root)
        excluded = text.split('## Excluded commits')[1].split('## Acceptance')[0]
        self.assertIn(other, excluded)
        self.assertNotIn(picked, excluded)
        self.assertIn('rework.js', changes)
        self.assertNotIn('other.js', changes)

    def test_pause_resume_log_precise_timestamps(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        ok(self, athena('sprint', 'pause', '--resume-when', 'ready', cwd=root))
        ok(self, athena('sprint', 'resume', 's-x', cwd=root))
        text = (root / '.ai_state/sprints/s-x/log.md').read_text()
        for action in ('paused', 'resumed'):
            self.assertRegex(text, rf'- \d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}\.\d{{3}}Z {action} at ')
