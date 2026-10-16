"""G-003: late-integrated commits from a paused sprint must stay out of Changes."""
import re
import subprocess
import unittest

from gate_harness import ENV, athena, git, tmpdir
from test_state_cli import ok, v2project


def commit_at(root, filename, author, committer):
    (root / filename).write_text(filename + '\n')
    git(root, 'add', filename)
    run = subprocess.run(['git', '-C', str(root), 'commit', '-qm', filename],
                         env={**ENV, 'GIT_AUTHOR_DATE': author, 'GIT_COMMITTER_DATE': committer},
                         text=True, capture_output=True)
    if run.returncode:
        raise AssertionError(run.stderr)
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def packet(test, root):
    prep = ok(test, athena('review', 'prepare', cwd=root)).stdout
    run = re.search(r'^run (\S+)', prep, re.M).group(1)
    text = (root / f'.ai_state/.runtime/review/{run}/packet.md').read_text()
    changes = text.split('## Changes (base → current tree)')[1].split('## Evidence')[0]
    return text, changes


class PausedCommitterDate(unittest.TestCase):
    def test_late_integrated_paused_commits_are_excluded_by_committer_date(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        own = commit_at(root, 'own.js', '2026-10-01T08:00:00Z', '2026-10-01T08:00:00Z')
        # Resume HEAD did not contain the other slice yet; its author date predates the pause.
        log = root / '.ai_state/sprints/s-x/log.md'
        log.write_text(f'- 2026-10-01T09:00:00.000Z paused at impl (head {own})\n'
                       f'- 2026-10-01T11:00:00.000Z resumed at impl (head {own})\n')
        other = commit_at(root, 'other.js', '2026-09-30T08:00:00Z', '2026-10-01T10:00:00Z')
        commit_at(root, 'own2.js', '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')
        (root / 'pending.js').write_text('pending\n')
        text, changes = packet(self, root)
        self.assertIn(other, text)
        self.assertNotIn('other.js', changes)
        for name in ('own.js', 'own2.js', 'pending.js'):
            self.assertIn(name, changes)

    def test_merge_does_not_reintroduce_excluded_side_commits(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        own = commit_at(root, 'own.js', '2026-10-01T08:00:00Z', '2026-10-01T08:00:00Z')
        git(root, 'checkout', '-qb', 'side')
        other = commit_at(root, 'other.js', '2026-09-30T08:00:00Z', '2026-10-01T10:00:00Z')
        commit_at(root, 'kept.js', '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')
        git(root, 'checkout', '-q', '-')
        commit_at(root, 'own2.js', '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')
        git(root, 'merge', '--no-ff', '--no-commit', 'side')
        commit_at(root, 'merge-note.js', '2026-10-01T12:30:00Z', '2026-10-01T12:30:00Z')
        (root / '.ai_state/sprints/s-x/log.md').write_text(
            f'- 2026-10-01T09:00:00.000Z paused at impl (head {own})\n'
            f'- 2026-10-01T11:00:00.000Z resumed at impl (head {own})\n')
        text, changes = packet(self, root)
        self.assertIn(other, text)
        self.assertNotIn('other.js', changes)
        for name in ('own.js', 'own2.js', 'kept.js', 'merge-note.js'):
            self.assertIn(name, changes)
