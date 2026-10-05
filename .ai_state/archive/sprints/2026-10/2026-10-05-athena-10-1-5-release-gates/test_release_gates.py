"""Verify retained native Mac install/P8/rollback artifacts and live preservation checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

STATE = next(p for p in Path(__file__).resolve().parents if p.name == '.ai_state')
RUN = STATE / '.runtime/release-10-1-5'
USER_ROOT = Path('/Users/mi_manchi')
CLI = USER_ROOT / '.athena/bin/athena'


def read_json(path):
    return json.loads(path.read_text())


class ReleaseGates(unittest.TestCase):
    def test_actual_candidate_install_and_doctor(self):
        for folder in (RUN, RUN / 'round2'):
            with self.subTest(round=folder.name):
                transaction = read_json(folder / 'install-transaction.json')
                self.assertEqual(transaction['version'], '10.1.5')
                self.assertEqual(transaction['platforms'], ['cc', 'cx'])
                self.assertIn('athena 10.1.5', (folder / 'install.stdout').read_text())
                self.assertIn('doctor: no drift', (folder / 'doctor-installed.stdout').read_text())
                self.assertTrue((USER_ROOT / transaction['backup'] / 'backup.json').is_file())

    def test_native_quick_ship_and_structured_hook_output(self):
        for folder in (RUN, RUN / 'round2'):
            with self.subTest(round=folder.name):
                execution = read_json(folder / 'p8-execution.json')
                self.assertEqual(execution['exit_code'], 0)
                self.assertEqual(execution['rollback_exit'], 0)
                rows = [json.loads(line) for line in (folder / 'p8-stream.jsonl').read_text().splitlines()]
                result = next(row for row in rows if row.get('type') == 'result')
                self.assertEqual(result['subtype'], 'success')
                self.assertFalse(result['is_error'])
                hooks = [row for row in rows if row.get('subtype') == 'hook_response']
                for event in ('SessionStart', 'PreToolUse', 'PostToolUse', 'Stop'):
                    self.assertTrue(any(row['hook_event'] == event for row in hooks), event)
                for hook in hooks:
                    self.assertEqual((hook['exit_code'], hook['outcome']), (0, 'success'), hook)
                history = list((USER_ROOT / '.claude/projects').glob(f"*/{result['session_id']}.jsonl"))
                self.assertEqual(len(history), 1, 'native Claude session remains persisted')
                if folder.name == 'round2':
                    contexts = [json.loads(row['stdout']) for row in hooks
                                if row['hook_event'] == 'SessionStart' and row.get('stdout', '').strip()]
                    self.assertTrue(any('p8-json' in row.get('hookSpecificOutput', {}).get('additionalContext', '')
                                        for row in contexts), 'real nonempty JSON hook response was accepted')
        project = RUN / 'p8-project'
        for slug in ('2026-10-05-p8-installer', '2026-10-05-p8-json'):
            evidence = project / '.ai_state/archive/sprints/2026-10' / slug / 'evidence.yaml'
            self.assertIn('exit: 0', evidence.read_text())
            self.assertIn('node --test add.test.cjs', evidence.read_text())
        status = subprocess.run([str(CLI), 'status', '--json'], cwd=project, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(status.stdout)['route']['sprint'], '')

    def test_rollback_restores_current_baseline_and_retains_original_settings(self):
        before = read_json(RUN / 'round2/install-before.json')
        for row in before['files']:
            target = USER_ROOT / row['path']
            with self.subTest(path=row['path']):
                if row.get('missing'):
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row['sha256'])
                    self.assertEqual(target.stat().st_mode & 0o777, row['mode'])
        self.assertEqual((USER_ROOT / '.athena/current').readlink().as_posix(), before['current'])
        self.assertEqual(read_json(USER_ROOT / '.athena/installed.json')['version'], '10.1.0')
        doctor = subprocess.run([str(CLI), 'doctor'], text=True, capture_output=True, check=True)
        self.assertIn('doctor: no drift', doctor.stdout)
        first = read_json(RUN / 'install-before.json')
        expected = next(row['sha256'] for row in first['files'] if row['path'] == '.claude/settings.json')
        transaction = read_json(RUN / 'install-transaction.json')
        saved = USER_ROOT / transaction['backup'] / 'files/.claude/settings.json'
        self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), expected)

    def test_cleanup_preserves_session_history_and_reproducibility(self):
        for name in read_json(RUN / 'history-before.json'):
            self.assertTrue((USER_ROOT / name).exists(), name)
        cleanup = read_json(RUN / 'cleanup-result.json')
        self.assertGreater(cleanup['bytes'], 0)
        for row in cleanup['removed']:
            target = Path(row['path'])
            self.assertFalse(target.exists())
            if target.name == 'node_modules':
                self.assertTrue((target.parent / 'package-lock.json').is_file())
                self.assertTrue((target.parent / 'plugin/extensions/athena-gates.ts').is_file())


if __name__ == '__main__':
    unittest.main()
