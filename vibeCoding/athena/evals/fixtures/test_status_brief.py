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
