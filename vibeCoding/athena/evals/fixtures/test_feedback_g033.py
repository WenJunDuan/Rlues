"""G-033: a review packet listed an older, unrelated commit (palette-calibrate packet → recap commit).

The sprint was paused right after start; while paused, other sprints shipped (left the hot layer) and
their commits had unknown ownership, so G-024 kept them in Changes. While a sprint has nothing of its
own yet, only commits naming it stay from that paused interval. Changes after a --no-ff merge are
base → current tree.
"""
import re
import unittest

from gate_harness import athena, git, tmpdir
from test_feedback_g024 import branch_merge, commit
from test_state_cli import ok, v2project


def changes(packet):
    return packet.split('## Changes (base → current tree)')[1].split('## Evidence')[0]


def prepare(testcase, root):
    prep = ok(testcase, athena('review', 'prepare', cwd=root)).stdout
    run = re.search(r'^run (\S+)', prep, re.M).group(1)
    return (root / f'.ai_state/.runtime/review/{run}/packet.md').read_text()


class MergeBase(unittest.TestCase):
    def test_no_ff_merge_lists_base_to_tree(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        base = git(root, 'rev-parse', '--short', 'HEAD').stdout.strip()
        commit(root, 'main.js', 'feat(s-x): main side')
        branch_merge(root, 'feat/s-x', 'side.js', 'feat(s-x): branch side')
        (root / 'wip.js').write_text('uncommitted\n')
        packet = prepare(self, root)
        self.assertIn(f'(base {base})', packet)
        self.assertNotIn('Excluded commits', packet)
        listed = changes(packet)
        for name in ('main.js', 'side.js', 'wip.js'):
            self.assertIn(name, listed)
        self.assertNotIn('app.js', listed)


class PausedBeforeOwnWork(unittest.TestCase):
    def test_foreign_interval_commits_leave_changes(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=root))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=root))
        foreign = commit(root, 'recap.js', 'feat(recap): other work')
        _, named = branch_merge(root, 'writer-x', 'early.js', 'feat(s-x): early writer part')
        ok(self, athena('sprint', 'drop', 's-y', '--reason', 'shipped elsewhere', cwd=root))
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'chore(state): close y')
        ok(self, athena('sprint', 'resume', 's-x', cwd=root))
        branch_merge(root, 'feat/s-x', 'own.js', 'feat: palette')
        packet = prepare(self, root)
        excluded = packet.split('## Acceptance')[0]
        self.assertIn(foreign, excluded)
        self.assertNotIn(named, excluded)
        listed = changes(packet)
        for name in ('own.js', 'early.js'):
            self.assertIn(name, listed)
        self.assertNotIn('recap.js', listed)


if __name__ == '__main__':
    unittest.main()
