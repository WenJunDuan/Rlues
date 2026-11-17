"""S5: bounded session view, status-aware hot ledgers and retention."""
import json
import unittest
from gate_harness import athena, tmpdir
from test_state_cli import v2project, ok, snapshot


class Brief(unittest.TestCase):
    def test_budget_and_categories(self):
        root = v2project(tmpdir(self))
        s = root / '.ai_state'
        (s / 'queue.md').write_text(''.join(f'{i}. ' + '队' * 2000 + '\n' for i in range(20)))
        (s / 'issues.md').write_text(''.join(f'| B-{i:03} | bug | P{i % 2} | ' + '急' * 2000 + ' | x | x | open |\n' for i in range(20)))
        (s / 'HANDOFF.md').write_text('# Handoff\n\n## ' + '新' * 2000 + '\nsecret body\n## old\n')
        before = snapshot(root)
        for n in (1, 5, 10):
            out = ok(self, athena('status', '--brief', '--limit', str(n), cwd=root)).stdout
            self.assertLessEqual(len(out.encode()), 2048)
            for text in ('active: idle', 'queue (first', 'P0 10, P1 10', 'waiting (0)', 'HANDOFF: ##'):
                self.assertIn(text, out)
            self.assertNotIn('secret body', out)
        self.assertEqual(snapshot(root), before)
        self.assertNotEqual(athena('status', '--brief', '--limit', '0', cwd=root).returncode, 0)
        self.assertNotEqual(athena('status', '--brief', '--json', cwd=root).returncode, 0)

    def test_idle_without_optional_files(self):
        root = v2project(tmpdir(self))
        out = ok(self, athena('status', '--brief', cwd=root)).stdout
        self.assertIn('1. r/x', out)
        self.assertIn('HANDOFF: (none)', out)

    def test_active_waiting_and_top_handoff_title(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'active-s', cwd=root))
        s = root / '.ai_state'
        (s / 'sprints/aaa-broken').mkdir()
        (s / 'sprints/paused-s').mkdir()
        (s / 'sprints/paused-s/design.md').write_text('---\nstatus: paused\nresume_when: user ready\n---\n')
        (s / 'HANDOFF.md').write_text('# 交接 · latest\n\n## shipped\nbody\n')
        out = ok(self, athena('status', '--brief', cwd=root)).stdout
        self.assertIn('active: active-s', out)
        self.assertIn('waiting (1)', out)
        self.assertIn('paused-s — user ready', out)
        self.assertIn('HANDOFF: # 交接 · latest', out)
        self.assertNotIn('shipped', out)


class HotLedgers(unittest.TestCase):
    def test_archive_reconciles_and_preserves_unfinished(self):
        from test_gate_advisory import advisories
        root = v2project(tmpdir(self))
        s = root / '.ai_state'
        for name in ('queue.md', 'SPRINTS.md'):
            (s / name).write_text('# Ledger\n\n| id | status | notes |\n|---|---|---|\n' +
                ''.join(f'| old-{i} | done | ' + '归档' * 100 + ' |\n' for i in range(50)) +
                '| paused | paused | must stay |\n| pending | pending | must stay |\n| mystery | unknown | done is mentioned, not status |\n')
        before = json.loads(ok(self, athena('status', '--json', cwd=root)).stdout)['ledgers']
        for name in ('queue.md', 'SPRINTS.md'):
            self.assertIn(name, advisories(root, ['A7'])['A7'])
        original = snapshot(root)
        ok(self, athena('tidy', '--dry-run', cwd=root))
        self.assertEqual(snapshot(root), original)
        out = ok(self, athena('tidy', cwd=root)).stdout
        self.assertIn('counts (total/unfinished) unchanged', out)
        after = json.loads(ok(self, athena('status', '--json', cwd=root)).stdout)['ledgers']
        self.assertEqual(before, after)
        for name in ('queue.md', 'SPRINTS.md'):
            self.assertLessEqual((s / name).stat().st_size, 16384)
            text = (s / name).read_text()
            for state in ('paused', 'pending', 'mystery'):
                self.assertIn(state, text)
            self.assertNotIn('old-0', text)
            self.assertIn('old-0', (s / 'archive/ledgers' / name).read_text())
        self.assertNotIn('A7', advisories(root, ['A7']))
        stable = snapshot(root)
        ok(self, athena('tidy', cwd=root))
        self.assertEqual(snapshot(root), stable)

    def test_unknown_and_pending_content_can_exceed_cap(self):
        root = v2project(tmpdir(self))
        file = root / '.ai_state/queue.md'
        text = '# Queue\n1. pending ' + '活' * 6000 + '\n2. unknown\n'
        file.write_text(text)
        out = ok(self, athena('tidy', cwd=root)).stdout
        self.assertIn('retained above limit', out)
        self.assertEqual(file.read_text(), text)


