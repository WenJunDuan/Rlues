"""G-018: H1 blocked the sprint's own design.md written from a worktree nested in the main repo.

`<main>/.claude/worktrees/w1/.ai_state/…` is inside mainRoot but not inside `<main>/.ai_state`,
so it counted as an implementation write (athena-10-1-5 S1 AC1).
"""
import unittest

from gate_harness import PLATFORMS, athena, call, git, tmpdir
from test_state_cli import ok, v2project

SLUG = 't'


def nested(testcase, where='.claude/worktrees/w1'):
    """v2 project with sprint `t` in design (template only, no AC line) + a worktree nested under it."""
    root = v2project(tmpdir(testcase))
    ok(testcase, athena('sprint', 'start', 'r/x', '--slug', SLUG, cwd=root))
    wt = root / where
    git(root, 'worktree', 'add', '-q', str(wt), '-b', 'w1')
    return root, wt


class NestedWorktreeState(unittest.TestCase):
    def test_design_in_nested_worktree_state_is_not_implementation(self):
        root, wt = nested(self)
        design = wt / f'.ai_state/sprints/{SLUG}/design.md'
        for platform in PLATFORMS:
            for cwd in (wt, root):  # the writer inside the worktree, and the main agent addressing it
                with self.subTest(platform=platform, cwd=cwd.name):
                    verdict = call(platform, 'write', cwd, file=design)
                    self.assertFalse(verdict.blocked, verdict.reason)

    def test_main_checkout_design_still_allowed(self):
        root, wt = nested(self)
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertFalse(call(platform, 'write', wt, file=root / f'.ai_state/sprints/{SLUG}/design.md').blocked)

    def test_source_in_nested_worktree_still_needs_acceptance(self):
        root, wt = nested(self)
        for platform in PLATFORMS:
            for target in (wt / 'app.js', wt / 'src/.ai_state.js', wt / 'pkg/.ai_state/x.js', root / 'app.js'):
                with self.subTest(platform=platform, target=str(target.relative_to(root))):
                    verdict = call(platform, 'write', wt, file=target)
                    self.assertTrue(verdict.blocked, target)
                    self.assertIn('H1', verdict.reason)

    def test_unregistered_nested_directory_state_is_implementation(self):
        # Only a root git knows as a worktree owns a .ai_state; a plain directory named so does not.
        root, wt = nested(self)
        fake = root / '.claude/worktrees/ghost/.ai_state/sprints/t/design.md'
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertTrue(call(platform, 'write', root, file=fake).blocked)

    def test_acceptance_line_unblocks_worktree_source(self):
        root, wt = nested(self)
        design = root / f'.ai_state/sprints/{SLUG}/design.md'
        design.write_text(design.read_text(encoding='utf-8') + '\n- AC1: add returns 2\n', encoding='utf-8')
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertFalse(call(platform, 'write', wt, file=wt / 'app.js').blocked)


if __name__ == '__main__':
    unittest.main()
