"""Placeholder vs real-secret discrimination for runtime-run.py (A) and _input-binding (C).

Every fixture is driven through both native implementations; judgements must agree.
Placeholder bodies are all >= 12 characters so they reach the quoted SECRET branch.
"""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[4]
VIBE = REPO / 'vibeCoding'
RUNTIME_CC = VIBE / 'claude/9.9.9/.claude/skills/athena-vm/scripts/runtime-run.py'
RUNTIME_CX = VIBE / 'codex/9.9.9/.codex/skills/athena-vm/scripts/runtime-run.py'
CC_HOOKS = VIBE / 'claude/9.9.9/.claude/hooks'
CX_HOOKS = VIBE / 'codex/9.9.9/.codex/hooks'
PI_HOOKS = VIBE / 'pi-agent/plugin/extensions/cc-core'

# Quoted placeholders and placeholder-shaped prefixed segments; none may block or be excluded.
PLACEHOLDERS = (
    b'api_key = "YOUR_API_KEY_HERE"',
    b'api_key: "${OPENAI_API_KEY}"',
    b'client_secret: "<your-client-secret>"',
    b'password: "REPLACE_WITH_VALUE"',
    b"access_token: '{{GITHUB_TOKEN_HERE}}'",
    b'password: "xxxxxxxxxxxxxxxx"',
    b'client_secret = "changeme-changeme-x"',
    b'access_token: "sample-token-value"',
    b'password: "not-a-real-password"',
    b'api_key = "<PLACEHOLDER_KEY_X>"',
    b'# example key: sk-xxxxxxxxxxxxxxxxxxxxxx',
    b'# docs: sk-YOUR_OPENAI_KEY_HERE_XX',
)
# Real secrets plus adversarial near-placeholders; every one must keep the old behaviour.
REAL_SECRETS = (
    b'password = "A1b2C3d4E5f6G7h8I9j0"',
    b'api_key = "your-1a2b3c4d5e6f7g8h9i0j-key"',
    b'password: "tbdX9kQ2mL7vR4nZ8wP1"',
    b'client_secret: "<AKIAIOSFODNN7EXAMPLE>"',
    b'token: ghp_A1b2C3d4E5f6G7h8I9j0',
    b'key: sk-A1b2C3d4E5f6G7h8I9j0K',
    b'-----BEGIN RSA PRIVATE KEY-----',
)
# Placeholder and real secret in one file, one line, or nested inside a released span.
MIXED_SECRETS = (
    b'api_key = "YOUR_API_KEY_HERE"\npassword = "A1b2C3d4E5f6G7h8I9j0"\n',
    b'api_key = "YOUR_API_KEY_HERE" password = "A1b2C3d4E5f6G7h8I9j0"',
    b'api_key = "${sk-A1b2C3d4E5f6G7h8I9j0X}"',
)

ENV_PLACEHOLDER_LINES = (
    'recipe: uses token: placeholder',
    'version: token:none',
    'runtime: api_key: ${RUNTIME_KEY}',
    'image: secret = <your-secret>',
    'seed: password: TBD',
    'scenario: token: TODO',
    'required: password=',
)
ENV_CREDENTIAL_LINES = (
    'runtime: token=A1b2C3d4E5f6G7h8I9j0',
    'version: password: X9kQ2mL7vR4nZ8wP1cD',
    'image: https://user:pw@example.invalid/img',
)
ENV_MIXED_LINES = (
    'recipe: token: ${TOK} password: A1b2C3d4E5f6G7h8I9j0',
)


