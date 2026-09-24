"""Gate core size, distribution shape and contract consistency (athena-10-1 S2 AC8, AC9)."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from gate_harness import ATHENA, ENV, GATE

DEAD_HOOKS = ('pace-continuator', 'compact-snapshot', 'subagent-retry')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Budget(unittest.TestCase):
    def test_line_budget(self):
        """Hook path (hook/core/lib/rules/platform) ≤3,000 lines; every file incl. the CLI ≤300 (S4 design)."""
        files = sorted(GATE.rglob('*.cjs'))
        counts = {f.relative_to(GATE).as_posix(): len(f.read_text(encoding='utf-8').splitlines()) for f in files}
        hook_path = {k: v for k, v in counts.items() if not k.startswith('cli')}
        self.assertLessEqual(sum(hook_path.values()), 3000, hook_path)
        for name, lines in counts.items():
            with self.subTest(file=name):
                self.assertLessEqual(lines, 300)

    def test_no_python_or_foreign_files_in_gate(self):
        for path in GATE.rglob('*'):
            if path.is_file():
                rel = path.relative_to(GATE).as_posix()
                with self.subTest(path=rel):
                    if rel.startswith('templates/'):
                        self.assertIn(path.suffix, ('.md', '.yaml'))
                    else:
                        self.assertEqual(path.suffix, '.cjs')


class Distribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / 'dist'
        run = subprocess.run(['node', str(ATHENA / 'build.mjs'), '--out', str(cls.out)], text=True, capture_output=True, env=ENV)
        if run.returncode:
            raise AssertionError(run.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def files(self, platform):
        root = self.out / platform / '10.1'
        return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}

    def test_no_legacy_hooks_anywhere(self):
        for platform in ('claude', 'codex', 'pi', 'athena'):
            for rel in self.files(platform):
                with self.subTest(platform=platform, file=rel):
                    self.assertNotRegex(rel, r'(^|/)\.(claude|codex)/hooks/')
                    self.assertNotIn('cc-core/', rel)
                    self.assertFalse(any(dead in rel for dead in DEAD_HOOKS))

    def test_hook_registrations_point_at_the_one_core(self):
        keys = subprocess.run(['node', '-e', "process.stdout.write(JSON.stringify(Object.keys(require(process.argv[1]).EVENTS)))",
                               str(GATE / 'platform/cc.cjs')], text=True, capture_output=True, env=ENV)
        events = set(json.loads(keys.stdout))
        for platform, rel, pattern in (
                ('claude', '.claude/settings.json', r'^node ~/\.athena/current/hook\.cjs ([A-Za-z]+) --platform cc$'),
                ('codex', '.codex/hooks.json', r'^/usr/bin/env node ~/\.athena/current/hook\.cjs ([A-Za-z]+) --platform cx$')):
            hooks = json.loads(self.files(platform)[rel].read_text(encoding='utf-8'))['hooks']
            for event, groups in hooks.items():
                for group in groups:
                    for hook in group['hooks']:
                        with self.subTest(platform=platform, event=event):
                            m = re.match(pattern, hook['command'])
                            self.assertTrue(m, hook['command'])
                            self.assertEqual(m.group(1), event)
                            self.assertIn(event, events, 'adapter must map every registered event')

    def test_core_dist_and_pi_vendor_are_byte_identical_to_gate(self):
        core = self.files('athena')
        gate = {p.relative_to(GATE).as_posix(): p for p in GATE.rglob('*') if p.is_file()}
        self.assertEqual(set(gate), set(core) - {'GENERATED.md', 'manifest.json', 'contracts.json'})
        pi = {k[len('plugin/core/gate/'):]: v for k, v in self.files('pi').items() if k.startswith('plugin/core/gate/')}
        self.assertEqual(set(pi), set(gate))
        for rel in gate:
            with self.subTest(file=rel):
                self.assertEqual(sha(core[rel]), sha(gate[rel]))
                self.assertEqual(sha(pi[rel]), sha(gate[rel]))
        self.assertTrue((self.out / 'athena/10.1/hook.cjs').stat().st_mode & 0o111)

    def test_contracts_name_existing_rules(self):
        contracts = json.loads((self.out / 'athena/10.1/contracts.json').read_text(encoding='utf-8'))
        for rule in contracts['hard']:
            with self.subTest(rule=rule):
                self.assertEqual(len(list((GATE / 'rules').glob(f'{rule.lower()}-*.cjs'))), 1)
        checks = subprocess.run(['node', '-e', "process.stdout.write(JSON.stringify(Object.keys(require(process.argv[1]).CHECKS)))",
                                 str(GATE / 'rules/advisory.cjs')], text=True, capture_output=True, env=ENV)
        self.assertEqual(sorted(json.loads(checks.stdout)), sorted(contracts['advisory']))
        ship = next(s for s in contracts['stages'] if s['id'] == 'ship')
        at_ship = subprocess.run(['node', '-e', "process.stdout.write(JSON.stringify(require(process.argv[1]).AT.ship))",
                                  str(GATE / 'rules/advisory.cjs')], text=True, capture_output=True, env=ENV)
        self.assertEqual(json.loads(at_ship.stdout), ship['advisory'])


if __name__ == '__main__':
    unittest.main()
