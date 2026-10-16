"""G-014: install merges user rules index rows in a temporary HOME."""
import unittest

from gate_harness import ENV, RELEASE, athena, tmpdir
from test_install import build


class RulesIndexMerge(unittest.TestCase):
    def test_install_preserves_user_rows_updates_package_rows_and_rolls_back(self):
        tmp = tmpdir(self)
        dist = build(tmp / 'dist')
        home = tmp / 'home'
        index = home / '.claude/rules/_index.md'
        index.parent.mkdir(parents=True)
        custom = '  | models.md | 用户模型选择 |'
        before = '# Old rules\n\n| 文件 | 何时读 |\n|---|---|\n| coding.md | stale |\n' + custom + '\n'
        index.write_text(before)
        env = {**ENV, 'HOME': str(home)}
        proposed = (dist / f'claude/{RELEASE}/.claude/rules/_index.md').read_text()
        for _ in range(2):
            run = athena('install', '--platform', 'cc', '--dist', str(dist), cwd=home, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
            text = index.read_text()
            self.assertEqual(text.count(custom), 1)
            self.assertNotIn('stale', text)
            for line in proposed.splitlines():
                if line.startswith('|'):
                    self.assertIn(line, text)
        # First rollback restores the merged index; second restores the original user index.
        for expected in (text, before):
            run = athena('rollback', cwd=home, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(index.read_text(), expected)
