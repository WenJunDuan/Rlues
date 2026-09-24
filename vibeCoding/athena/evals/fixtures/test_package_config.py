"""Package settings.json / config.toml: official names, security baseline, and installer merge of env/ask.

Sources (checked 2026-09-24): code.claude.com/docs/en/{permissions,discover-plugins,model-config};
learn.chatgpt.com codex agent-approvals-security; openai/codex config.schema.json.
"""
import json
from pathlib import Path
import re
import subprocess
import unittest

from gate_harness import ENV, GATE

ATHENA = Path(__file__).resolve().parents[2]
CC = ATHENA / 'adapters/cc/package/settings.json'
CX = ATHENA / 'adapters/cx/package/config.toml'
MARKER = re.compile(r'\{\{athena:[A-Z_]+\}\}')
MERGE = ("const p=require(process.argv[1]);const [c,q]=JSON.parse(require('fs').readFileSync(0,'utf8'));"
         "process.stdout.write(p.mergeSettings(c,q,'9.9.9-test'));")


def cc():
    return json.loads(MARKER.sub('x', CC.read_text(encoding='utf-8')))


def merge(current, proposed):
    run = subprocess.run(['node', '-e', MERGE, str(GATE / 'cli/lib/install-plan.cjs')], input=json.dumps([current, proposed]),
                         text=True, capture_output=True, env=ENV)
    if run.returncode:
        raise AssertionError(run.stderr)
    return json.loads(run.stdout)


class ClaudeSettings(unittest.TestCase):
    def test_plugins_use_declared_marketplaces(self):
        s = cc()
        known = {'claude-plugins-official', *s.get('extraKnownMarketplaces', {})}
        for key in s['enabledPlugins']:
            with self.subTest(plugin=key):
                self.assertRegex(key, r'^[a-z0-9-]+@[a-z0-9-]+$')
                self.assertIn(key.split('@', 1)[1], known, 'marketplace must be official or declared')

    def test_secrets_are_denied_for_read_and_edit(self):
        deny = set(cc()['permissions']['deny'])
        for path in ('./.env', '**/.env.*', '~/.ssh/**', '~/.aws/**', '**/*.pem'):
            for tool in ('Read', 'Edit'):
                self.assertIn(f'{tool}({path})', deny)

    def test_irreversible_commands_ask(self):
        ask = cc()['permissions']['ask']
        for rule in ('Bash(git push --force*)', 'Bash(npm publish*)'):
            self.assertIn(rule, ask)

    def test_no_pinned_or_undocumented_env(self):
        env = cc()['env']
        for key in ('ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_FABLE_MODEL', 'CLAUDE_CODE_ATTRIBUTION_HEADER', 'DISABLE_INSTALLATION_CHECKS'):
            self.assertNotIn(key, env, 'model pins go stale; undocumented keys stay in the user file')


class InstallerMerge(unittest.TestCase):
    def test_package_env_fills_gaps_user_wins(self):
        out = merge(json.dumps({'env': {'A': 'user', 'VIBECODING_ATHENA_VERSION': 'old'}}),
                    json.dumps({'env': {'A': 'pkg', 'B': 'pkg'}}))
        self.assertEqual(out['env'], {'A': 'user', 'B': 'pkg', 'VIBECODING_ATHENA_VERSION': '9.9.9-test'})

    def test_fresh_install_gets_package_env(self):
        out = merge('', json.dumps({'env': {'B': 'pkg'}}))
        self.assertEqual(out['env']['B'], 'pkg')

    def test_deny_and_ask_are_unions_and_user_allow_kept(self):
        out = merge(json.dumps({'permissions': {'allow': ['Bash(x)'], 'deny': ['Read(u)'], 'ask': ['Bash(u)']}}),
                    json.dumps({'permissions': {'allow': ['Bash(p)'], 'deny': ['Read(p)'], 'ask': ['Bash(p)']}}))
        self.assertEqual(out['permissions']['allow'], ['Bash(x)'])
        self.assertEqual(set(out['permissions']['deny']), {'Read(u)', 'Read(p)'})
        self.assertEqual(set(out['permissions']['ask']), {'Bash(u)', 'Bash(p)'})


class CodexConfig(unittest.TestCase):
    def text(self):
        return MARKER.sub('x', CX.read_text(encoding='utf-8'))

    def test_first_install_is_not_full_access(self):
        t = self.text()
        self.assertRegex(t, r'(?m)^approval_policy = "on-request"$')
        self.assertRegex(t, r'(?m)^sandbox_mode = "workspace-write"$')
        self.assertNotRegex(t, r'(?m)^sandbox_mode = "danger-full-access"')

    def test_no_deprecated_or_unknown_root_keys(self):
        t = self.text()
        for key in ('personality', 'windows_wsl_setup_acknowledged'):
            self.assertNotRegex(t, rf'(?m)^{key}\s*=')

    def test_parses(self):
        try:
            import tomllib
        except ModuleNotFoundError:  # py3.10
            import tomli as tomllib
        tomllib.loads(self.text())


if __name__ == '__main__':
    unittest.main()
