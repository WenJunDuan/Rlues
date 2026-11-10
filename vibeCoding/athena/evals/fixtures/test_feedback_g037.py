"""G-037: docs evidence only accepted markdown in the source tree, so a research note under
.ai_state/docs/ could not prove an AC. Markdown under .ai_state/docs/ (any depth) now counts;
other .ai_state files and links escaping .ai_state/docs stay unprovable.
"""
import unittest

from gate_harness import GOOD_DESIGN, athena, project, tmpdir
from test_gate_evidence import records


class StateDocs(unittest.TestCase):
    def setUp(self):
        self.root = project(tmpdir(self), design=GOOD_DESIGN)
        research = self.root / '.ai_state/docs/research'
        research.mkdir(parents=True)
        (research / 'note.md').write_text('benchmark verdict\n')

    def last(self, *command):
        run = athena('run', '--covers', 'AC1', '--', *command, cwd=self.root)
        return run, records(self.root)[-1]

    def test_research_note_is_docs_evidence(self):
        for command in (('grep', '-F', '-q', 'benchmark verdict', '.ai_state/docs/research/note.md'),
                        ("grep -Fq 'benchmark verdict' .ai_state/docs/research/*.md",)):
            with self.subTest(command=command):
                run, row = self.last(*command)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual((row['kind'], row['provable'], row['covers']), ('docs', True, ['AC1']))

    def test_missing_text_records_the_failure(self):
        run, row = self.last('grep', '-F', '-q', 'absent', '.ai_state/docs/research/note.md')
        self.assertEqual((run.returncode, row['kind'], row['exit']), (1, 'docs', 1))

    def test_other_state_files_and_escaping_links_stay_unprovable(self):
        (self.root / '.ai_state/notes.md').write_text('benchmark verdict\n')
        (self.root.parent / 'outside.md').write_text('benchmark verdict\n')
        (self.root / '.ai_state/docs/link.md').symlink_to(self.root.parent / 'outside.md')
        for target in ('.ai_state/notes.md', '.ai_state/docs/link.md'):
            with self.subTest(target=target):
                _, row = self.last('grep', '-F', '-q', 'benchmark verdict', target)
                self.assertFalse(row['provable'])


if __name__ == '__main__':
    unittest.main()
