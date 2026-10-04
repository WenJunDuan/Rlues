"""`athena issue add --type gate` also appends one row to the configured upstream FEEDBACK.md
(athena-10-1-5 S1): env ATHENA_FEEDBACK or `feedback` in ~/.athena/config.json. Best-effort:
no config, a missing file or a write error leave exit 0 and one warning line."""
import datetime
import json
import unittest

from gate_harness import athena, tmpdir
from test_state_cli import v2project

TODAY = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
TABLE = ('# 使用反馈\n\n## proj-a\n\n| 项目账 | 级 | 现象 | 影响 | 当时绕法 | 建议 | 状态 |\n|---|---|---|---|---|---|---|\n'
         '| G-004 | P2 | old | x | y | z | 待修 |\n\n### 环境事实\n\n| 事实 | 影响 |\n|---|---|\n| a | b |\n')


class UpstreamFeedback(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = v2project(self.tmp)
        self.home = self.tmp / 'home'
        (self.home / '.athena').mkdir(parents=True)
        self.feedback = self.tmp / 'up/FEEDBACK.md'
        self.feedback.parent.mkdir()
        self.feedback.write_text(TABLE, encoding='utf-8')

    def add(self, *args, env=None, kind='gate', text='H1 blocks the design write'):
        return athena('issue', 'add', '--type', kind, '--text', text, *args, cwd=self.root, env={'HOME': str(self.home), 'ATHENA_FEEDBACK': None, **(env or {})})  # harness default is off; unset unless the case sets it

    def issues(self):
        return (self.root / '.ai_state/issues.md').read_text(encoding='utf-8')

    def test_env_file_gets_one_row_inside_the_feedback_table(self):
        run = self.add('--sev', 'P2', env={'ATHENA_FEEDBACK': str(self.feedback)})
        self.assertEqual((run.returncode, run.stdout.strip(), run.stderr), (0, 'G-001', ''))
        lines = self.feedback.read_text(encoding='utf-8').split('\n')
        at = lines.index('| G-004 | P2 | old | x | y | z | 待修 |')
        self.assertEqual(lines[at + 1], f'| G-001 | P2 | {TODAY}，proj：H1 blocks the design write | — | — | — | 待修 |')
        self.assertEqual(lines[at + 2:], TABLE.split('\n')[TABLE.split('\n').index('| G-004 | P2 | old | x | y | z | 待修 |') + 1:])
        self.assertIn('| G-001 | gate | P2 | H1 blocks the design write |', self.issues())

    def test_config_json_under_home_and_env_precedence(self):
        (self.home / '.athena/config.json').write_text(json.dumps({'feedback': str(self.feedback)}), encoding='utf-8')
        self.assertEqual(self.add().stderr, '')
        self.assertIn('| G-001 | — |', self.feedback.read_text(encoding='utf-8'))
        other = self.tmp / 'other.md'
        other.write_text('# notes\n', encoding='utf-8')
        self.assertEqual(self.add(env={'ATHENA_FEEDBACK': str(other)}).returncode, 0)
        self.assertNotIn('G-002', self.feedback.read_text(encoding='utf-8'))
        self.assertEqual(other.read_text(encoding='utf-8'),  # no 项目账 table yet → header + row at the end
                         f'# notes\n\n| 项目账 | 级 | 现象 | 影响 | 当时绕法 | 建议 | 状态 |\n|---|---|---|---|---|---|---|\n'
                         f'| G-002 | — | {TODAY}，proj：H1 blocks the design write | — | — | — | 待修 |\n')
        run = self.add(env={'ATHENA_FEEDBACK': ''})  # explicit off: silent, config ignored
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        self.assertNotIn('G-003', self.feedback.read_text(encoding='utf-8'))

    def test_cells_cannot_break_the_table(self):
        self.add(text='a | b\nc', env={'ATHENA_FEEDBACK': str(self.feedback)})
        row = [l for l in self.feedback.read_text(encoding='utf-8').split('\n') if l.startswith('| G-001')][0]
        self.assertEqual(row.count('|'), 8)
        self.assertIn('a / b c', row)

    def test_other_types_stay_local(self):
        run = self.add(kind='bug', env={'ATHENA_FEEDBACK': str(self.feedback)})
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        self.assertEqual(self.feedback.read_text(encoding='utf-8'), TABLE)

    def test_missing_config_file_or_write_error_only_warns(self):
        before = sorted(p.name for p in self.tmp.iterdir())
        cases = (({}, 'no upstream feedback file configured'),
                 ({'ATHENA_FEEDBACK': str(self.tmp / 'absent/FEEDBACK.md')}, 'ENOENT'),
                 ({'ATHENA_FEEDBACK': str(self.feedback.parent)}, 'EISDIR'))
        for n, (env, needle) in enumerate(cases, 1):
            with self.subTest(env=env):
                run = self.add(env=env)
                self.assertEqual((run.returncode, run.stdout.strip()), (0, f'G-00{n}'))
                self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
                self.assertIn(needle, run.stderr)
                self.assertIn(f'G-00{n} is recorded locally', run.stderr)
        (self.home / '.athena/config.json').write_text('{not json', encoding='utf-8')
        self.assertIn('no upstream feedback file configured', self.add().stderr)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), before, 'nothing created outside the configured file')
        self.assertEqual(self.feedback.read_text(encoding='utf-8'), TABLE)
        self.assertEqual(self.issues().count('| gate |'), 4)


if __name__ == '__main__':
    unittest.main()
