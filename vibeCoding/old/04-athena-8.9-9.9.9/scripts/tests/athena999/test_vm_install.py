"""9.9.9 install and runtime boundary regressions; never use the real HOME/VM."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[6]
CX = ROOT / 'vibeCoding/old/04-athena-8.9-9.9.9/codex/9.9.9/.codex/skills'
CC = ROOT / 'vibeCoding/old/04-athena-8.9-9.9.9/claude/9.9.9/.claude/skills'
RUNTIME = CX / 'athena-vm/scripts/runtime-run.py'
SETUP = CX / 'athena-setup/scripts/setup-athena.py'
INIT = CX / 'athena-init/scripts/init-platforms.py'
CONFIGURE = CX / 'athena-vm/scripts/configure-vm.py'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')

    def cli(self, script, *args, env=None):
        return subprocess.run([sys.executable, str(script), *map(str, args)],
                              capture_output=True, text=True, env=env or self.env)

    def repo(self):
        repo = self.base / 'repo'
        repo.mkdir()
        for command in (['git', 'init', '-q'], ['git', 'config', 'user.email', 'test@example.invalid'],
                        ['git', 'config', 'user.name', 'Fixture']):
            subprocess.run(command, cwd=repo, check=True, env=self.env)
        (repo / 'app.py').write_text('print("base")\n')
        (repo / 'gone.txt').write_text('delete me')
        (repo / '.gitignore').write_text('ignored.txt\n')
        subprocess.run(['git', 'add', '.'], cwd=repo, check=True, env=self.env)
        subprocess.run(['git', 'commit', '-qm', 'base'], cwd=repo, check=True, env=self.env)
        return repo

    def snapshot(self, repo, *args):
        bundle = self.base / 'input.tar.gz'
        result = self.cli(RUNTIME, 'snapshot', '--repo', repo, '--output', bundle, *args)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return bundle

    def scenario(self, **overrides):
        scenario = {'name': 'smoke', 'command': ['python3', 'app.py']}
        scenario.update(overrides)
        path = self.base / 'scenario.json'
        path.write_text(json.dumps(scenario))
        return path

    def run_bundle(self, bundle, scenario, *args):
        contract = self.base / 'design.md'
        if not contract.exists():
            contract.write_text('AC1: app prints tested content\n')
        output = self.base / 'result.json'
        process = self.cli(RUNTIME, 'run', '--bundle', bundle, '--contract', contract,
                           '--scenario', scenario, '--output', output, *args)
        self.assertTrue(output.exists(), process.stderr + process.stdout)
        return process, json.loads(output.read_text())


class RuntimeTests(Fixture):
    def test_interruption_returns_result_and_cleans_owned_run(self):
        repo = self.repo()
        bundle = self.snapshot(repo)
        ready = self.base / 'started'
        scenario = self.scenario(command=['python3', '-c', 'import time; from pathlib import Path; '
                                  f'Path({str(ready)!r}).touch(); time.sleep(60)'])
        contract, output = self.base / 'design.md', self.base / 'interrupted-result.json'
        contract.write_text('AC: interrupt is recoverable')
        process = subprocess.Popen([sys.executable, str(RUNTIME), 'run', '--bundle', str(bundle),
                  '--scenario', str(scenario), '--contract', str(contract), '--output', str(output)],
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self.env)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists())
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            self.assertTrue(output.exists(), stdout + stderr)
            result = json.loads(output.read_text())
            self.assertEqual(result['status'], 'interrupted')
            self.assertEqual(result['cleanup']['status'], 'passed')
            self.assertFalse(Path(result['resource_root']).exists())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_malformed_manifest_types_return_structured_input_rejection(self):
        for value in [3, 'bad', [], {'schema': 1, 'files': None, 'manifest_sha256': 'bad'}]:
            archive_path = self.base / 'malformed.tgz'
            with tarfile.open(archive_path, 'w:gz') as archive:
                payload = json.dumps(value).encode()
                member = tarfile.TarInfo('manifest.json')
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            process, result = self.run_bundle(archive_path, self.scenario())
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(result['status'], 'input_invalid')
            self.assertNotIn('Traceback', process.stderr)

    def test_archive_traversal_and_corrupted_manifest_are_rejected(self):
        repo = self.repo()
        bundle = self.snapshot(repo)
        for label, path_name in [('traversal', 'source/../outside'), ('absolute', '/outside')]:
            altered = self.base / (label + '.tgz')
            with tarfile.open(bundle) as source, tarfile.open(altered, 'w:gz') as target:
                for member in source.getmembers():
                    payload = source.extractfile(member)
                    if member.name == 'source/app.py':
                        member.name = path_name
                    target.addfile(member, payload)
            process, result = self.run_bundle(altered, self.scenario())
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(result['status'], 'input_invalid')
        self.assertFalse((self.base / 'outside').exists())
        altered = self.base / 'corrupt-manifest.tgz'
        with tarfile.open(bundle) as source, tarfile.open(altered, 'w:gz') as target:
            for member in source.getmembers():
                payload = source.extractfile(member).read()
                if member.name == 'manifest.json':
                    manifest = json.loads(payload)
                    manifest['base_commit'] = 'changed-without-rehash'
                    payload = json.dumps(manifest).encode()
                    member.size = len(payload)
                target.addfile(member, io.BytesIO(payload))
        process, result = self.run_bundle(altered, self.scenario())
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result['status'], 'input_invalid')

    def test_prepare_services_survive_until_run_and_owned_processes_are_cleaned(self):
        repo = self.repo()
        (repo / 'prepare.py').write_text('import os, subprocess\nfrom pathlib import Path\n'
              'p = subprocess.Popen(["python3", "-c", "import time; time.sleep(60)"])\n'
              'Path("owned.pid").write_text(str(p.pid))\n')
        (repo / 'check.py').write_text('import os\nfrom pathlib import Path\n'
              'pid = int(Path("owned.pid").read_text())\nos.kill(pid, 0)\nprint(pid)\n')
        bundle = self.snapshot(repo, '--allow-untracked', 'prepare.py', '--allow-untracked', 'check.py')
        process, result = self.run_bundle(bundle, self.scenario(prepare=['python3', 'prepare.py'],
                                               command=['python3', 'check.py']))
        self.assertEqual(process.returncode, 0, json.dumps(result))
        pid = int(result['steps'][-1]['stdout'])
        # A reaped or zombie child is stopped; no live fixture process may survive.
        state = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
        self.assertTrue(not state or state.startswith('Z'), state)

    def test_teardown_failure_is_not_a_pass(self):
        bundle = self.snapshot(self.repo())
        process, result = self.run_bundle(bundle, self.scenario(teardown=['python3', '-c', 'raise SystemExit(3)']))
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result['status'], 'teardown_failed')
        self.assertEqual(result['cleanup']['status'], 'failed')
        self.assertFalse(Path(result['resource_root']).exists())

    def test_final_worktree_and_allowlist_are_the_only_transferred_inputs(self):
        repo = self.repo()
        (repo / 'app.py').write_text('print("staged")\n')
        subprocess.run(['git', 'add', 'app.py'], cwd=repo, check=True, env=self.env)
        (repo / 'app.py').write_text('print("final dirty")\n')
        (repo / 'gone.txt').unlink()
        (repo / 'allowed.txt').write_text('explicit')
        (repo / 'other.txt').write_text('not explicit')
        (repo / 'ignored.txt').write_text('ignored')
        (repo / '.env').write_text('PASSWORD=never-transfer-this')
        bundle = self.snapshot(repo, '--allow-untracked', 'allowed.txt')
        with tarfile.open(bundle) as archive:
            names = archive.getnames()
            self.assertIn('source/allowed.txt', names)
            self.assertNotIn('source/other.txt', names)
            self.assertNotIn('source/.env', names)
            manifest = json.load(archive.extractfile('manifest.json'))
            self.assertTrue(any(row['path'] == 'gone.txt' and row['type'] == 'deleted'
                                for row in manifest['files']))
        process, result = self.run_bundle(bundle, self.scenario())
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(result['status'], 'passed')
        self.assertIn('final dirty', result['steps'][-1]['stdout'])
        self.assertTrue(result['input_manifest_sha256'])
        self.assertTrue(result['contract_sha256'])
        self.assertEqual(result['cleanup']['status'], 'passed')
        self.assertFalse(Path(result['resource_root']).exists())

    def test_tracked_secrets_excluded_and_required_secret_blocks(self):
        repo = self.repo()
        (repo / 'credentials.json').write_text('{"password":"fixture-secret"}')
        subprocess.run(['git', 'add', 'credentials.json'], cwd=repo, check=True, env=self.env)
        bundle = self.snapshot(repo)
        self.assertNotIn(b'fixture-secret', bundle.read_bytes())
        result = self.cli(RUNTIME, 'snapshot', '--repo', repo, '--output', self.base / 'bad.tgz',
                          '--required-input', 'credentials.json')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('fixture-secret', result.stdout + result.stderr)

    def test_symlink_escape_and_receiver_extra_file_are_rejected(self):
        repo = self.repo()
        (repo / 'escape').symlink_to('../outside')
        result = self.cli(RUNTIME, 'snapshot', '--repo', repo, '--output', self.base / 'bad.tgz',
                          '--allow-untracked', 'escape')
        self.assertNotEqual(result.returncode, 0)
        (repo / 'escape').unlink()
        bundle = self.snapshot(repo)
        mutated = self.base / 'extra.tar.gz'
        with tarfile.open(bundle) as source, tarfile.open(mutated, 'w:gz') as target:
            for member in source.getmembers():
                target.addfile(member, source.extractfile(member) if member.isfile() else None)
            extra = tarfile.TarInfo('source/extra.py')
            extra.size = 8
            target.addfile(extra, io.BytesIO(b'print(1)'))
        process, result = self.run_bundle(mutated, self.scenario())
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result['status'], 'input_invalid')

    def test_ready_failure_prevents_scenario_and_timeout_runs_cleanup(self):
        repo = self.repo()
        bundle = self.snapshot(repo)
        process, result = self.run_bundle(bundle, self.scenario(ready=['python3', '-c', 'raise SystemExit(4)']))
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result['scenario']['status'], 'not_ready')
        self.assertFalse(any(step['name'] == 'command' for step in result['steps']))
        marker = self.base / 'teardown-called'
        scenario = self.scenario(command=['python3', '-c', 'import time; time.sleep(30)'],
                                 teardown=['python3', '-c', f'from pathlib import Path; Path({str(marker)!r}).touch()'])
        process, result = self.run_bundle(bundle, scenario, '--timeout', '0.2')
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result['status'], 'timed_out')
        self.assertTrue(marker.exists())
        self.assertEqual(result['cleanup']['status'], 'passed')

    def test_transport_failure_is_distinct_for_required_and_advisory(self):
        repo = self.repo()
        bundle = self.snapshot(repo)
        config = self.base / 'vm.json'
        config.write_text(json.dumps({'version': 1, 'vms': [{'name': 'fixture', 'host': '127.0.0.1',
                              'port': 1, 'user': 'fixture', 'auth': {'method': 'key'},
                              'workdir': '/tmp/athena-fixture'}]}))
        config.chmod(0o600)
        for requirement in ('required', 'advisory'):
            process, result = self.run_bundle(bundle, self.scenario(), '--runner', 'ssh', '--vm',
                             'fixture', '--config', config, '--requirement', requirement, '--timeout', '1')
            self.assertEqual(result['configured']['status'], 'passed')
            self.assertEqual(result['transport']['status'], 'failed')
            self.assertEqual(result['scenario']['status'], 'not_run')
            self.assertEqual(result['status'], 'transport_failed')
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(result['blocks_delivery'], requirement == 'required')

    def test_contract_changes_binding_and_no_vm_local_is_complete(self):
        repo = self.repo()
        bundle = self.snapshot(repo)
        _, before = self.run_bundle(bundle, self.scenario())
        (self.base / 'design.md').write_text('AC1: changed requirement\n')
        _, after = self.run_bundle(bundle, self.scenario())
        self.assertNotEqual(before['contract_sha256'], after['contract_sha256'])
        self.assertEqual(after['transport']['status'], 'passed')
        self.assertEqual(after['runner'], 'local')


class InstallTests(Fixture):
    def package(self, kind, version, label):
        package = self.base / label / ('.claude' if kind == 'cc' else '.codex')
        package.mkdir(parents=True)
        config = ({'model': 'release-model', 'effortLevel': 'high', 'permissions': {'defaultMode': 'default'},
                   'env': {'VIBECODING_ATHENA_VERSION': version}, 'hooks': {}} if kind == 'cc' else None)
        if kind == 'cc':
            (package / 'settings.json').write_text(json.dumps(config))
        else:
            (package / 'config.toml').write_text('model = "release-model"\nmodel_reasoning_effort = "high"\n'
                 '[shell_environment_policy.set]\nVIBECODING_VERSION = "' + version + '"\n')
            (package / 'hooks.json').write_text('{"hooks": {}}')
        (package / ('CLAUDE.md' if kind == 'cc' else 'AGENTS.md')).write_text(version + '\n')
        skill = package / 'skills/athena-demo'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(version + ' demo\n')
        return package

    def setup(self, kind, package, *args, env=None):
        return self.cli(SETUP, '--home', self.home, '--only', kind, '--' + kind + '-package', package, *args, env=env)

    def test_single_platform_fresh_and_user_config_are_preserved(self):
        for kind in ('cc', 'cx'):
            package = self.package(kind, '9.9.9', kind)
            endpoint = self.home / ('.claude' if kind == 'cc' else '.codex')
            endpoint.mkdir(exist_ok=True)
            config = endpoint / ('settings.json' if kind == 'cc' else 'config.toml')
            if kind == 'cc':
                config.write_text(json.dumps({'model': 'user-model', 'effortLevel': 'low',
                    'permissions': {'defaultMode': 'plan'}, 'hooks': {'Stop': [{'hooks': [{'command': 'third-party'}]}]}}))
            else:
                config.write_text('model = "user-model"\nmodel_provider = "custom"\nmodel_reasoning_effort = "low"\n'
                                  'approval_policy = "on-request"\n# user comment\n')
            result = self.setup(kind, package)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn('user-model', config.read_text())
            self.assertIn('low', config.read_text())
            self.assertIn('9.9.9', config.read_text())
            self.assertIn('third-party' if kind == 'cc' else '# user comment', config.read_text())

    def test_migration_preserves_user_assets_and_rolls_back(self):
        for kind in ('cc', 'cx'):
            old = self.package(kind, '9.9.8', kind + '-old')
            new = self.package(kind, '9.9.9', kind + '-new')
            endpoint = self.home / ('.claude' if kind == 'cc' else '.codex')
            import shutil
            shutil.copytree(old, endpoint, dirs_exist_ok=True)
            target_skill = self.home / ('.claude/skills/athena-demo/SKILL.md' if kind == 'cc'
                                       else '.agents/skills/athena-demo/SKILL.md')
            target_skill.parent.mkdir(parents=True, exist_ok=True)
            target_skill.write_text('user override\n')
            prompt = endpoint / ('CLAUDE.md' if kind == 'cc' else 'AGENTS.md')
            result = self.setup(kind, new, '--migrate', '--baseline-' + kind + '-package', old)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(target_skill.read_text(), 'user override\n')
            self.assertEqual(prompt.read_text(), '9.9.9\n')
            backups = sorted((self.home / '.athena/backups').iterdir())
            result = self.cli(SETUP, '--home', self.home, '--rollback', backups[-1])
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(prompt.read_text(), '9.9.8\n')
            self.assertEqual(target_skill.read_text(), 'user override\n')

    def test_failed_transaction_restores_existing_config(self):
        package = self.package('cx', '9.9.9', 'cx')
        config = self.home / '.codex/config.toml'
        config.parent.mkdir()
        original = 'model = "user-model"\n'
        config.write_text(original)
        result = self.setup('cx', package, env=dict(self.env, ATHENA_TEST_FAIL_AT='asset-copy'))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(config.read_text(), original)
        self.assertFalse((self.home / '.codex/AGENTS.md').exists())

    def test_init_only_probes_selected_platform_and_caches(self):
        repo = self.repo()
        binary = self.base / 'bin'
        binary.mkdir()
        calls = self.base / 'calls'
        for name in ('claude', 'codex'):
            script = binary / name
            script.write_text('#!/bin/sh\necho ' + name + ' >> ' + str(calls) + '\necho ' + name + ' 1.0.0\n')
            script.chmod(0o755)
        env = dict(self.env, PATH=str(binary) + os.pathsep + self.env['PATH'])
        template = self.base / 'index-template.md'
        template.write_text('---\nplatforms_enabled: ["both"]\ncc_version: ""\ncx_version: ""\n---\n')
        for _ in range(2):
            result = self.cli(INIT, '--repo', repo, '--platforms', 'cx', '--template', template, env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(calls.read_text().splitlines(), ['codex'])
        self.assertIn('platforms_enabled: ["cx"]', (repo / '.ai_state/_index.md').read_text())

    def test_init_legacy_both_is_normalized_without_changing_other_state(self):
        repo = self.repo()
        index = repo / '.ai_state/_index.md'
        index.parent.mkdir()
        index.write_text('---\nplatforms_enabled: ["both"]\nstage: "impl"\ncustom: "keep"\n---\n')
        result = self.cli(INIT, '--repo', repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('platforms_enabled: ["cc", "cx"]', index.read_text())
        self.assertIn('stage: "impl"', index.read_text())
        self.assertIn('custom: "keep"', index.read_text())

    def test_rollback_refuses_later_user_edit_without_partial_write(self):
        package = self.package('cx', '9.9.9', 'cx')
        result = self.setup('cx', package)
        self.assertEqual(result.returncode, 0, result.stderr)
        prompt = self.home / '.codex/AGENTS.md'
        prompt.write_text('later user edit')
        backup = next((self.home / '.athena/backups').iterdir())
        result = self.cli(SETUP, '--home', self.home, '--rollback', backup)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(prompt.read_text(), 'later user edit')
        self.assertTrue((self.home / '.codex/config.toml').exists())

    def test_dry_run_and_unselected_endpoint_are_zero_write(self):
        package = self.package('cx', '9.9.9', 'cx')
        other = self.home / '.claude/settings.json'
        other.parent.mkdir()
        other.write_text('not even valid JSON; unselected')
        result = self.setup('cx', package, '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / '.codex').exists())
        result = self.setup('cx', package)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(other.read_text(), 'not even valid JSON; unselected')


class InitConcurrencyTests(Fixture):
    """Use actual native index writers while CLI discovery is paused."""

    def writer(self, index, content, use_node):
        if use_node:
            command = ['node', '-e', 'const fs=require("fs"), io=require(process.argv[1]); '
                       'if(io.update(process.argv[2],()=>fs.readFileSync(0,"utf8"))===null) process.exit(2);',
                       str(CC.parents[0] / 'hooks/_index-io.cjs'), str(index)]
        else:
            command = [sys.executable, '-c', 'import sys; from pathlib import Path; '
                       'sys.path.insert(0,sys.argv[1]); import _index_io; '
                       'result=_index_io.update(Path(sys.argv[2]),lambda _:sys.stdin.read()); '
                       'raise SystemExit(2 if result is None else 0)',
                       str(CX.parents[0] / 'hooks'), str(index)]
        result = subprocess.run(command, input=content, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def paused_init(self, repo, script, selected):
        binary = self.base / 'bin'
        binary.mkdir(exist_ok=True)
        started, resume = self.base / 'started', self.base / 'resume'
        started.unlink(missing_ok=True)
        resume.unlink(missing_ok=True)
        executable = binary / ('claude' if selected == 'cc' else 'codex')
        executable.write_text('#!' + sys.executable + '\nfrom pathlib import Path\nimport time\n'
             f'Path({str(started)!r}).touch()\nend=time.monotonic()+10\n'
             f'while not Path({str(resume)!r}).exists() and time.monotonic()<end: time.sleep(0.01)\n'
             'print("fixture-cli 1.2.3")\n')
        executable.chmod(0o755)
        template = self.base / 'template.md'
        template.write_text('---\nplatforms_enabled: ["both"]\nstage: "impl"\n---\n')
        process = subprocess.Popen([sys.executable, str(script), '--repo', str(repo), '--platforms',
                       selected, '--template', str(template), '--refresh'], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True,
                       env=dict(self.env, PATH=str(binary) + os.pathsep + self.env['PATH']))
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        deadline = time.monotonic() + 5
        while not started.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(started.exists(), 'init never reached selected CLI probe')
        return process, resume

    def test_probe_does_not_overwrite_concurrent_stage_or_body(self):
        repo = self.repo()
        index = repo / '.ai_state/_index.md'
        index.parent.mkdir()
        for selected, script in [('cx', INIT), ('cc', CC / 'athena-init/scripts/init-platforms.py')]:
            with self.subTest(platform=selected):
                content = '---\nplatforms_enabled: ["' + selected + '"]\nstage: "impl"\n---\n'
                index.write_text(content)
                process, resume = self.paused_init(repo, script, selected)
                latest = content.replace('"impl"', '"review"') + '\nplatform_features:\n  cc_body_example: true\n'
                self.writer(index, latest, use_node=selected == 'cx')
                resume.touch()
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stdout + stderr)
                actual = index.read_text()
                self.assertIn('stage: "review"', actual)
                self.assertIn('  cc_body_example: true', actual)
                self.assertIn(selected + '_version: "fixture-cli 1.2.3"', actual)

    def test_changed_intent_rejects_probe_and_preserves_new_cache(self):
        repo = self.repo()
        index = repo / '.ai_state/_index.md'
        index.parent.mkdir()
        cache = index.parent / '.runtime/platform-capabilities.json'
        for selected, script in [('cx', INIT), ('cc', CC / 'athena-init/scripts/init-platforms.py')]:
            with self.subTest(platform=selected):
                content = '---\nplatforms_enabled: ["' + selected + '"]\nstage: "impl"\n---\n'
                index.write_text(content)
                process, resume = self.paused_init(repo, script, selected)
                other = 'cc' if selected == 'cx' else 'cx'
                latest = content.replace('["' + selected + '"]', '["' + other + '"]').replace('"impl"', '"review"')
                self.writer(index, latest, use_node=selected == 'cx')
                cache.parent.mkdir(exist_ok=True)
                expected_cache = json.dumps({other: {'version': 'newer observation'}})
                cache.write_text(expected_cache)
                resume.touch()
                stdout, stderr = process.communicate(timeout=5)
                self.assertNotEqual(process.returncode, 0, stdout + stderr)
                self.assertIn('intent changed', stderr)
                self.assertEqual(index.read_text(), latest)
                self.assertEqual(cache.read_text(), expected_cache)

    def test_first_creation_preserves_index_created_during_probe(self):
        repo = self.repo()
        for selected, script in [('cx', INIT), ('cc', CC / 'athena-init/scripts/init-platforms.py')]:
            with self.subTest(platform=selected):
                import shutil
                shutil.rmtree(repo / '.ai_state', ignore_errors=True)
                process, resume = self.paused_init(repo, script, selected)
                index = repo / '.ai_state/_index.md'
                index.parent.mkdir(exist_ok=True)
                # Another initializer commits through the actual native lock.
                index.write_text('---\nplatforms_enabled: ["' + selected + '"]\n---\n')
                latest = '---\nplatforms_enabled: ["' + selected + '"]\nstage: "review"\ncustom: "keep"\n---\n'
                self.writer(index, latest, use_node=selected == 'cx')
                resume.touch()
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stdout + stderr)
                self.assertIn('stage: "review"', index.read_text())
                self.assertIn('custom: "keep"', index.read_text())

    def test_shared_lock_timeout_is_nonzero_and_does_not_create_or_overwrite(self):
        repo = self.repo()
        index = repo / '.ai_state/_index.md'
        index.parent.mkdir()
        template = self.base / 'template.md'
        template.write_text('---\nplatforms_enabled: ["both"]\n---\n')
        lock = index.with_name('_index.md.lock')
        lock.write_text('held by another writer')
        for script in [INIT, CC / 'athena-init/scripts/init-platforms.py']:
            for existing in [False, True]:
                with self.subTest(script=str(script), existing=existing):
                    if existing:
                        index.write_text('---\nstage: "review"\nplatforms_enabled: ["cx"]\n---\n')
                    else:
                        index.unlink(missing_ok=True)
                    before = index.read_bytes() if existing else None
                    result = self.cli(script, '--repo', repo, '--platforms', 'cx', '--template', template)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('lock', result.stderr)
                    self.assertEqual(index.read_bytes() if index.exists() else None, before)
                    self.assertFalse((index.parent / '.runtime/platform-capabilities.json').exists())
                    self.assertEqual(lock.read_text(), 'held by another writer')

    def test_installed_cx_uses_own_native_writer_and_repeat_is_zero_write(self):
        import shutil
        repo = self.repo()
        installed = self.home / '.agents/skills/athena-init/scripts/init-platforms.py'
        installed.parent.mkdir(parents=True)
        shutil.copy2(INIT, installed)
        hooks = self.home / '.codex/hooks'
        hooks.mkdir(parents=True)
        shutil.copy2(CX.parents[0] / 'hooks/_index_io.py', hooks / '_index_io.py')
        template = self.base / 'template.md'
        template.write_text('---\nplatforms_enabled: ["both"]\n---\n')
        env = dict(self.env, CODEX_HOME=str(self.home / '.codex'))
        result = self.cli(installed, '--repo', repo, '--platforms', 'cx', '--template', template, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = [repo / '.ai_state/_index.md', repo / '.ai_state/.runtime/platform-capabilities.json']
        before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]
        result = self.cli(installed, '--repo', repo, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([(path.read_bytes(), path.stat().st_mtime_ns) for path in paths], before)


class FirstUseTests(Fixture):
    def fake_binaries(self):
        binary = self.base / 'bin'
        binary.mkdir(exist_ok=True)
        for name in ['claude', 'codex']:
            path = binary / name
            path.write_text('#!/bin/sh\necho fixture-cli-1.0\n')
            path.chmod(0o755)
        return dict(self.env, PATH=str(binary) + os.pathsep + self.env['PATH'])

    def test_standalone_package_without_old_release_installs_and_initializes(self):
        import shutil
        for kind, source in [('cc', CC.parent), ('cx', CX.parent)]:
            with self.subTest(platform=kind):
                isolated = self.base / ('standalone-' + kind)
                package = isolated / source.name
                shutil.copytree(source, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                target_home = isolated / 'first-home'
                target_home.mkdir()
                history = target_home / source.name / 'sessions/prior.jsonl'
                history.parent.mkdir(parents=True)
                history.write_text('existing conversation\n')
                third_party = target_home / ('.claude/skills/custom' if kind == 'cc' else '.agents/skills/custom') / 'SKILL.md'
                third_party.parent.mkdir(parents=True)
                third_party.write_text('user skill\n')
                env = dict(self.fake_binaries(), HOME=str(target_home), CODEX_HOME=str(target_home / '.codex'))
                env.pop('ATHENA_CC_PKG', None)
                env.pop('ATHENA_CX_PKG', None)
                result = subprocess.run([sys.executable, str(package / 'skills/athena-setup/scripts/setup-athena.py'),
                            '--home', str(target_home), '--only', kind, '--' + kind + '-package', str(package)],
                            cwd=isolated, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(str(ROOT), result.stdout)
                self.assertFalse((target_home / '.athena/vm.json').exists())
                self.assertEqual(history.read_text(), 'existing conversation\n')
                self.assertEqual(third_party.read_text(), 'user skill\n')
                installed_skills = target_home / ('.claude/skills' if kind == 'cc' else '.agents/skills')
                # Inspect all shipped helper/reference/template bytes, not just SKILL.md names.
                for asset in (package / 'skills').rglob('*'):
                    if asset.is_file():
                        installed = installed_skills / asset.relative_to(package / 'skills')
                        self.assertTrue(installed.is_file(), str(installed))
                        self.assertEqual(installed.read_bytes(), asset.read_bytes())
                project = isolated / 'project'
                project.mkdir()
                subprocess.run(['git', 'init', '-q'], cwd=project, env=env, check=True)
                result = subprocess.run([sys.executable, str(installed_skills / 'athena-init/scripts/init-platforms.py'),
                              '--repo', str(project), '--platforms', kind], cwd=project, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('platforms_enabled: ["' + kind + '"]', (project / '.ai_state/_index.md').read_text())
                result = subprocess.run([sys.executable, str(installed_skills / 'athena-vm/scripts/runtime-run.py'),
                              'doctor', '--runner', 'local'], cwd=project, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['scenario']['status'], 'not_run')
                result = subprocess.run([sys.executable, str(installed_skills / 'athena-vm/scripts/configure-vm.py'),
                              '--help'], cwd=project, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_vm_config_can_be_created_without_claiming_transport(self):
        result = self.cli(CONFIGURE, '--name', 'dev', '--host', 'example.invalid', '--user', 'fixture',
                          '--workdir', '/tmp/athena-fixture')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.home / '.athena/vm.json'
        data = json.loads(path.read_text())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(data['version'], 1)
        self.assertEqual(data['vms'][0]['auth'], {'method': 'key'})
        summary = json.loads(result.stdout)
        self.assertEqual(summary['configured']['status'], 'passed')
        self.assertEqual(summary['transport']['status'], 'not_run')
        self.assertEqual(summary['scenario']['status'], 'not_run')
        before = path.read_bytes()
        result = self.cli(CONFIGURE, '--name', 'dev', '--host', 'changed.invalid', '--user', 'fixture',
                          '--workdir', '/tmp/changed')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), before)

    def test_alias_configuration_preserves_other_targets_and_uses_alias(self):
        config = self.home / '.athena/vm.json'
        config.parent.mkdir()
        existing = {'version': 1, 'custom': {'keep': True}, 'vms': [{'name': 'other', 'custom': 'keep'}]}
        config.write_text(json.dumps(existing))
        config.chmod(0o600)
        binary = self.base / 'bin'
        binary.mkdir()
        calls = self.base / 'ssh-calls'
        fake_ssh = binary / 'ssh'
        fake_ssh.write_text('#!' + sys.executable + '\nimport sys,json\nfrom pathlib import Path\n'
                    f'with Path({str(calls)!r}).open("a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n'
                    'if sys.argv[1:]==["-G","my-existing-alias"]:\n'
                    ' print("hostname example.invalid\\nuser fixture\\nport 2222\\nidentityfile ~/.ssh/existing")\n'
                    'else:\n print(json.dumps({"system":"Linux","release":"fixture","machine":"x86_64","python":"3.12"}))\n')
        fake_ssh.chmod(0o755)
        env = dict(self.env, PATH=str(binary) + os.pathsep + self.env['PATH'])
        result = self.cli(CONFIGURE, '--name', 'dev', '--ssh-alias', 'my-existing-alias',
                          '--workdir', '/tmp/athena-fixture', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(config.read_text())
        self.assertEqual(actual['custom'], existing['custom'])
        self.assertEqual(actual['vms'][0], existing['vms'][0])
        target = actual['vms'][1]
        self.assertEqual(target['ssh_alias'], 'my-existing-alias')
        self.assertEqual(target['host'], 'example.invalid')
        self.assertEqual(target['user'], 'fixture')
        self.assertEqual(target['port'], 2222)
        self.assertEqual(len(calls.read_text().splitlines()), 1)
        result = self.cli(RUNTIME, 'doctor', '--runner', 'ssh', '--vm', 'dev', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        ssh_args = json.loads(calls.read_text().splitlines()[-1])
        self.assertEqual(ssh_args[-2], 'my-existing-alias')
        self.assertNotIn('-p', ssh_args)

    def test_configure_dry_run_and_invalid_existing_secret_are_zero_write(self):
        arguments = ['--name', 'dev', '--host', 'example.invalid', '--user', 'fixture', '--workdir', '/tmp/run']
        result = self.cli(CONFIGURE, *arguments, '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / '.athena').exists())
        config = self.home / '.athena/vm.json'
        config.parent.mkdir()
        original = json.dumps({'version': 1, 'vms': [{'name': 'old', 'password': 'do-not-print-me'}]})
        config.write_text(original)
        config.chmod(0o600)
        result = self.cli(CONFIGURE, *arguments)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('do-not-print-me', result.stdout + result.stderr)
        self.assertEqual(config.read_text(), original)


if __name__ == '__main__':
    unittest.main()
