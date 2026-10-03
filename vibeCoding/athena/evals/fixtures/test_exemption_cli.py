"""G-004: audited CLI exemptions use the same validation as the hooks."""
from datetime import datetime, timedelta, timezone
import json
import unittest

from gate_harness import GOOD_DESIGN, athena, call, git, project, set_index, tmpdir


def date(days=0):
    return (datetime.now(timezone.utc).date() + timedelta(days=days)).isoformat()


def entries(root):
    run = athena('status', '--json', cwd=root)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)['exemptions']


class ExemptionCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, path='System', design=GOOD_DESIGN)

    def add(self, key='h4_worktree', until=None, reason='VM only; writes evidence'):
        return athena('exemption', 'add', '--key', key, '--until', until or date(3),
                      '--reason', reason, cwd=self.root)

    def test_add_list_remove_and_audit(self):
        index = self.root / '.ai_state/_index.md'
        original = index.read_text()
        run = self.add()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(entries(self.root), [{'key': 'h4_worktree', 'until': date(3),
                                              'status': 'active', 'why': ''}])
        run = athena('exemption', 'list', cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('h4_worktree', run.stdout)
        self.assertIn('[active]', run.stdout)
        self.assertIn('VM only; writes evidence', run.stdout)
        self.assertEqual(athena('exemption', 'remove', '--key', 'h4_worktree', cwd=self.root).returncode, 0)
        self.assertEqual(entries(self.root), [])
        self.assertIn('(no exemptions)', athena('exemption', 'list', cwd=self.root).stdout)
        self.assertIn(original.split('---')[2], index.read_text())
        ledger = (self.root / '.ai_state/issues.md').read_text()
        self.assertIn('exemption add h4_worktree', ledger)
        self.assertIn('exemption remove h4_worktree', ledger)
        self.assertEqual(ledger.count('VM only; writes evidence'), 2)
        self.assertEqual(athena('issue', 'list', cwd=self.root).stdout, '(no matching issues)\n')

    def test_readd_replaces_key_and_preserves_other_fields(self):
        set_index(self.root, exemptions=f'[{{key: skip_polish, until: "{date(2)}", reason: "VM"}}]',
                  flags='{"fixture":true}')
        self.assertEqual(self.add().returncode, 0)
        self.assertEqual(self.add(until=date(5), reason='updated reason').returncode, 0)
        current = entries(self.root)
        self.assertEqual([x['key'] for x in current], ['skip_polish', 'h4_worktree'])
        self.assertEqual(current[1]['until'], date(5))
        self.assertIn('flags: {"fixture":true}', (self.root / '.ai_state/_index.md').read_text())

    def test_invalid_input_does_not_write_state_or_ledger(self):
        index = self.root / '.ai_state/_index.md'
        before = index.read_bytes()
        for kwargs in ({'key': 'h2_evidence'}, {'until': date(15)}, {'until': date(-1)},
                       {'until': 'not-a-date'}, {'until': '2026-02-30'},
                       {'reason': ''}, {'reason': '   '}):
            with self.subTest(kwargs=kwargs):
                run = self.add(**kwargs)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(index.read_bytes(), before)
                self.assertFalse((self.root / '.ai_state/issues.md').exists())
        self.assertEqual(self.add(until=date()).returncode, 0, 'today is inclusive')

    def test_cli_exemption_controls_h4(self):
        for platform in ('cc', 'cx'):
            self.assertTrue(call(platform, 'agent', self.root, type='generator').blocked)
        self.assertEqual(self.add().returncode, 0)
        for platform in ('cc', 'cx'):
            self.assertFalse(call(platform, 'agent', self.root, type='generator').blocked)
        self.assertEqual(athena('exemption', 'remove', '--key', 'h4_worktree', cwd=self.root).returncode, 0)
        self.assertTrue(call('cc', 'agent', self.root, type='generator').blocked)

    def test_all_allowed_keys_and_quoted_reason_round_trip(self):
        reason = 'VM "evidence, only"；不写源码'
        keys = ('h4_worktree', 'skip_runtime_verify', 'skip_polish',
                'skip_architecture_check', 'harness_target_outside_repo')
        for key in keys:
            run = self.add(key=key, until=date(13), reason=reason)
            self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual([x['key'] for x in entries(self.root)], list(keys))
        self.assertEqual(athena('exemption', 'list', cwd=self.root).stdout.count(reason), len(keys))

    def test_expired_entry_is_listed_and_ignored(self):
        set_index(self.root, exemptions=f'[{{key: h4_worktree, until: "{date(-1)}", reason: "VM"}}]')
        run = athena('exemption', 'list', cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('[expired]', run.stdout)
        self.assertTrue(call('cc', 'agent', self.root, type='generator').blocked)

    def test_worktree_writes_main_state_and_stages_tracked_files(self):
        self.assertEqual(self.add().returncode, 0)
        git(self.root, 'add', '.ai_state')
        git(self.root, 'commit', '-qm', 'exemption base')
        wt = self.tmp / 'wt'
        git(self.root, 'worktree', 'add', '-q', str(wt))
        run = athena('exemption', 'remove', '--key', 'h4_worktree', cwd=wt)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(entries(self.root), [])
        self.assertIn('h4_worktree', (wt / '.ai_state/_index.md').read_text())
        staged = git(self.root, 'diff', '--cached', '--name-only').stdout.splitlines()
        self.assertEqual(staged, ['.ai_state/_index.md', '.ai_state/issues.md'])

    def test_usage_and_status_point_to_cli(self):
        self.assertIn('exemption add|list|remove', athena(cwd=self.root).stdout)
        self.assertIn('athena exemption', athena('status', cwd=self.root).stdout)
        for args in (('exemption',), ('exemption', 'remove'), ('exemption', 'add', '--key', 'h4_worktree'),
                     ('exemption', 'remove', '--key', 'unknown'), ('exemption', 'list', '--key', 'h4_worktree')):
            with self.subTest(args=args):
                self.assertEqual(athena(*args, cwd=self.root).returncode, 2)