class Retention(unittest.TestCase):
    def test_subagent_size_rotation_keeps_live_provenance(self):
        root = v2project(tmpdir(self))
        s = root / '.ai_state'
        (s / 'sprints/live').mkdir(parents=True)
        runtime = s / '.runtime'
        runtime.mkdir(exist_ok=True)
        old = json.dumps({'sprint': 'old', 'type': 'generator', 'payload': 'x' * 1100000}) + '\n'
        live = json.dumps({'sprint': 'live', 'type': 'generator'}) + '\n'
        stream = runtime / 'subagents.jsonl'
        stream.write_text(old + live)
        original = snapshot(root)
        ok(self, athena('tidy', '--dry-run', cwd=root))
        self.assertEqual(snapshot(root), original)
        ok(self, athena('tidy', cwd=root))
        self.assertEqual(stream.read_text(), live)
        rotated = list(runtime.glob('subagents-*.jsonl'))
        self.assertEqual(len(rotated), 1)
        self.assertEqual(rotated[0].read_text(), old)
        import os
        os.utime(rotated[0], (1, 1))
        os.utime(stream, (1, 1))
        ok(self, athena('tidy', cwd=root))
        self.assertFalse(rotated[0].exists())
        self.assertTrue(stream.exists())

    def test_a7_exact_byte_boundary(self):
        from test_gate_advisory import advisories
        root = v2project(tmpdir(self))
        for name in ('queue.md', 'SPRINTS.md'):
            p = root / '.ai_state' / name
            p.write_bytes(b'x' * 16384)
        self.assertNotIn('A7', advisories(root, ['A7']))
        for name in ('queue.md', 'SPRINTS.md'):
            p = root / '.ai_state' / name
            p.write_bytes(b'x' * 16385)
        warning = advisories(root, ['A7'])['A7']
        self.assertIn('queue.md', warning)
        self.assertIn('SPRINTS.md', warning)


class LedgerSafety(unittest.TestCase):
    def test_table_boundaries_and_inline_status_examples(self):
        root = v2project(tmpdir(self))
        p = root / '.ai_state/queue.md'
        retained = ('\n| task | notes |\n|---|---|\n| unfinished | done |\n'
                    '\n- pending: query `status: done` from remote\n'
                    '- pending \\| done; status example\n'
                    '\n| task | status |\n|---|---|\n| escaped \\| done | pending |\n')
        p.write_text('| task | status |\n|---|---|\n| old | done |\n' +
                     '| big | shipped | ' + 'x' * 17000 + ' |\n' + retained)
        ok(self, athena('tidy', cwd=root))
        self.assertIn(retained, p.read_text())
        archive = root / '.ai_state/archive/ledgers/queue.md'
        self.assertNotIn('unfinished', archive.read_text())
        self.assertNotIn('query', archive.read_text())

    def test_fences_and_nested_metadata_stay_hot(self):
        root = v2project(tmpdir(self))
        p = root / '.ai_state/queue.md'
        retained = ('    | task | status |\n    |---|---|\n    | unfinished code | done |\n    - [x] code example\n'
                    '- pending fenced table\n  ```md\n\n  | task | status |\n  |---|---|\n  | unfinished example | done |\n  ```\n'
                    '- pending task\n  ```yaml\n  status: done\n  ```\n'
                    '- pending parent\n  child:\n    status: done\n'
                    '\n```md\n| task | status |\n|---|---|\n| unfinished | done |\n```\n'
                    '- [x] parent\n  - [ ] unfinished child\n')
        p.write_text('- finished; status: done\n- [x] old ' + 'x' * 17000 + '\n\n' + retained)
        ok(self, athena('tidy', cwd=root))
        self.assertEqual(p.read_text(), '\n' + retained)
