"""athena-10-1 S5: `athena init` creates v2 state and never overwrites existing state."""
import unittest

from gate_harness import athena, git, project, tmpdir


class Init(unittest.TestCase):
    def test_fresh_repo_gets_v2_state(self):
        root = tmpdir(self) / 'fresh'
        root.mkdir()
        git(root, 'init', '-q')
        (root / 'sub').mkdir()
        dry = athena('init', '--dry-run', cwd=root / 'sub')
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse((root / '.ai_state').exists())
        run = athena('init', cwd=root / 'sub')
        self.assertEqual(run.returncode, 0, run.stderr)
        index = (root / '.ai_state/_index.md').read_text()
        self.assertIn('schema: athena-state/2', index)
        for name in ('issues.md', 'queue.md', 'sprints', 'roadmap', 'archive'):
            self.assertTrue((root / '.ai_state' / name).exists(), name)
        self.assertIn('.ai_state/.runtime/', (root / '.gitignore').read_text().splitlines())
        self.assertEqual(athena('status', cwd=root).returncode, 0)
        again = athena('init', cwd=root)
        self.assertEqual(again.returncode, 1)
        self.assertIn('already initialised', again.stderr)
        self.assertEqual((root / '.ai_state/_index.md').read_text(), index)

    def test_v1_state_points_to_migrate(self):
        root = tmpdir(self) / 'old'
        root.mkdir()
        git(root, 'init', '-q')
        (root / '.ai_state').mkdir()
        (root / '.ai_state/_index.md').write_text('---\nversion: "9.9.9"\n---\n')
        run = athena('init', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('migrate --to 10.1', run.stderr)

    def test_outside_git_and_in_linked_worktree_refuse(self):
        plain = tmpdir(self) / 'plain'
        plain.mkdir()
        self.assertIn('git', athena('init', cwd=plain).stderr)
        root = project(tmpdir(self))
        wt = root.parent / 'wt'
        git(root, 'worktree', 'add', '-q', str(wt), '-b', 'wt')
        run = athena('init', cwd=wt)
        self.assertEqual(run.returncode, 1)
        self.assertIn('linked worktree', run.stderr)


if __name__ == '__main__':
    unittest.main()
