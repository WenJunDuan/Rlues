import unittest
from gate_harness import GATE, athena, project, tmpdir, GOOD_DESIGN, check_file
from test_gate_evidence import records

class ExecutionEnvironment(unittest.TestCase):
    def test_inline_and_export_runner_environment_is_unprovable(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        target = check_file(root)
        for name in ('npm_config_script_shell', 'UV_PROJECT_ENVIRONMENT', 'UV_NO_SYNC', 'POETRY_ACTIVE',
                     'PIPENV_IGNORE_VIRTUALENVS', 'HATCH_ENV', 'VIRTUAL_ENV', 'GOFLAGS', 'RUSTC_WRAPPER',
                     'CARGO_TARGET_DIR', 'GRADLE_USER_HOME', 'MAVEN_ARGS', 'NODE_OPTIONS'):
            value = '' if name == 'NODE_OPTIONS' else '1'
            for command in (f'{name}={value} node --test {target}', f'export {name}=; node --test {target}'):
                with self.subTest(command=command):
                    run = athena('run', '--', command, cwd=root)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertFalse(records(root)[-1]['provable'])

    def test_explicit_runner_families_and_baseline_rejections(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        target = check_file(root)
        for name in ('UV_NO_SYNC', 'POETRY_ACTIVE', 'PIPENV_IGNORE_VIRTUALENVS', 'HATCH_ENV', 'VIRTUAL_ENV',
                     'GOFLAGS', 'RUSTC_WRAPPER', 'CARGO_TARGET_DIR', 'GRADLE_USER_HOME', 'MAVEN_ARGS',
                     'NODE_ENV', 'DATA_SRC', 'PATH', 'PYTHONPATH', 'npm_config_script_shell'):
            run = athena('run', '--env', f'{name}=', '--', 'node', '--test', target, cwd=root)
            # Empty PATH cannot find node, still cannot prove.
            self.assertFalse(records(root)[-1]['provable'], name)

    def test_pat_dsn_and_empty_username_url_are_rejected(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        for assignment in ('GITHUB_PAT=fixture', 'SENTRY_DSN=fixture', 'SERVICE_URL=redis://:fixture@h'):
            run = athena('run', '--env', assignment, '--', 'node', '--test', check_file(root), cwd=root)
            self.assertEqual(run.returncode, 2, assignment)
            self.assertIn('像凭据', run.stderr)

    def test_monorepo_runs_per_package_and_preserves_zero_rejection(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        sub = root / 'packages/one'; sub.mkdir(parents=True)
        run = athena('run', '--', 'node', '--test', check_file(root), cwd=sub)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(records(root)[-1]['provable'])
        self.assertEqual(records(root)[-1]['cwd'], 'packages/one')
        self.assertIn('按包分跑', (GATE.parent / 'core/package/skills/pace/references/gates.md').read_text())
