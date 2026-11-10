"""G-031: `sprint resume X` failed while another sprint was active, and the `sprint drop` typed next
dropped the active sprint. resume names the active sprint and the next step; drop takes an explicit
slug and refuses one that is not the active sprint.
"""
import unittest

from gate_harness import athena, tmpdir
from test_state_cli import fm, ok, v2project


class ResumeThenDrop(unittest.TestCase):
    def setUp(self):
        self.root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=self.root))
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=self.root))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=self.root))

    def test_resume_while_another_is_active_names_it_and_the_next_step(self):
        run = athena('sprint', 'resume', 's-x', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('sprint s-y is in flight', run.stderr)
        self.assertIn('next: athena sprint pause', run.stderr)
        self.assertIn('athena sprint resume s-x', run.stderr)
        self.assertEqual(fm(self.root / '.ai_state/_index.md')['sprint'], 's-y')

    def test_drop_without_slug_is_refused(self):
        run = athena('sprint', 'drop', '--reason', 'oops', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('drop <slug>', run.stderr)
        self.assertTrue((self.root / '.ai_state/sprints/s-y').is_dir())

    def test_drop_of_a_non_active_slug_is_refused(self):
        run = athena('sprint', 'drop', 's-x', '--reason', 'meant the paused one', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('s-x is not the active sprint (active: s-y)', run.stderr)
        for slug in ('s-x', 's-y'):
            self.assertTrue((self.root / f'.ai_state/sprints/{slug}').is_dir(), slug)
        self.assertEqual(fm(self.root / '.ai_state/_index.md')['sprint'], 's-y')

    def test_drop_of_the_active_slug_archives_it(self):
        ok(self, athena('sprint', 'drop', 's-y', '--reason', 'superseded', cwd=self.root))
        self.assertFalse((self.root / '.ai_state/sprints/s-y').exists())
        self.assertTrue((self.root / '.ai_state/sprints/s-x').is_dir())

    def test_usage_shows_the_slug(self):
        self.assertIn('athena sprint drop <slug> --reason', athena('sprint', cwd=self.root).stderr)


if __name__ == '__main__':
    unittest.main()
