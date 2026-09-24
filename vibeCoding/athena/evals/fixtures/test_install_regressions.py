"""Regressions for the S6 review (round 1): TOML forms, failed installs, symlinks, user hooks, doctor."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from gate_harness import ENV, GATE, tmpdir
from test_install import build, cli, fake_999_home, snapshot

TOML_DRIVER = ("const p=require(process.argv[1]);const c=JSON.parse(require('fs').readFileSync(0,'utf8'));"
               "process.stdout.write(JSON.stringify(c.map(x=>p.mergeToml(x,'','/h','10.1.0'))));")


class Rounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = build(Path(cls.tmp.name) / 'dist')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def home(self):
        home = tmpdir(self) / 'home'
        (home / '.claude').mkdir(parents=True)
        (home / '.codex').mkdir()
        fake_999_home(home)
        return home

    def test_toml_forms_never_produce_a_second_table(self):
        cases = ['[shell_environment_policy.set] # env\nX = "1"\n', '[ shell_environment_policy.set ]\nX = "1"\n',
                 '["shell_environment_policy".set]\nX = "1"\n', '[shell_environment_policy]\nset.FOO = "1"\n',
                 '[shell_environment_policy]\nset = { FOO = "1" }\n', 'shell_environment_policy = { set = { FOO = "1" } }\n',
                 '[shell_environment_policy.set]\n"VIBECODING_VERSION" = "9.9.9"\n', 'model = "x"\r\n',
                 "[shell_environment_policy]\n'set' = { FOO = \"1\" }\n", "[shell_environment_policy]\n'set'.FOO = \"1\"\n",
                 "[shell_environment_policy.set]\n'VIBECODING_VERSION' = '9'\n",
                 '[shell_environment_policy]\ninherit = "core"\n\n[shell_environment_policy.set]\nVIBECODING_VERSION = "9.9.9"\n']
        out = json.loads(subprocess.run(['node', '-e', TOML_DRIVER, str(GATE / 'cli/lib/install-plan.cjs')], input=json.dumps(cases),
                                        text=True, capture_output=True, env=ENV).stdout)
        import tomllib  # noqa: the shim provides tomli on 3.10
        for case, res in zip(cases, out):
            with self.subTest(case=case.splitlines()[0]):
                data = tomllib.loads(res['text'])  # must stay valid TOML
                sep = data.get('shell_environment_policy', {}).get('set', {})
                self.assertTrue(res['note'] or sep.get('VIBECODING_VERSION') == '10.1.0', res)
        self.assertIn('\r\n', out[-5]['text'])
        self.assertIsNone(out[-1]['note'], 'the shipped template form is edited in place')

    def test_fresh_codex_config_carries_the_installed_version(self):
        home = tmpdir(self) / 'fresh'
        home.mkdir()
        self.assertEqual(cli('install', '--platform', 'cx', home=home, dist=self.dist).returncode, 0)
        self.assertIn('VIBECODING_VERSION = "10.1.0', (home / '.codex/config.toml').read_text())
        self.assertNotIn('"9.9.9"', (home / '.codex/config.toml').read_text())

    def test_path_conflicts_refuse_before_writing(self):
        home = self.home()
        (home / '.claude/workflows').write_text('a file where a directory is needed\n')
        before = snapshot(home)
        run = cli('install', '--platform', 'cc', home=home, dist=self.dist)
        self.assertEqual(run.returncode, 1)
        self.assertIn('is not a directory', run.stderr)
        self.assertEqual(snapshot(home), before)
        self.assertFalse((home / '.athena').exists())

    def test_symlinked_settings_survive_install_and_rollback(self):
        home = self.home()
        dotfiles = home / 'dotfiles'
        dotfiles.mkdir()
        shutil.move(str(home / '.claude/settings.json'), dotfiles / 'settings.json')
        os.symlink('../dotfiles/settings.json', home / '.claude/settings.json')
        original = (dotfiles / 'settings.json').read_text()
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=self.dist).returncode, 0)
        self.assertTrue((home / '.claude/settings.json').is_symlink())
        self.assertIn('.athena/current/hook.cjs', (dotfiles / 'settings.json').read_text())
        self.assertEqual(cli('rollback', home=home, dist=None).returncode, 0)
        self.assertTrue((home / '.claude/settings.json').is_symlink())
        self.assertEqual((dotfiles / 'settings.json').read_text(), original)

    def test_user_hook_with_a_999_name_elsewhere_is_kept(self):
        home = self.home()
        settings = json.loads((home / '.claude/settings.json').read_text())
        settings['hooks']['PreToolUse'].append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3 ~/myproj/hooks/pre-bash-guard.py'}]})
        (home / '.claude/settings.json').write_text(json.dumps(settings))
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=self.dist).returncode, 0)
        self.assertIn('~/myproj/hooks/pre-bash-guard.py', (home / '.claude/settings.json').read_text())

    def test_rollback_keeps_post_install_edits_and_retired_directories(self):
        home = self.home()
        (home / '.claude/hooks/delivery-gate.cjs').unlink()
        (home / '.claude/hooks/delivery-gate.cjs').mkdir()
        (home / '.claude/hooks/delivery-gate.cjs/mine.txt').write_text('user file\n')
        before = snapshot(home)
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=self.dist).returncode, 0)
        edited = json.loads((home / '.claude/settings.json').read_text())
        edited['added_after_install'] = True
        (home / '.claude/settings.json').write_text(json.dumps(edited))
        (home / '.athena/10.1/mynotes').mkdir()
        (home / '.athena/10.1/mynotes/n').write_text('note\n')
        back = cli('rollback', home=home, dist=None)
        self.assertEqual(back.returncode, 0, back.stderr)
        self.assertEqual(snapshot(home), {k: v for k, v in before.items()})
        kept = list((home / '.athena/backups').glob('*/after-install'))
        self.assertTrue(kept)
        self.assertIn('added_after_install', (kept[0] / '.claude/settings.json').read_text())
        self.assertTrue((kept[0] / '.athena/10.1/mynotes/n').is_file())
        self.assertFalse((home / '.athena/bin').exists(), 'directories the install created are removed')

    def test_doctor_catches_removed_hooks_and_broken_json(self):
        home = self.home()
        self.assertEqual(cli('install', '--platform', 'cc,cx', home=home, dist=self.dist).returncode, 0)
        (home / '.claude/settings.json').write_text('{}')
        (home / '.codex/hooks.json').write_text('not json')
        out = cli('doctor', home=home, dist=None)
        self.assertEqual(out.returncode, 1)
        self.assertIn('.claude/settings.json: ', out.stdout)
        self.assertIn('gates are off', out.stdout)
        self.assertIn('.codex/hooks.json unreadable', out.stdout)

    def test_invalid_user_json_is_a_clean_refusal(self):
        home = self.home()
        (home / '.claude/settings.json').write_text('{ "a": 1, }')
        run = cli('install', '--platform', 'cc', home=home, dist=self.dist)
        self.assertEqual(run.returncode, 1)
        self.assertIn('not valid JSON', run.stderr)
        self.assertNotIn('    at ', run.stderr, 'no stack trace')


class Recovery(unittest.TestCase):
    def test_interrupted_reinstall_is_rolled_back_first(self):
        tmp = tmpdir(self)
        dist = build(tmp / 'dist')
        home = tmp / 'home'
        (home / '.claude').mkdir(parents=True)
        (home / '.codex').mkdir()
        fake_999_home(home)
        before = snapshot(home)
        self.assertEqual(cli('install', '--platform', 'cc', home=home, dist=dist).returncode, 0)
        after_a = snapshot(home)
        driver = ("const fs=require('fs');const real=fs.renameSync;let n=0;fs.renameSync=function(){if(++n>25)process.exit(9);return real.apply(this,arguments)};"
                  "require(process.argv[1]).main(['install','--platform','cc','--home',process.argv[2],'--dist',process.argv[3]],"
                  "{cwd:process.argv[2],stdout:process.stdout,stderr:process.stderr,env:process.env});")
        run = subprocess.run(['node', '-e', driver, str(GATE / 'cli.cjs'), str(home), str(dist)], capture_output=True, text=True, env=ENV)
        self.assertEqual(run.returncode, 9, run.stderr)
        self.assertEqual(cli('rollback', home=home, dist=None).returncode, 0)
        self.assertEqual(snapshot(home), after_a, 'the interrupted install is undone first')
        self.assertEqual(cli('rollback', home=home, dist=None).returncode, 0)
        self.assertEqual(snapshot(home), before)


if __name__ == '__main__':
    unittest.main()
