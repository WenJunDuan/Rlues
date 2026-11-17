"""G-014: CC no longer ships rules/_index.md; an upgrade keeps only the user's part of the merged index."""
import json
import unittest

from gate_harness import ENV, athena, tmpdir
from test_install import build

INDEX = '.claude/rules/_index.md'
OLD_PACKAGE = ('# Rules 索引\n\n项目规范（不是命令权限）。\n\n| 文件 | 何时读 |\n|---|---|\n| coding.md | 写/审代码 |\n'
               '| session-workflow.md | 会话开场核对 |\n\n严重度：P0 违反 = REWORK。\n')
CUSTOM = '  | models.md | 用户模型选择 |'
NOTES = '# My notes\n\n  Preserve this paragraph.\n'


def previous_install(home, files):
    state = home / '.athena/installed.json'
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({'files': files, 'backup': '.athena/backups/previous'}))


class RulesIndexRetire(unittest.TestCase):
    def setUp(self):
        self.base = tmpdir(self)
        self.dist = build(self.base / 'dist')

    def install(self, home, platforms='cc'):
        run = athena('install', '--platform', platforms, '--dist', str(self.dist), cwd=home, env={**ENV, 'HOME': str(home)})
        self.assertEqual(run.returncode, 0, run.stderr)
        return run

    def rollback(self, home):
        run = athena('rollback', cwd=home, env={**ENV, 'HOME': str(home)})
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_upgrade_keeps_only_user_rows_and_notes_and_rolls_back(self):
        home = self.base / 'home'
        index = home / INDEX
        index.parent.mkdir(parents=True)
        row = '| session-workflow.md | 会话开场核对 |\n'
        before = OLD_PACKAGE.replace(row, row + CUSTOM + '\n') + '\n' + NOTES
        index.write_text(before)
        previous_install(home, [{'path': INDEX, 'kind': 'cc', 'merged': True, 'package_content': OLD_PACKAGE}])
        run = self.install(home)
        self.assertIn('kept your rows and notes only', run.stderr)
        text = index.read_text()
        self.assertEqual(text, f'| 文件 | 何时读 |\n|---|---|\n{CUSTOM}\n\n{NOTES}')
        self.install(home)
        self.assertEqual(index.read_text(), text, 'second install leaves the user index alone')
        self.rollback(home)
        self.assertEqual(index.read_text(), text)
        self.rollback(home)
        self.assertEqual(index.read_text(), before)

    def test_upgrade_retires_a_package_only_index(self):
        home = self.base / 'home'
        index = home / INDEX
        index.parent.mkdir(parents=True)
        index.write_text(OLD_PACKAGE)
        previous_install(home, [{'path': INDEX, 'kind': 'cc', 'merged': True, 'package_content': OLD_PACKAGE}])
        self.install(home)
        self.assertFalse(index.exists())
        backups = list((home / '.athena/backups').glob(f'*/files/{INDEX}'))
        self.assertEqual([b.read_text() for b in backups], [OLD_PACKAGE])
        self.rollback(home)
        self.assertEqual(index.read_text(), OLD_PACKAGE)

    def test_upgrade_moves_files_no_longer_shipped_into_the_backup(self):
        home = self.base / 'home'
        stale = {'.claude/rules/session-workflow.md': 'cc', '.codex/standards/session-workflow.md': 'cx'}
        for rel in stale:
            (home / rel).parent.mkdir(parents=True, exist_ok=True)
            (home / rel).write_text('# 会话工作流\n')
        previous_install(home, [{'path': rel, 'kind': kind, 'sha256': 'x'} for rel, kind in stale.items()])
        self.install(home, 'cc,cx')
        for rel in stale:
            with self.subTest(rel=rel):
                self.assertFalse((home / rel).exists())
                self.assertEqual(len(list((home / '.athena/backups').glob(f'*/files/{rel}'))), 1)
        self.rollback(home)
        for rel in stale:
            self.assertEqual((home / rel).read_text(), '# 会话工作流\n')

    def test_user_index_without_athena_record_is_left_after_a_10x_install(self):
        home = self.base / 'home'
        index = home / INDEX
        index.parent.mkdir(parents=True)
        index.write_text(NOTES)
        previous_install(home, [])
        self.install(home)
        self.assertEqual(index.read_text(), NOTES)


if __name__ == '__main__':
    unittest.main()