def load_runtime(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cx_hook(name):
    if str(CX_HOOKS) not in sys.path:
        sys.path.insert(0, str(CX_HOOKS))
    spec = importlib.util.spec_from_file_location(name, CX_HOOKS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNTIMES = (('cc', load_runtime(RUNTIME_CC, 'runtime_run_cc')),
            ('cx', load_runtime(RUNTIME_CX, 'runtime_run_cx')))


class PredicateMatrix(unittest.TestCase):
    """AC1/AC2/AC3/AC5/AC7: one fixture set, both native runners, identical verdicts."""

    def test_placeholders_are_not_secrets_on_both_runners(self):
        for name, runtime in RUNTIMES:
            for fixture in PLACEHOLDERS:
                with self.subTest(runner=name, fixture=fixture):
                    self.assertFalse(runtime.secret_present(fixture))

    def test_real_secrets_and_adversarial_lookalikes_stay_secrets(self):
        for name, runtime in RUNTIMES:
            for fixture in REAL_SECRETS:
                with self.subTest(runner=name, fixture=fixture):
                    self.assertTrue(runtime.secret_present(fixture))

    def test_mixed_placeholder_and_real_stays_secret(self):
        for name, runtime in RUNTIMES:
            for fixture in MIXED_SECRETS:
                with self.subTest(runner=name, fixture=fixture):
                    self.assertTrue(runtime.secret_present(fixture))

    def test_redaction_behaviour_is_unchanged(self):
        for name, runtime in RUNTIMES:
            for fixture in PLACEHOLDERS + REAL_SECRETS:
                with self.subTest(runner=name, fixture=fixture):
                    self.assertEqual(runtime.redacted(fixture + b'\n'), '[REDACTED sensitive output]\n')
            self.assertEqual(runtime.redacted(b'plain line\n'), 'plain line\n')

    def test_runtime_runner_is_byte_identical_on_cc_and_cx(self):
        self.assertEqual(RUNTIME_CC.read_bytes(), RUNTIME_CX.read_bytes())

    def test_pi_has_no_runtime_runner_copy(self):
        self.assertEqual(list((PI_HOOKS.parent).rglob('runtime-run.py')), [])


class ConsumptionPoints(unittest.TestCase):
    """AC1/AC3/AC7 end to end across collect, required-input, bundle, contract and scenario."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(RUNTIME_CX), *map(str, args)],
                              capture_output=True, text=True, env=self.env)

    def repo(self, payload):
        repo = self.base / 'repo'
        repo.mkdir()
        for command in (['git', 'init', '-q'], ['git', 'config', 'user.email', 'test@example.invalid'],
                        ['git', 'config', 'user.name', 'Fixture']):
            subprocess.run(command, cwd=repo, check=True, env=self.env)
        (repo / 'app.py').write_text('print("base")\n')
        (repo / 'config.yaml').write_bytes(payload)
        subprocess.run(['git', 'add', '.'], cwd=repo, check=True, env=self.env)
        subprocess.run(['git', 'commit', '-qm', 'base'], cwd=repo, check=True, env=self.env)
        return repo

    def scenario(self, **overrides):
        body = {'name': 'smoke', 'command': ['python3', 'app.py']}
        body.update(overrides)
        path = self.base / 'scenario.json'
        path.write_text(json.dumps(body))
        return path

    def run_bundle(self, bundle, scenario, contract_body):
        contract = self.base / 'design.md'
        contract.write_bytes(contract_body)
        output = self.base / 'result.json'
        process = self.cli('run', '--bundle', bundle, '--contract', contract,
                           '--scenario', scenario, '--output', output)
        self.assertTrue(output.exists(), process.stderr + process.stdout)
        return process, json.loads(output.read_text())

    def test_placeholder_input_is_collected_transferred_and_contract_accepted(self):
        for fixture in PLACEHOLDERS:
            with self.subTest(fixture=fixture):
                self.temp.cleanup()
                self.setUp()
                repo = self.repo(fixture + b'\n')
                bundle = self.base / 'input.tar.gz'
                result = self.cli('snapshot', '--repo', repo, '--output', bundle,
                                  '--required-input', 'config.yaml')
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                with tarfile.open(bundle) as archive:
                    self.assertIn('source/config.yaml', archive.getnames())
                process, payload = self.run_bundle(bundle, self.scenario(),
                                                   b'AC1: keeps placeholders\n' + fixture + b'\n')
                self.assertEqual(payload['status'], 'passed', process.stderr + process.stdout)

    def test_mixed_input_is_still_excluded_and_required_input_still_blocks(self):
        for fixture in MIXED_SECRETS:
            with self.subTest(fixture=fixture):
                self.temp.cleanup()
                self.setUp()
                repo = self.repo(fixture)
                bundle = self.base / 'input.tar.gz'
                result = self.cli('snapshot', '--repo', repo, '--output', bundle,
                                  '--required-input', 'config.yaml')
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('A1b2C3d4E5f6G7h8I9j0', result.stdout + result.stderr)
                clean = self.cli('snapshot', '--repo', repo, '--output', bundle)
                self.assertEqual(clean.returncode, 0, clean.stderr + clean.stdout)
                with tarfile.open(bundle) as archive:
                    self.assertNotIn('source/config.yaml', archive.getnames())

    def test_mixed_contract_still_blocks_the_run(self):
        repo = self.repo(b'clean = "value"\n')
        bundle = self.base / 'input.tar.gz'
        self.assertEqual(self.cli('snapshot', '--repo', repo, '--output', bundle).returncode, 0)
        for fixture in MIXED_SECRETS:
            with self.subTest(fixture=fixture):
                process, payload = self.run_bundle(bundle, self.scenario(), fixture)
                self.assertEqual(payload['status'], 'input_invalid', process.stdout + process.stderr)

    def test_scenario_placeholder_validates_and_mixed_scenario_is_rejected(self):
        repo = self.repo(b'clean = "value"\n')
        bundle = self.base / 'input.tar.gz'
        self.assertEqual(self.cli('snapshot', '--repo', repo, '--output', bundle).returncode, 0)
        good = self.scenario(prepare=['echo', "api_key = 'YOUR_API_KEY_HERE'"])
        process, payload = self.run_bundle(bundle, good, b'AC: placeholder scenario\n')
        self.assertEqual(payload['status'], 'passed', process.stdout + process.stderr)
        bad = self.scenario(prepare=['echo', "api_key = 'YOUR_API_KEY_HERE'",
                                     "password = 'A1b2C3d4E5f6G7h8I9j0'"])
        process, payload = self.run_bundle(bundle, bad, b'AC: mixed scenario\n')
        self.assertEqual(payload['status'], 'input_invalid', process.stdout + process.stderr)

    def tamper(self, bundle, name, content):
        target = self.base / 'tampered.tar.gz'
        with tarfile.open(bundle) as source, tarfile.open(target, 'w:gz') as sink:
            for member in source.getmembers():
                data = source.extractfile(member).read()
                if member.name == name:
                    data = content
                member.size = len(data)
                sink.addfile(member, io.BytesIO(data))
        return target

    def test_transferred_real_secret_is_still_rejected_by_bundle_inspection(self):
        repo = self.repo(b'api_key = "YOUR_API_KEY_HERE"\n')
        bundle = self.base / 'input.tar.gz'
        self.assertEqual(self.cli('snapshot', '--repo', repo, '--output', bundle).returncode, 0)
        runtime = RUNTIMES[0][1]
        runtime.inspect_bundle(bundle.read_bytes())
        for fixture in REAL_SECRETS + MIXED_SECRETS:
            with self.subTest(fixture=fixture):
                tampered = self.tamper(bundle, 'source/config.yaml', fixture)
                with self.assertRaises(ValueError) as caught:
                    runtime.inspect_bundle(tampered.read_bytes())
                self.assertEqual(str(caught.exception), 'secret pattern in transferred input')


class EnvironmentCredentialSyntax(unittest.TestCase):
    """AC4/AC7: public environment fields accept placeholders, still reject real credentials."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.ai_state').mkdir(parents=True)

    def write(self, line):
        (self.root / '.ai_state/runtime-env.yaml').write_text(line + '\n')

    def cc(self):
        code = ('const m=require(process.argv[1]);'
                'try{process.stdout.write(JSON.stringify(m.environment(process.argv[2])));}'
                'catch(e){process.stderr.write(String(e.message));process.exit(3);}')
        return subprocess.run(['node', '-e', code, str(CC_HOOKS / '_input-binding.cjs'), str(self.root)],
                              text=True, capture_output=True)

    def cx(self):
        try:
            return cx_hook('_input_binding').environment(self.root), None
        except ValueError as error:
            return None, str(error)

    def test_placeholder_environment_values_are_accepted_on_both_natives(self):
        for line in ENV_PLACEHOLDER_LINES:
            with self.subTest(line=line):
                self.write(line)
                run = self.cc()
                self.assertEqual(run.returncode, 0, run.stderr)
                value, error = self.cx()
                self.assertIsNone(error)
                self.assertEqual(json.loads(run.stdout)['recipe'], value['recipe'])

    def test_real_credentials_are_still_rejected_on_both_natives(self):
        for line in ENV_CREDENTIAL_LINES + ENV_MIXED_LINES:
            with self.subTest(line=line):
                self.write(line)
                run = self.cc()
                self.assertEqual(run.returncode, 3, run.stdout)
                self.assertIn('credential syntax', run.stderr)
                value, error = self.cx()
                self.assertIsNone(value)
                self.assertIn('credential syntax', error)

    def test_cc_and_pi_input_binding_are_byte_identical(self):
        self.assertEqual((CC_HOOKS / '_input-binding.cjs').read_bytes(),
                         (PI_HOOKS / '_input-binding.cjs').read_bytes())


if __name__ == '__main__':
    unittest.main()
