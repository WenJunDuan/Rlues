"""G-021 / G-024: review prepare excluded the sprint's own commits made while it was paused.

Writers commit in their own worktree during the pause and the main agent merges around resume; the
packet listed all of it under "Excluded commits" and Changes came out empty. Only commits attributable
to another sprint (message / merged branch naming its slug, or touching only its state) are excluded.
"""
import re
import unittest

from gate_harness import athena, git, tmpdir
from test_state_cli import ok, v2project


def head(root):
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def commit(root, name, message):
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(f'{name}\n', encoding='utf-8')
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', message)
    return head(root)


def branch_merge(root, branch, name, message):
    wt = root.parent / f'wt-{branch.replace("/", "-")}'
    git(root, 'worktree', 'add', '-q', str(wt), '-b', branch)
    side = commit(wt, name, message)
    git(root, 'merge', '--no-ff', '-q', '-m', f"Merge branch '{branch}'", branch)
    return side, head(root)


class PausedOwnCommits(unittest.TestCase):
    def packet(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        commit(root, 'own.js', 'implement x')
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=root))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=root))
        self.other = commit(root, 'other.js', 'feat(s-y): other slice')
        self.state = commit(root, '.ai_state/sprints/s-y/notes.md', 'notes')
        _, self.own_merge = branch_merge(root, 'writer-1', 'writer.js', 'add writer change')
        _, self.other_merge = branch_merge(root, 'feat/s-y-part', 'part.js', 'add part')
        self.plain = commit(root, 'util.js', 'tidy util')
        ok(self, athena('sprint', 'pause', '--resume-when', 'after x', cwd=root))
        ok(self, athena('sprint', 'resume', 's-x', cwd=root))
        prep = ok(self, athena('review', 'prepare', cwd=root)).stdout
        run = re.search(r'^run (\S+)', prep, re.M).group(1)
        return (root / f'.ai_state/.runtime/review/{run}/packet.md').read_text()

    def test_own_and_unknown_commits_stay_in_changes(self):
        packet = self.packet()
        changes = packet.split('## Changes (base → current tree)')[1].split('## Evidence')[0]
        for name in ('own.js', 'writer.js', 'util.js'):
            self.assertIn(name, changes)
        for name in ('other.js', 'part.js'):
            self.assertNotIn(name, changes)

    def test_only_other_sprint_commits_are_listed_excluded(self):
        packet = self.packet()
        excluded = packet.split('## Acceptance')[0]
        for sha in (self.other, self.state, self.other_merge):
            self.assertIn(sha, excluded)
        for sha in (self.own_merge, self.plain):
            self.assertNotIn(sha, excluded)


if __name__ == '__main__':
    unittest.main()
