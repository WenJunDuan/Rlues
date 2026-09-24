"""athena install / rollback / doctor in a temporary HOME (athena-10-1 S6 AC1–AC4)."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from gate_harness import ATHENA, ENV, VIBE, athena, tmpdir

FROZEN_CC = VIBE / 'claude/9.9.9/.claude'
FROZEN_CX = VIBE / 'codex/9.9.9/.codex'


def build(out):
    run = subprocess.run(['node', str(ATHENA / 'build.mjs'), '--out', str(out)], capture_output=True, text=True, env=ENV)
    if run.returncode:
        raise AssertionError(run.stderr)
    return out


def fake_999_home(home):
    """A HOME as setup-athena.py 9.9.9 left it, plus user-owned additions."""
    for name in ('CLAUDE.md', 'hooks', 'agents', 'skills', 'rules', 'settings.json'):
        src = FROZEN_CC / name
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, home / '.claude' / name)
    settings = json.loads((home / '.claude/settings.json').read_text())
    settings['theme'] = 'dark'
    settings['hooks'].setdefault('PreToolUse', []).append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'echo user-hook'}]})
    (home / '.claude/settings.json').write_text(json.dumps(settings, indent=2))
    for name in ('AGENTS.md', 'hooks', 'agents', 'standards', 'hooks.json'):
        src = FROZEN_CX / name
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, home / '.codex' / name)
    config = (FROZEN_CX / 'config.toml').read_text().replace('<USER_HOME>', str(home))
    (home / '.codex/config.toml').write_text(config + '\n[profiles.mine]\nmodel = "user-choice"\n')
    shutil.copytree(FROZEN_CX / 'skills', home / '.agents/skills', ignore=shutil.ignore_patterns('__pycache__'))
    (home / '.claude/user-notes.md').write_text('mine\n')


def snapshot(home):
    out = {}
    for p in sorted(Path(home).rglob('*')):
        rel = p.relative_to(home).as_posix()
        if rel.startswith('.athena/backups') or not (p.is_file() or p.is_symlink()):
            continue
        out[rel] = os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def cli(*args, home, dist, cwd=None):
    return athena(*args, '--home', str(home), *(('--dist', str(dist)) if dist else ()), cwd=cwd or home)


class InstallRoundTrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = build(Path(cls.tmp.name) / 'dist')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_999_to_101_doctor_rollback(self):
        home = tmpdir(self) / 'home'
        (home / '.claude').mkdir(parents=True)
        (home / '.codex').mkdir()
        fake_999_home(home)
        before = snapshot(home)
        dry = cli('install', '--platform', 'cc,cx', '--dry-run', home=home, dist=self.dist)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn('retire .claude/hooks/delivery-gate.cjs', dry.stdout)
        self.assertEqual(snapshot(home), before, 'dry-run changes nothing')

        run = cli('install', '--platform', 'cc,cx', home=home, dist=self.dist)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(os.readlink(home / '.athena/current'), '10.1')
        self.assertTrue((home / '.athena/10.1/hook.cjs').is_file())
        self.assertFalse((home / '.claude/hooks/delivery-gate.cjs').exists())
        self.assertFalse((home / '.codex/hooks/delivery-gate.py').exists())
        settings = json.loads((home / '.claude/settings.json').read_text())
        self.assertEqual(settings['theme'], 'dark')
        commands = [h['command'] for groups in settings['hooks'].values() for g in groups for h in g['hooks']]
        self.assertIn('echo user-hook', commands)
        self.assertFalse([c for c in commands if '/.claude/hooks/' in c], 'no 9.9.9 hook survives the merge')
        self.assertTrue(any('~/.athena/current/hook.cjs PreToolUse --platform cc' in c for c in commands))
        cx_hooks = json.loads((home / '.codex/hooks.json').read_text())['hooks']
        self.assertTrue(all('.athena/current/hook.cjs' in h['command'] for gs in cx_hooks.values() for g in gs for h in g['hooks']))
        config = (home / '.codex/config.toml').read_text()
        self.assertIn('[profiles.mine]', config)
        self.assertRegex(config, r'VIBECODING_VERSION = "10\.1\.0')
        self.assertIn('athena review prepare', (home / '.agents/skills/athena-review/SKILL.md').read_text())
        self.assertEqual((home / '.claude/user-notes.md').read_text(), 'mine\n')

        doctor = cli('doctor', home=home, dist=None)
        self.assertEqual(doctor.returncode, 0, doctor.stdout)
        guard = subprocess.run(['node', str(home / '.athena/current/hook.cjs'), 'PreToolUse', '--platform', 'cc'],
                               input=json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'cwd': str(home),
                                                 'tool_input': {'command': 'rm -rf /'}}), text=True, capture_output=True)
        self.assertEqual(guard.returncode, 2, 'the installed core blocks')
        shim = subprocess.run([str(home / '.athena/bin/athena'), '--help'], capture_output=True, text=True, env={**ENV, 'HOME': str(home)})
        self.assertIn('usage: athena', shim.stdout)

        (home / '.claude/agents/reviewer.md').write_text('tampered\n')
        drift = cli('doctor', home=home, dist=None)
        self.assertEqual(drift.returncode, 1)
        self.assertIn('drift .claude/agents/reviewer.md', drift.stdout)

        back = cli('rollback', home=home, dist=None)
        self.assertEqual(back.returncode, 0, back.stderr)
        self.assertEqual(snapshot(home), before, 'rollback restores 9.9.9 byte for byte')
        self.assertEqual(cli('rollback', home=home, dist=None).returncode, 1)
        self.assertIn('not installed', cli('doctor', home=home, dist=None).stdout)

    def test_reinstall_then_rollback_returns_to_first_install(self):
        home = tmpdir(self) / 'home'
        home.mkdir()
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=self.dist).returncode, 0)
        first = snapshot(home)
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=self.dist).returncode, 0)
        self.assertEqual(cli('rollback', home=home, dist=None).returncode, 0)
        self.assertEqual(snapshot(home), first)
        self.assertEqual(cli('doctor', home=home, dist=None).returncode, 0)

    def test_tampered_or_incomplete_dist_is_refused(self):
        dist = Path(tempfile.mkdtemp()) / 'dist'
        shutil.copytree(self.dist, dist)
        home = tmpdir(self) / 'home'
        home.mkdir()
        (dist / 'claude/10.1/.claude/CLAUDE.md').write_text('tampered\n')
        run = cli('install', '--platform', 'cc', home=home, dist=dist)
        self.assertEqual(run.returncode, 1)
        self.assertIn('dist asset altered: claude/10.1/.claude/CLAUDE.md', run.stderr)
        manifest = dist / 'athena/10.1/manifest.json'
        data = json.loads(manifest.read_text())
        data['files'] = [f for f in data['files'] if f['path'] != 'lib/shell-lex.cjs']
        manifest.write_text(json.dumps(data))
        (dist / 'athena/10.1/lib/shell-lex.cjs').unlink()
        run = cli('install', '--platform', 'cx', home=home, dist=dist)
        self.assertEqual(run.returncode, 1)
        self.assertIn('required asset: lib/shell-lex.cjs', run.stderr)
        self.assertEqual(list(home.iterdir()), [], 'nothing written on refusal')
        shutil.rmtree(dist.parent)

    def test_usage(self):
        home = tmpdir(self)
        for args in (('install',), ('install', '--platform', 'vim'), ('install', '--platform', 'cc', '--bogus')):
            with self.subTest(args=args):
                self.assertEqual(athena(*args, cwd=home).returncode, 2)


if __name__ == '__main__':
    unittest.main()
