"""Regressions for the 2026-09-07 Claude 9.9.9 rework findings."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CX = ROOT / 'codex/9.9.9/.codex/hooks'
CC = ROOT / 'claude/9.9.9/.claude/hooks'
CX_SKILLS = ROOT / 'codex/9.9.9/.codex/skills'
SETUP = CX_SKILLS / 'athena-setup/scripts/setup-athena.py'
INIT = CX_SKILLS / 'athena-init/scripts/init-platforms.py'
RUNTIME = CX_SKILLS / 'athena-vm/scripts/runtime-run.py'


def py_module(name):
    sys.path.insert(0, str(CX))
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), CX / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class BindingRework(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.sprint = self.root / '.ai_state/sprints/test'
        self.sprint.mkdir(parents=True)
        (self.root / '.ai_state/_index.md').write_text(
            '---\nversion: "9.9.8"\ncurrent_sprint_slug: "test"\n---\n'
        )
        (self.sprint / 'design.md').write_text('## Done Contract\n- AC1: returns exact bytes\n')
        (self.root / 'app.py').write_text('print(1)\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'app.py'], check=True)
        subprocess.run(
            ['git', '-C', str(self.root), '-c', 'user.name=Fixture',
             '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base'],
            check=True,
        )

    def review_command(self, platform, action, *args):
        directory, suffix, runner = (CX, '.py', sys.executable) if platform == 'cx' else (CC, '.cjs', 'node')
        cli = directory.parent / 'skills/pace/scripts' / ('review-binding' + suffix)
        return subprocess.run(
            [runner, str(cli), action, '--cwd', str(self.root), *args],
            text=True, capture_output=True,
        )

    def prepare_packet(self):
        design = (self.sprint / 'design.md').read_bytes()
        (self.sprint / 'review-packet.md').write_text(
            '---\nsource_design_sha256: "' + hashlib.sha256(design).hexdigest()
            + '"\n---\n## Done Contract\n- AC1: returns exact bytes\n'
        )
        (self.sprint / 'evidence.yaml').write_text(
            'collected_evidence:\n  - tool_use_id: "run-one"\n    result: pass\n'
        )

    def test_binding_required_ignores_index_version(self):
        binding = py_module('_input_binding')
        self.assertTrue(binding.required(self.sprint))
        code = (
            'const m=require(process.argv[1]);'
            'process.stdout.write(String(m.required(process.argv[2])));'
        )
        run = subprocess.run(
            ['node', '-e', code, str(CC / '_input-binding.cjs'), str(self.sprint)],
            text=True, capture_output=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, 'true')

    def test_gitlink_is_skipped_not_thrown(self):
        vendor = self.root / 'vendor'
        vendor.write_text('blob\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'vendor'], check=True)
        vendor.unlink()
        vendor.mkdir()
        (vendor / 'nested.txt').write_text('dir\n')
        binding = py_module('_input_binding')
        digest = binding.source_sha256(self.root)
        self.assertEqual(len(digest), 64)
        code = (
            'const m=require(process.argv[1]);'
            'process.stdout.write(m.sourceSha256(process.argv[2]));'
        )
        run = subprocess.run(
            ['node', '-e', code, str(CC / '_input-binding.cjs'), str(self.root)],
            text=True, capture_output=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, digest)
        self.assertIn('skip gitlink', run.stderr)

    def test_evidence_append_and_later_commit_do_not_void_review(self):
        self.prepare_packet()
        binding = py_module('_review_binding')
        prepared = binding.prepare(self.root, 'implementation', [])
        run = prepared['review_run_id']
        dispatch = self.sprint / 'dispatch.json'
        dispatch.write_text(json.dumps({'agent_id': 'native-one'}))
        binding.bind(self.root, run, dispatch)
        (self.sprint / 'evidence.yaml').write_text(
            'collected_evidence:\n  - tool_use_id: "run-one"\n    result: pass\n'
            '  - tool_use_id: "run-two"\n    result: pass\n'
        )
        subprocess.run(['git', '-C', str(self.root), 'commit', '--allow-empty', '-qm', 'bookkeeping'], check=True)
        result = self.sprint / 'result.json'
        result.write_text(json.dumps({
            'agent_id': 'native-one', 'status': 'completed', 'output': 'VERDICT: PASS\n',
        }))
        row = binding.accept(self.root, run, result)
        self.assertEqual(row['event'], 'accepted')
        binding.validate_current(self.root, self.sprint, self.sprint / 'reviews/implementation-review.md')

    def test_conflicting_verdicts_are_rejected(self):
        self.prepare_packet()
        for platform in ('cx', 'cc'):
            with self.subTest(platform=platform):
                prepared = json.loads(self.review_command(platform, 'prepare').stdout)
                target = '/root/conflict-' + platform
                dispatch = self.sprint / 'dispatch.json'
                dispatch.write_text(json.dumps({'task_name': target}))
                self.assertEqual(
                    self.review_command(platform, 'bind', '--run', prepared['review_run_id'], '--receipt', str(dispatch)).returncode,
                    0,
                )
                result = self.sprint / 'result.json'
                result.write_text(json.dumps({
                    'task_name': target,
                    'status': 'completed',
                    'output': 'VERDICT: FAIL\nIf empty-check is added then VERDICT: PASS\n',
                }))
                run = self.review_command(platform, 'accept', '--run', prepared['review_run_id'], '--receipt', str(result))
                self.assertEqual(run.returncode, 2, run.stdout)
                self.assertIn('conflicting verdicts', run.stderr)
                self.review_command(platform, 'supersede', '--run', prepared['review_run_id'])

    def test_cx_installed_layout_review_binding_help(self):
        home = self.root / 'home'
        hooks = home / '.codex/hooks'
        hooks.mkdir(parents=True)
        for name in ('_review_binding.py', '_input_binding.py', '_index_io.py', 'delivery-gate.py'):
            shutil.copy2(CX / name, hooks / name)
        script = home / '.agents/skills/pace/scripts/review-binding.py'
        script.parent.mkdir(parents=True)
        shutil.copy2(CX.parent / 'skills/pace/scripts/review-binding.py', script)
        env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home / '.codex'), PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run([sys.executable, str(script), '--help'], text=True, capture_output=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertIn('prepare', run.stdout)


class GuardAndLock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name)
        (self.cwd / '.ai_state').mkdir()
        (self.cwd / '.ai_state/_index.md').write_text('---\nstage: "impl"\ncurrent_sprint_slug: "test"\n---\n')

    def analyze(self, platform, command):
        directory, suffix, runner = (CX, '.py', sys.executable) if platform == 'cx' else (CC, '.cjs', 'node')
        payload = json.dumps({
            'cwd': str(self.cwd),
            'tool_name': 'Bash',
            'tool_input': {'command': command},
        })
        return subprocess.run(
            [runner, str(directory / ('pre-bash-guard' + suffix))],
            input=payload, text=True, capture_output=True,
        )

    def test_nested_push_and_shared_parser_cases(self):
        cases = [
            ("bash -c 'git push origin main'", True),
            ("git commit -m 'fix #12' && git push origin main", True),
            ('rm --recursive --force /', True),
            ('sudo rm -rf /', True),
            (r'\git push origin main', True),
            ("git commit -m 'fix #12'", False),
        ]
        for platform in ('cx', 'cc'):
            for command, blocked in cases:
                with self.subTest(platform=platform, command=command):
                    run = self.analyze(platform, command)
                    if blocked:
                        self.assertEqual(run.returncode, 2, run.stderr + run.stdout)
                    else:
                        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)

    def test_stale_empty_legacy_lock_is_cleared(self):
        with tempfile.TemporaryDirectory() as raw:
            ai = Path(raw) / '.ai_state'
            ai.mkdir()
            idx = ai / '_index.md'
            idx.write_text('original')
            lock = idx.with_name('_index.md.lock')
            lock.write_text('')
            os.utime(lock, (time.time() - 30, time.time() - 30))
            for platform, operation in (
                ('cx', ('io.update(p,lambda _: "cleared")', '')),
                ('cc', ('', 'io.update(p,()=>"cleared")')),
            ):
                idx.write_text('original')
                lock.write_text('')
                os.utime(lock, (time.time() - 30, time.time() - 30))
                if platform == 'cx':
                    code = (
                        'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                        'import _index_io as io; p=Path(sys.argv[2]); io.update(p,lambda _: "cleared")'
                    )
                    run = subprocess.run(
                        [sys.executable, '-c', code, str(CX), str(idx)],
                        text=True, capture_output=True,
                    )
                else:
                    code = (
                        'const p=process.argv[2],io=require(process.argv[1]+"/_index-io.cjs");'
                        'io.update(p,()=>"cleared")'
                    )
                    run = subprocess.run(['node', '-e', code, str(CC), str(idx)], text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(idx.read_text(), 'cleared', platform)
                self.assertFalse(lock.exists(), platform)

    def test_light_ship_sees_untracked_source(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'README.md').write_text('# docs\n')
            subprocess.run(['git', '-C', str(repo), 'add', 'README.md'], check=True)
            subprocess.run(
                ['git', '-C', str(repo), '-c', 'user.name=Fixture',
                 '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'docs'],
                check=True,
            )
            subprocess.run(['git', '-C', str(repo), 'checkout', '-qb', 'topic'], check=True)
            subprocess.run(['git', '-C', str(repo), 'update-ref', 'refs/remotes/origin/topic', 'HEAD'], check=True)
            (repo / 'README.md').write_text('# docs\nmore\n')
            subprocess.run(['git', '-C', str(repo), 'add', 'README.md'], check=True)
            subprocess.run(
                ['git', '-C', str(repo), '-c', 'user.name=Fixture',
                 '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'more docs'],
                check=True,
            )
            gate = py_module('delivery-gate')
            self.assertTrue(gate.ship_change_is_light(repo))
            (repo / 'app.py').write_text('print("dirty")\n')
            self.assertFalse(gate.ship_change_is_light(repo))
            code = (
                'const m=require(process.argv[1]);'
                'process.stdout.write(String(m.shipChangeIsLight(process.argv[2])));'
            )
            run = subprocess.run(
                ['node', '-e', code, str(CC / 'delivery-gate.cjs'), str(repo)],
                text=True, capture_output=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, 'false')


class InstallRework(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')

    def cli(self, script, *args, env=None):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            capture_output=True, text=True, env=env or self.env,
        )

    def package(self, kind, version, label):
        package = self.base / label / ('.claude' if kind == 'cc' else '.codex')
        package.mkdir(parents=True)
        if kind == 'cc':
            (package / 'settings.json').write_text(json.dumps({
                'model': 'release-model',
                'permissions': {'deny': ['Agent(critic)', 'Agent(evaluator)', 'Agent(spec-compliance)']},
                'enabledPlugins': {'codex-plugin-cc@third-party-marketplace': False},
                'env': {'VIBECODING_ATHENA_VERSION': version},
                'hooks': {},
            }))
            (package / 'CLAUDE.md').write_text(version + '\n')
            for name in (
                'delivery-gate.cjs', '_review-binding.cjs', '_input-binding.cjs', 'pre-bash-guard.cjs',
            ):
                hook = package / 'hooks' / name
                hook.parent.mkdir(exist_ok=True)
                hook.write_text('// ' + name + '\n')
        else:
            (package / 'config.toml').write_text(
                'model = "release-model"\n[shell_environment_policy.set]\nVIBECODING_VERSION = "' + version + '"\n'
            )
            (package / 'hooks.json').write_text('{"hooks": {}}')
            (package / 'AGENTS.md').write_text(version + '\n')
            for name in ('delivery-gate.py', '_review_binding.py', '_input_binding.py'):
                hook = package / 'hooks' / name
                hook.parent.mkdir(exist_ok=True)
                hook.write_text('# ' + name + '\n')
            skill = package / 'skills/pace/scripts'
            skill.mkdir(parents=True)
            (skill / 'review-binding.py').write_text('print("ok")\n')
        return package

    def setup(self, kind, package, *args):
        return self.cli(SETUP, '--home', self.home, '--only', kind, '--' + kind + '-package', package, *args)

    def test_migrate_backup_survives_other_platform_install(self):
        backups = self.home / '.athena/backups'
        migrate = backups / 'old-cx-migrate'
        migrate.mkdir(parents=True)
        (migrate / 'transaction.json').write_text(json.dumps({
            'schema': 1, 'home': str(self.home), 'version': '9.9.8',
            'platforms': ['cx'], 'install_kind': 'migrate', 'files': [],
        }))
        result = self.setup('cc', self.package('cc', '9.9.9', 'cc'))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(migrate.exists())

    def test_same_platform_redeploy_prunes_only_matching_kind(self):
        result = self.setup('cc', self.package('cc', '9.9.9', 'cc'))
        self.assertEqual(result.returncode, 0, result.stderr)
        old = self.home / '.athena/backups/old-cc-redeploy'
        old.mkdir()
        (old / 'transaction.json').write_text(json.dumps({
            'schema': 1, 'home': str(self.home.resolve()), 'version': '9.9.9',
            'platforms': ['cc'], 'install_kind': 'redeploy', 'files': [],
        }))
        migrate = self.home / '.athena/backups/keep-migrate'
        migrate.mkdir()
        (migrate / 'transaction.json').write_text(json.dumps({
            'schema': 1, 'home': str(self.home.resolve()), 'version': '9.9.8',
            'platforms': ['cc'], 'install_kind': 'migrate', 'files': [],
        }))
        (self.home / '.claude/hooks/delivery-gate.cjs').unlink()
        result = self.setup('cc', self.package('cc', '9.9.9', 'cc-again'))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(old.exists())
        self.assertTrue(migrate.exists())

    def test_rollback_allows_missing_after_file(self):
        package = self.package('cx', '9.9.9', 'cx')
        config = self.home / '.codex/config.toml'
        config.parent.mkdir()
        original = 'model = "user-model"\n'
        config.write_text(original)
        result = self.setup('cx', package)
        self.assertEqual(result.returncode, 0, result.stderr)
        config.unlink()
        backup = next((self.home / '.athena/backups').iterdir())
        result = self.cli(SETUP, '--home', self.home, '--rollback', backup)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(config.read_text(), original)

    def test_incomplete_version_is_not_same(self):
        sys.path.insert(0, str(SETUP.parent))
        spec = importlib.util.spec_from_file_location('setup_athena', SETUP)
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        config = self.home / '.claude/settings.json'
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'env': {'VIBECODING_ATHENA_VERSION': '9.9.9'}}))
        self.assertEqual(setup.read_version('cc', self.home)[0], 'incomplete')

    def test_migrate_merges_managed_deny_and_plugin(self):
        old = self.package('cc', '9.9.8', 'cc-old')
        settings = json.loads((old / 'settings.json').read_text())
        settings['permissions'] = {'deny': ['Bash(rm -rf /)']}
        settings['enabledPlugins'] = {'codex-plugin-cc@third-party-marketplace': True}
        (old / 'settings.json').write_text(json.dumps(settings))
        shutil.copytree(old, self.home / '.claude', dirs_exist_ok=True)
        new = self.package('cc', '9.9.9', 'cc-new')
        result = self.setup('cc', new, '--migrate', '--baseline-cc-package', old)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads((self.home / '.claude/settings.json').read_text())
        self.assertIn('Agent(critic)', data['permissions']['deny'])
        self.assertEqual(data['enabledPlugins']['codex-plugin-cc@third-party-marketplace'], False)

    def test_init_reads_block_style_platforms(self):
        repo = self.base / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True, env=self.env)
        index = repo / '.ai_state/_index.md'
        index.parent.mkdir()
        index.write_text('---\nplatforms_enabled:\n  - cc\n  - cx\nstage: "impl"\n---\n')
        result = self.cli(INIT, '--repo', repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = index.read_text()
        self.assertIn('platforms_enabled: ["cc", "cx"]', text)
        self.assertNotIn('  - cc', text)
        self.assertIn('stage: "impl"', text)

    def test_auth_assignment_is_not_a_secret(self):
        repo = self.base / 'repo'
        repo.mkdir()
        for command in (
            ['git', 'init', '-q'],
            ['git', 'config', 'user.email', 'test@example.invalid'],
            ['git', 'config', 'user.name', 'Fixture'],
        ):
            subprocess.run(command, cwd=repo, check=True, env=self.env)
        (repo / 'app.py').write_text('print("base")\n')
        (repo / 'auth.py').write_text(
            'api_key = os.environ["API_KEY"]\npassword = getpass()\npassword = user.password_hash\n'
        )
        subprocess.run(['git', 'add', '.'], cwd=repo, check=True, env=self.env)
        subprocess.run(['git', 'commit', '-qm', 'base'], cwd=repo, check=True, env=self.env)
        bundle = self.base / 'ok.tgz'
        result = self.cli(RUNTIME, 'snapshot', '--repo', repo, '--output', bundle)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        with tarfile.open(bundle) as archive:
            self.assertIn('source/auth.py', archive.getnames())
        (repo / 'leaked.py').write_text('password = "super-secret-value"\n')
        subprocess.run(['git', 'add', 'leaked.py'], cwd=repo, check=True, env=self.env)
        bad = self.base / 'bad.tgz'
        result = self.cli(RUNTIME, 'snapshot', '--repo', repo, '--output', bad)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('excluded secret pattern: leaked.py', result.stderr)
        self.assertNotIn(b'super-secret-value', bad.read_bytes())

    def test_polish_worker_has_no_nested_isolation(self):
        text = (CC.parent / 'agents/polish-worker.md').read_text()
        self.assertNotRegex(text, r'(?m)^isolation:\s*worktree')


class PromptAndParity(unittest.TestCase):
    def test_cc_impl_allows_state_repair_but_blocks_source_and_stop(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            state = root / '.ai_state'
            state.mkdir()
            (state / '_index.md').write_text(
                '---\npath: "Feature"\nstage: "impl"\ncurrent_sprint_slug: "repair"\n---\n'
            )
            for event, file, blocked in (
                ('PreToolUse', state / 'sprints/repair/design.md', False),
                ('PreToolUse', root / 'app.py', True),
                ('Stop', root / 'app.py', True),
            ):
                with self.subTest(event=event, file=str(file)):
                    run = subprocess.run(
                        ['node', str(CC / 'delivery-gate.cjs')],
                        input=json.dumps({'cwd': str(root), 'hook_event_name': event,
                                          'tool_name': 'Write', 'tool_input': {'file_path': str(file)}}),
                        text=True, capture_output=True,
                    )
                    output = json.loads(run.stdout) if run.stdout.strip() else {}
                    self.assertEqual(output.get('decision') == 'block', blocked, run.stderr)

    def test_index_frontmatter_skips_indent_and_rejects_duplicates(self):
        gate = py_module('delivery-gate')
        text = '---\npath: "Feature"\nplatform_features:\n  path: "System"\n---\n'
        fm = gate.parse_frontmatter(text)
        self.assertEqual(fm['path'], 'Feature')
        with self.assertRaises(gate.GateError):
            gate.parse_frontmatter('---\npath: "Feature"\npath: "System"\n---\n')
        code = (
            'const m=require(process.argv[1]);'
            'try { m.parseFrontmatter(require("fs").readFileSync(0,"utf8")); process.exit(0); }'
            'catch (e) { process.stderr.write(e.message); process.exit(2); }'
        )
        run = subprocess.run(
            ['node', '-e', code, str(CC / 'delivery-gate.cjs')],
            input='---\npath: "Feature"\npath: "System"\n---\n',
            text=True, capture_output=True,
        )
        self.assertEqual(run.returncode, 2)
        self.assertIn('duplicate', run.stderr)

    def test_design_changed_blocks_ship(self):
        gate = py_module('delivery-gate')
        with tempfile.TemporaryDirectory() as raw:
            sprint = Path(raw)
            (sprint / 'design.md').write_text('old')
            reviews = sprint / 'reviews'
            reviews.mkdir()
            (reviews / 'implementation-review.md').write_text('PASS')
            os.utime(sprint / 'design.md', (time.time() + 10, time.time() + 10))
            with self.assertRaises(gate.GateError):
                gate.validate_design_contract(sprint, {'design_changed_after_impl': 'false'})
            os.utime(reviews / 'implementation-review.md', (time.time() + 20, time.time() + 20))
            gate.validate_design_contract(sprint, {'design_changed_after_impl': 'false'})
            with self.assertRaises(gate.GateError):
                gate.validate_design_contract(sprint, {'design_changed_after_impl': 'true'})

    def test_required_os_does_not_fake_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / 'repo'
            repo.mkdir()
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            for command in (
                ['git', 'init', '-q'],
                ['git', 'config', 'user.email', 'test@example.invalid'],
                ['git', 'config', 'user.name', 'Fixture'],
            ):
                subprocess.run(command, cwd=repo, check=True, env=env)
            (repo / 'app.py').write_text('print("ok")\n')
            subprocess.run(['git', 'add', '.'], cwd=repo, check=True, env=env)
            subprocess.run(['git', 'commit', '-qm', 'base'], cwd=repo, check=True, env=env)
            bundle = base / 'in.tgz'
            subprocess.run(
                [sys.executable, str(RUNTIME), 'snapshot', '--repo', str(repo), '--output', str(bundle)],
                check=True, env=env, capture_output=True, text=True,
            )
            scenario = base / 'scenario.json'
            scenario.write_text(json.dumps({
                'name': 'os', 'command': ['python3', 'app.py'], 'required_os': 'DoesNotExistOS',
            }))
            (base / 'design.md').write_text('AC1: os must match\n')
            output = base / 'result.json'
            run = subprocess.run(
                [sys.executable, str(RUNTIME), 'run', '--bundle', str(bundle),
                 '--contract', str(base / 'design.md'), '--scenario', str(scenario), '--output', str(output)],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(run.returncode, 0)
            result = json.loads(output.read_text())
            self.assertEqual(result['status'], 'environment_unsatisfied')
            self.assertNotEqual(result['status'], 'passed')

    def test_cc_rules_declare_native_paths(self):
        rules = CC.parent / 'rules'
        for name in ('coding-standards.md', 'doc-style.md', 'security-checklist.md'):
            text = (rules / name).read_text()
            self.assertIn('paths:', text.split('---', 2)[1])


if __name__ == '__main__':
    unittest.main()
