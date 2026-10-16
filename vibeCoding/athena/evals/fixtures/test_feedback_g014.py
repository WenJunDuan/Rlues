"""G-014: install merges user rules index rows in a temporary HOME."""
import json
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

    def test_upgrade_uses_only_proven_package_rows_and_keeps_same_header_user_rows(self):
        tmp = tmpdir(self)
        dist = build(tmp / 'dist')
        proposed = (dist / f'claude/{RELEASE}/.claude/rules/_index.md').read_text()
        previous = '| 文件 | 何时读 |\n|---|---|\n| retired.md | old package row |\n'
        custom = '  | models.md | 用户模型选择 |'
        current = previous + custom + '\n\n| 项目 | 描述 |\n|---|---|\n| unrelated.md | other table |\n'
        for source in ('package_content', 'backup'):
            with self.subTest(source=source):
                home = tmp / source
                index = home / '.claude/rules/_index.md'
                index.parent.mkdir(parents=True)
                index.write_text(current)
                state = home / '.athena/installed.json'
                state.parent.mkdir()
                entry = {'path': '.claude/rules/_index.md'}
                if source == 'package_content':
                    entry['package_content'] = previous
                else:
                    backup = home / '.athena/backups/previous/files/.claude/rules/_index.md'
                    backup.parent.mkdir(parents=True)
                    backup.write_text(previous + custom + '\n')
                state.write_text(json.dumps({'files': [entry], 'backup': '.athena/backups/previous'}))
                for _ in range(2):
                    run = athena('install', '--platform', 'cc', '--dist', str(dist),
                                 cwd=home, env={**ENV, 'HOME': str(home)})
                    self.assertEqual(run.returncode, 0, run.stderr)
                    text = index.read_text()
                    if source == 'package_content':
                        self.assertNotIn('retired.md', text)
                    else:
                        self.assertIn('retired.md', text)  # Unknown ownership in an old user backup.
                    self.assertIn('| 项目 | 描述 |\n|---|---|\n| unrelated.md | other table |\n', text)
                    self.assertEqual(text.count(custom), 1)
                    entry = next(f for f in json.loads(state.read_text())['files']
                                 if f['path'] == '.claude/rules/_index.md')
                    self.assertEqual(entry['package_content'], proposed)

    def test_install_preserves_other_content_and_mismatched_table(self):
        tmp = tmpdir(self)
        dist = build(tmp / 'dist')
        proposed = (dist / f'claude/{RELEASE}/.claude/rules/_index.md').read_text()
        for same_header in (True, False):
            with self.subTest(same_header=same_header):
                home = tmp / str(same_header)
                index = home / '.claude/rules/_index.md'
                index.parent.mkdir(parents=True)
                user = '# My notes\n\n  Preserve this paragraph.\n\n| 项目 | 描述 |\n|---|---|\n| unrelated.md | other table |\n'
                index.write_text((proposed if same_header else '') + '\n' + user)
                for _ in range(2):
                    ok = athena('install', '--platform', 'cc', '--dist', str(dist),
                                cwd=home, env={**ENV, 'HOME': str(home)})
                    self.assertEqual(ok.returncode, 0, ok.stderr)
                    text = index.read_text()
                    self.assertIn(user, text)
                    self.assertEqual(text.count('# My notes'), 1)
                    self.assertTrue(text.startswith(proposed))
