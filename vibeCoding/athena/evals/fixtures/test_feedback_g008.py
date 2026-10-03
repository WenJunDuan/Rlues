import unittest
from gate_harness import athena, project, tmpdir, GOOD_DESIGN
from test_gate_evidence import records

class DocsAssertions(unittest.TestCase):
    def test_fixed_markdown_assertion_records_exit(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        (root / 'docs').mkdir(); (root / 'docs/guide.md').write_text('required paragraph\n')
        for pattern, code in (('required paragraph', 0), ('absent', 1)):
            run = athena('run', '--', f"grep -Fl '{pattern}' docs/*.md", cwd=root)
            self.assertEqual(run.returncode, code)
            row = records(root)[-1]
            self.assertEqual((row['kind'], row['provable'], row['exit']), ('docs', True, code))

    def test_other_and_outside_targets_remain_unprovable(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        (root / 'guide.md').write_text('word\n'); (root.parent / 'outside.md').write_text('word\n')
        (root / 'link.md').symlink_to(root.parent / 'outside.md')
        for command in ("grep -F word ../outside.md", "grep -F word link.md", "grep -F word app.js", "grep -E 'w.*' guide.md", "grep -F word guide.md; true", "echo word"):
            athena('run', '--', command, cwd=root)
            self.assertFalse(records(root)[-1]['provable'], command)

    def test_ignored_symlink_target_cannot_prove_docs(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        (root / 'ignored').mkdir(); (root / 'ignored/guide.md').write_text('word\n')
        (root / '.gitignore').write_text('ignored/\n')
        (root / 'link.md').symlink_to(root / 'ignored/guide.md')
        run = athena('run', '--', 'grep', '-F', 'word', 'link.md', cwd=root)
        self.assertEqual(run.returncode, 0)
        self.assertFalse(records(root)[-1]['provable'])
