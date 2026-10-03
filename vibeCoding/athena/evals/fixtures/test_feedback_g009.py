import json
import subprocess
import unittest
from gate_harness import GATE, ENV, tmpdir

class AgentPath(unittest.TestCase):
    def test_hook_prepend_makes_cli_visible_and_is_idempotent(self):
        home = tmpdir(self)
        bin_dir = home / '.athena/bin'; bin_dir.mkdir(parents=True)
        cli = bin_dir / 'athena'; cli.write_text('#!/bin/sh\necho fixture-athena\n'); cli.chmod(0o755)
        code = "const h=require(process.argv[1]); h.run('cc',{},'SessionStart'); h.run('cc',{},'SessionStart'); console.log(JSON.stringify({path:process.env.PATH, out:require('child_process').spawnSync('athena',[],{encoding:'utf8'}).stdout}));"
        run = subprocess.run(['node', '-e', code, str(GATE / 'hook.cjs')], env={**ENV, 'HOME': str(home)}, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(run.stdout)
        self.assertTrue(data['path'].startswith(str(bin_dir) + ':'))
        self.assertEqual(data['path'].split(':').count(str(bin_dir)), 1)
        self.assertEqual(data['out'], 'fixture-athena\n')

    def test_shell_hint_only_when_path_line_missing(self):
        home = tmpdir(self); rc = home / '.zshrc'
        code = "console.log(require(process.argv[1]).shellPathHint(process.argv[2],{SHELL:'/bin/zsh'}));"
        def hint():
            run = subprocess.run(['node','-e',code,str(GATE/'cli/install.cjs'),str(home)], env=ENV, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            return run.stdout.strip()
        self.assertIn('export PATH=', hint())
        rc.write_text('# export PATH="$HOME/.athena/bin:$PATH"\n')
        self.assertIn('export PATH=', hint())
        rc.write_text('export PATH="$HOME/.athena/bin:$PATH"\n')
        before = rc.read_text()
        self.assertEqual(hint(), '')
        self.assertEqual(rc.read_text(), before)

    def test_agent_shell_commands_export_path(self):
        for rel in ('cc/package/agents/generator.md', 'cc/package/agents/reviewer.md',
                    'cx/package/agents/generator.toml', 'cx/package/agents/reviewer.toml',
                    'pi/top/plugin/prompts/generator.md', 'pi/top/plugin/prompts/reviewer.md'):
            self.assertIn('export PATH="$HOME/.athena/bin:$PATH"', (GATE.parent / 'adapters' / rel).read_text(), rel)
