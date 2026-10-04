"""athena-10-5 S3: Claude Code / Codex plugin shells (build outputs), constitution injection for the
plugin form (ATHENA_CONSTITUTION), and the plugin section of `athena doctor`.

The manifests are checked against the fields this repo relies on only; neither `claude plugin validate`
nor Codex is run here.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from gate_harness import ATHENA, ENV, GOOD_DESIGN, athena, call, project, tmpdir

VERSION = (ATHENA / 'VERSION').read_text(encoding='utf-8').strip()
RELEASE = '.'.join(VERSION.split('-')[0].split('.')[:2])
GENERATED = ('manifest.json', 'GENERATED.md', 'contracts.json')
INSTALLER_DISTS = ('claude', 'codex', 'pi', 'athena')
IGNORED = {'__pycache__', '.DS_Store'}
_TMP = None
DIST = None


def build(out, src=ATHENA):
    return subprocess.run(['node', str(src / 'build.mjs'), '--src', str(src), '--out', str(out)], capture_output=True, text=True, env=ENV)


def setUpModule():
    global _TMP, DIST
    _TMP = tempfile.TemporaryDirectory()
    DIST = Path(_TMP.name) / 'dist'
    run = build(DIST)
    if run.returncode:
        raise AssertionError(run.stderr)


def tearDownModule():
    _TMP.cleanup()


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(Path(root).rglob('*'))
            if p.is_file() and not (IGNORED & set(p.relative_to(root).parts))}


def out(name):
    return DIST / name / RELEASE


def hook_shape(hooks):
    """{event: [(matcher, [timeouts], [extra keys])]} — everything but the command."""
    return {event: [(g.get('matcher'), [{k: v for k, v in h.items() if k != 'command'} for h in g['hooks']]) for g in groups]
            for event, groups in hooks.items()}


def commands(hooks):
    return [(event, h['command']) for event, groups in hooks.items() for g in groups for h in g['hooks']]


def copy_source(tmp):
    src = Path(tmp) / 'athena'
    shutil.copytree(ATHENA, src, ignore=shutil.ignore_patterns('evals', '__pycache__'))
    return src


class PluginShells(unittest.TestCase):
    def test_outputs_exist_with_generated_files_and_manifest(self):
        for name, files in (('claude-plugin', ('.claude-plugin/plugin.json', 'hooks/hooks.json', 'gate/hook.cjs', 'gate/cli.cjs', 'bin/athena',
                                               'constitution.md', 'README.md', 'skills/pace/SKILL.md', 'skills/pace/references/stages.md',
                                               'agents/reviewer.md')),
                            ('codex-plugin', ('plugin.json', 'hooks/hooks.json', 'gate/hook.cjs', 'README.md', 'skills/pace/SKILL.md',
                                              'skills/pace/references/stages.md', 'skills/athena-init/agents/openai.yaml'))):
            for rel in (*files, *GENERATED):
                with self.subTest(dist=name, file=rel):
                    self.assertTrue((out(name) / rel).is_file())
            manifest = json.loads((out(name) / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['version'], VERSION)
            self.assertEqual({e['path'] for e in manifest['files']}, set(tree(out(name))) - {'manifest.json'})

    def test_manifests(self):
        cc = json.loads((out('claude-plugin') / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        self.assertEqual((cc['name'], cc['version']), ('athena', VERSION))
        self.assertTrue(cc['description'])
        self.assertLessEqual(set(cc), {'name', 'version', 'description', 'author'})
        cx = json.loads((out('codex-plugin') / 'plugin.json').read_text(encoding='utf-8'))
        self.assertEqual((cx['name'], cx['version']), ('athena', VERSION))
        self.assertTrue(cx['description'])
        self.assertEqual(cx['extensions'], {'com.openai': {'hooks': './hooks/hooks.json'}})
        self.assertEqual(set(cx), {'name', 'version', 'description', 'extensions'})

    def test_hooks_match_installer_form_and_use_the_plugin_root(self):
        installer = {'claude-plugin': json.loads((ATHENA / 'adapters/cc/package/settings.json').read_text(encoding='utf-8'))['hooks'],
                     'codex-plugin': json.loads((ATHENA / 'adapters/cx/package/hooks.json').read_text(encoding='utf-8'))['hooks']}
        for name, var, platform in (('claude-plugin', '${CLAUDE_PLUGIN_ROOT}', 'cc'), ('codex-plugin', '${PLUGIN_ROOT}', 'cx')):
            data = json.loads((out(name) / 'hooks/hooks.json').read_text(encoding='utf-8'))
            self.assertEqual(list(data), ['hooks'])
            self.assertEqual(hook_shape(data['hooks']), hook_shape(installer[name]), name)
            for event, command in commands(data['hooks']):
                with self.subTest(dist=name, event=event):
                    self.assertTrue(command.endswith(f'node "{var}/gate/hook.cjs" {event} --platform {platform}'), command)
                    self.assertNotIn('.athena', command)
                    self.assertNotIn('~', command)
        cc = dict(commands(json.loads((out('claude-plugin') / 'hooks/hooks.json').read_text(encoding='utf-8'))['hooks']))
        self.assertTrue(cc['SessionStart'].startswith('ATHENA_CONSTITUTION="${CLAUDE_PLUGIN_ROOT}/constitution.md" node '))
        self.assertEqual([e for e, c in cc.items() if 'ATHENA_CONSTITUTION' in c], ['SessionStart'])

    def test_gate_core_is_byte_identical_to_the_athena_output(self):
        source = set(tree(ATHENA / 'gate'))
        core = tree(out('athena'))
        for name in ('claude-plugin', 'codex-plugin'):
            gate = tree(out(name) / 'gate')
            self.assertEqual(set(gate), source, name)
            for rel, content in gate.items():
                with self.subTest(dist=name, file=rel):
                    self.assertEqual(content, core[rel])
                    self.assertEqual(os.access(out(name) / 'gate' / rel, os.X_OK), os.access(out('athena') / rel, os.X_OK))

    def test_skills_and_agents_share_the_installer_sources(self):
        cc, cx = tree(out('claude') / '.claude'), tree(out('codex') / '.codex')
        plugin_cc, plugin_cx = tree(out('claude-plugin')), tree(out('codex-plugin'))
        for label, plugin, installer in (('cc', plugin_cc, cc), ('cx', plugin_cx, cx)):
            self.assertEqual({k for k in plugin if k.startswith('skills/')}, {k for k in installer if k.startswith('skills/')}, label)
        agents = {k: v for k, v in plugin_cc.items() if k.startswith('agents/')}
        self.assertEqual(agents, {k: v for k, v in cc.items() if k.startswith('agents/')})
        self.assertTrue(agents)
        self.assertFalse([k for k in plugin_cx if k.startswith('agents/') or k.endswith('.toml') or k == 'AGENTS.md'], 'no Codex agents / config / AGENTS.md')
        self.assertFalse([k for k in plugin_cc if k == 'CLAUDE.md' or k.startswith('rules/') or k == 'settings.json'])
        for name, plugin in (('claude-plugin', plugin_cc), ('codex-plugin', plugin_cx)):
            self.assertFalse([k for k, v in plugin.items() if b'{{athena:' in v and not k.startswith('gate/')], name)

    def test_constitution_is_the_core_agents_md_and_fits_the_injection_cap(self):
        text = (out('claude-plugin') / 'constitution.md').read_text(encoding='utf-8')
        source = (ATHENA / 'core/package/AGENTS.md').read_text(encoding='utf-8')
        self.assertEqual(text, source.replace('{{athena:SKILLS_DIR}}', '${CLAUDE_PLUGIN_ROOT}/skills'))
        self.assertLessEqual(len(text.encode('utf-8')), 4096)

    def test_readmes_are_short(self):
        for name in ('claude-plugin', 'codex-plugin'):
            text = (out(name) / 'README.md').read_text(encoding='utf-8')
            self.assertLessEqual(len(text.splitlines()), 40, name)
            self.assertIn(VERSION, text)
            self.assertIn('athena install', text)
        self.assertIn('--plugin-dir', (out('claude-plugin') / 'README.md').read_text(encoding='utf-8'))
        self.assertIn('/hooks', (out('codex-plugin') / 'README.md').read_text(encoding='utf-8'))

    def test_bin_athena_runs_from_the_built_plugin(self):
        shim = out('claude-plugin') / 'bin/athena'
        self.assertTrue(os.access(shim, os.X_OK))
        home = tmpdir(self)
        run = subprocess.run([str(shim), '--help'], capture_output=True, text=True, cwd=str(home), env={**ENV, 'HOME': str(home)})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('usage: athena', run.stdout)
        link = home / 'athena-link'
        link.symlink_to(shim)
        self.assertIn('usage: athena', subprocess.run([str(link), '--help'], capture_output=True, text=True, env=ENV).stdout)

    def run_hook(self, name, var, event, payload, cwd):
        hooks = json.loads((out(name) / 'hooks/hooks.json').read_text(encoding='utf-8'))['hooks']
        command = dict(commands(hooks))[event]
        env = {**ENV, 'HOME': str(cwd), var: str(out(name))}
        env.pop('ATHENA_CONSTITUTION', None)
        return subprocess.run(['sh', '-c', command], input=json.dumps(payload), capture_output=True, text=True, cwd=str(cwd), env=env)

    def test_plugin_hook_commands_run_the_vendored_gate(self):
        """The commands as shipped, with only the plugin root variable set and an empty HOME (no ~/.athena)."""
        for name, var in (('claude-plugin', 'CLAUDE_PLUGIN_ROOT'), ('codex-plugin', 'PLUGIN_ROOT')):
            cwd = tmpdir(self)
            with self.subTest(dist=name):
                guard = self.run_hook(name, var, 'PreToolUse', {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'cwd': str(cwd),
                                                                'tool_input': {'command': 'rm -rf /'}}, cwd)
                self.assertEqual(guard.returncode, 2, guard.stderr)
                start = self.run_hook(name, var, 'SessionStart', {'hook_event_name': 'SessionStart', 'cwd': str(cwd)}, cwd)
                self.assertEqual(start.returncode, 0, start.stderr)
                if name == 'claude-plugin':
                    context = json.loads(start.stdout)['hookSpecificOutput']['additionalContext']
                    self.assertIn('# Athena — 工程协作约定', context)
                    self.assertIn(f'{out(name)}/skills/pace/references/stages.md', context)
                    self.assertNotIn('${CLAUDE_PLUGIN_ROOT}', context)
                else:
                    self.assertEqual(start.stdout, '', 'Codex plugin form injects no constitution (AGENTS.md comes from the installer)')

    def test_installer_outputs_do_not_depend_on_the_plugin_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = copy_source(tmp)
            shutil.rmtree(src / 'adapters/cc-plugin')
            shutil.rmtree(src / 'adapters/cx-plugin')
            alone = Path(tmp) / 'dist'
            self.assertEqual(build(alone, src).returncode, 0)
            self.assertEqual(sorted(p.name for p in alone.iterdir()), sorted(INSTALLER_DISTS))
            for name in INSTALLER_DISTS:
                with self.subTest(dist=name):
                    self.assertEqual(tree(alone / name / RELEASE), tree(out(name)))


class AdapterMap(unittest.TestCase):
    """build.mjs "adapter_map": take files of another adapter's package/ (validated like core_map)."""

    def fails(self, mutate, needle):
        with tempfile.TemporaryDirectory() as tmp:
            src = copy_source(tmp)
            config = src / 'adapters/cc-plugin/platform.json'
            data = json.loads(config.read_text(encoding='utf-8'))
            mutate(data)
            config.write_text(json.dumps(data), encoding='utf-8')
            run = build(Path(tmp) / 'dist', src)
            self.assertEqual(run.returncode, 2, run.stdout)
            self.assertIn(needle, run.stderr)
            self.assertFalse((Path(tmp) / 'dist').exists(), 'nothing written')

    def test_unknown_adapter(self):
        self.fails(lambda d: d.update(adapter_map={'nope': {'agents/': 'agents/'}}), 'adapter_map names unknown adapter nope')

    def test_self_reference(self):
        self.fails(lambda d: d.update(adapter_map={'cc-plugin': {'agents/': 'agents/'}}), 'adapter_map names unknown adapter cc-plugin')

    def test_key_matching_no_file(self):
        self.fails(lambda d: d.update(adapter_map={'cc': {'nothing/': 'agents/'}}), 'adapter_map.cc key nothing/ matches no source file')

    def test_invalid_entries(self):
        self.fails(lambda d: d.update(adapter_map=['cc']), 'adapter_map must be an object')
        self.fails(lambda d: d.update(adapter_map={'cc': {'agents/': '../agents/'}}), 'invalid adapter_map.cc entry agents/')
        self.fails(lambda d: d.update(adapter_map={'cc': {'agents/': 'agents'}}), 'invalid adapter_map.cc entry agents/')

    def test_conflict_with_core_fails(self):
        self.fails(lambda d: d.update(adapter_map={'cc': {'agents/reviewer.md': 'skills/pace/SKILL.md'}}), 'conflict: skills/pace/SKILL.md')

    def test_only_mapped_files_are_taken_and_rendered_with_own_vars(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = copy_source(tmp)
            (src / 'adapters/cc/package/agents/zz-probe.md').write_text('skills at {{athena:SKILLS_DIR}}\n', encoding='utf-8')
            dist = Path(tmp) / 'dist'
            self.assertEqual(build(dist, src).returncode, 0)
            plugin = dist / 'claude-plugin' / RELEASE
            self.assertEqual((plugin / 'agents/zz-probe.md').read_text(encoding='utf-8'), 'skills at ${CLAUDE_PLUGIN_ROOT}/skills\n')
            self.assertEqual((dist / 'claude' / RELEASE / '.claude/agents/zz-probe.md').read_text(encoding='utf-8'), 'skills at ~/.claude/skills\n')
            self.assertFalse((plugin / 'settings.json').exists())
            self.assertFalse((plugin / 'workflows').exists())
            manifest = {e['path']: e for e in json.loads((plugin / 'manifest.json').read_text(encoding='utf-8'))['files']}
            self.assertEqual(manifest['agents/zz-probe.md']['source'], 'adapters/cc/package/agents/zz-probe.md')


class ConstitutionInjection(unittest.TestCase):
    TEXT = '# Athena — 工程协作约定\n\n- 完成：验收标准都有证据。\n'

    def file(self, text=None):
        path = tmpdir(self) / 'constitution.md'
        path.write_text(self.TEXT if text is None else text, encoding='utf-8')
        return path

    def env(self, path):
        return {'ATHENA_CONSTITUTION': str(path)}

    def test_env_unset_is_unchanged(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        context = call('cc', 'session', root).context
        self.assertTrue(context.startswith('[athena] path=Feature stage=impl'))
        self.assertNotIn('工程协作约定', context)
        bare = project(tmpdir(self), stage=None)
        verdict = call('cc', 'session', bare)
        self.assertEqual((verdict.context, verdict.raw.stdout, verdict.raw.stderr), ('', '', ''))

    def test_env_set_prepends_the_constitution_on_session_start(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        context = call('cc', 'session', root, env=self.env(self.file())).context
        self.assertTrue(context.startswith(self.TEXT.strip() + '\n\n[athena] path=Feature stage=impl'), context)

    def test_state_lines_survive_a_constitution_near_the_cap(self):
        big = 'x' * 4000 + '\nEND-OF-CONSTITUTION\n'
        self.assertLessEqual(len(big.encode()), 4096)
        root = project(tmpdir(self), path='Feature', stage='impl', extra_index='next_action: "finish AC1"\n')
        context = call('cc', 'session', root, env=self.env(self.file(big))).context
        self.assertIn('END-OF-CONSTITUTION', context)
        self.assertIn('stage=impl', context)
        self.assertIn('finish AC1', context)

    def test_oversized_file_is_skipped_with_a_warning(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        verdict = call('cc', 'session', root, env=self.env(self.file('y' * 4097)))
        self.assertTrue(verdict.context.startswith('[athena] path=Feature stage=impl'))
        self.assertNotIn('yyyy', verdict.context)
        self.assertIn('advisory constitution', verdict.raw.stderr)
        self.assertIn('4097 bytes', verdict.raw.stderr)
        self.assertEqual(verdict.raw.returncode, 0)

    def test_unreadable_file_is_skipped_with_a_warning(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        verdict = call('cc', 'session', root, env=self.env(tmpdir(self) / 'missing.md'))
        self.assertTrue(verdict.context.startswith('[athena] path=Feature'))
        self.assertIn('ATHENA_CONSTITUTION unreadable', verdict.raw.stderr)

    def test_no_ai_state_still_injects(self):
        bare = project(tmpdir(self), stage=None)
        self.assertEqual(call('cc', 'session', bare, env=self.env(self.file())).context, self.TEXT.strip())
        plain = tmpdir(self)   # not even a git repository
        self.assertEqual(call('cc', 'session', plain, env=self.env(self.file())).context, self.TEXT.strip())

    def test_prompt_and_tool_events_never_carry_it(self):
        root = project(tmpdir(self), path='Refactor', stage='impl', design=GOOD_DESIGN)
        env = self.env(self.file())
        self.assertEqual(call('cc', 'prompt', root, env=env).context, '')
        call('cc', 'agent', root, type='polish-worker', env=env)
        queued = call('cc', 'prompt', root, env=env).context
        self.assertIn('polish-worker', queued)
        self.assertNotIn('工程协作约定', queued)
        self.assertFalse(call('cc', 'bash', root, command='ls', env=env).blocked)

    def test_plugin_root_placeholder_is_resolved(self):
        bare = project(tmpdir(self), stage=None)
        path = self.file('see ${CLAUDE_PLUGIN_ROOT}/skills/pace\n')
        self.assertEqual(call('cc', 'session', bare, env={**self.env(path), 'CLAUDE_PLUGIN_ROOT': '/opt/plugin'}).context, 'see /opt/plugin/skills/pace')


class DoctorPluginForms(unittest.TestCase):
    def doctor(self, home):
        return athena('doctor', '--home', str(home), cwd=home)

    def plugin(self, home, platform, version='10.5.0', name='athena'):
        if platform == 'cc':
            manifest = home / '.claude/plugins/cache/local/athena' / version / '.claude-plugin/plugin.json'
        else:
            manifest = home / '.codex/plugins/cache/local/athena' / version / 'plugin.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'name': name, 'version': version}), encoding='utf-8')

    def test_no_plugins_keeps_the_existing_report(self):
        home = tmpdir(self)
        run = self.doctor(home)
        self.assertEqual(run.returncode, 1)
        self.assertIn('FAIL not installed', run.stdout)
        self.assertIn('ok   plugin cc: none under ~/.claude/plugins', run.stdout)
        self.assertIn('ok   plugin cx: none under ~/.codex/plugins/cache', run.stdout)
        self.assertNotIn('WARN', run.stdout)
        self.assertEqual(list(home.iterdir()), [], 'read-only')

    def test_plugins_are_reported_with_versions(self):
        home = tmpdir(self)
        self.plugin(home, 'cc')
        self.plugin(home, 'cx', version='10.5.1')
        other = home / '.claude/plugins/cache/local/other/1.0.0/.claude-plugin/plugin.json'
        other.parent.mkdir(parents=True)
        other.write_text(json.dumps({'name': 'other', 'version': '1.0.0'}), encoding='utf-8')
        (home / '.claude/plugins/broken/.claude-plugin').mkdir(parents=True)
        (home / '.claude/plugins/broken/.claude-plugin/plugin.json').write_text('{not json', encoding='utf-8')
        before = sorted(p.as_posix() for p in home.rglob('*'))
        run = self.doctor(home)
        self.assertEqual(run.returncode, 1, 'plugin presence does not change the exit code')
        self.assertIn('ok   plugin cc: athena 10.5.0 at ~/.claude/plugins/cache/local/athena/10.5.0', run.stdout)
        self.assertIn('ok   plugin cx: athena 10.5.1 at ~/.codex/plugins/cache/local/athena/10.5.1', run.stdout)
        self.assertNotIn('other', run.stdout)
        self.assertNotIn('WARN', run.stdout, 'no installer hooks → no double-hook warning')
        self.assertEqual(sorted(p.as_posix() for p in home.rglob('*')), before, 'read-only')

    def test_both_forms_warn_without_changing_the_exit_code(self):
        home = tmpdir(self)
        install = athena('install', '--platform', 'cc,cx', '--home', str(home), '--dist', str(DIST), cwd=home)
        self.assertEqual(install.returncode, 0, install.stderr)
        clean = self.doctor(home)
        self.assertEqual(clean.returncode, 0, clean.stdout)
        self.assertNotIn('WARN', clean.stdout)
        self.plugin(home, 'cc')
        run = self.doctor(home)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn('doctor: no drift', run.stdout)
        self.assertRegex(run.stdout, r'WARN cc: plugin form and installer form both present \(9 Athena hook\(s\) in ~/\.claude/settings\.json\)')
        self.assertNotIn('WARN cx', run.stdout)
        self.plugin(home, 'cx')
        run = self.doctor(home)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertRegex(run.stdout, r'WARN cx: plugin form and installer form both present \(8 Athena hook\(s\) in ~/\.codex/hooks\.json\)')


if __name__ == '__main__':
    unittest.main()
