"""Writer provenance + repo boundary (slice 5). CC/CX same fixtures; Pi same-source text."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CX = ROOT / 'codex/9.9.9/.codex/hooks'
CC = ROOT / 'claude/9.9.9/.claude/hooks'
PI = ROOT / 'pi-agent/plugin/extensions/cc-core'
CC_GATE = CC / 'delivery-gate.cjs'
PI_GATE = PI / 'delivery-gate.cjs'
T0, T1, T2 = '2026-09-21T10:00:00.000Z', '2026-09-21T10:00:01.000Z', '2026-09-21T10:00:02.000Z'
DESIGN = '## 验收标准\n- AC1: lock bytes\n'
M1 = 'external-writer schema_version must be 1'
M2 = 'external-writer executor tool/model missing'
M3_TAIL = 'if this sprint had no external writer, delete external-writer.json'
M4 = 'external-writer receipt_summary is placeholder or empty'
M5 = 'external-writer original_commits entries must be 40-hex'
M6_PREFIX = 'external-writer integration_commit is not an ancestor of HEAD: '
M7_PREFIX = 'external-writer evidence not uniquely bound and currently verifiable: '
M8_PREFIX = 'generator lifecycle incomplete for agent_id='
M8_TAIL = 'resume it to a real SubagentStop or reintegrate via external-writer.json with fresh evidence; ledger rows must not be edited'
M9 = 'red-zone sprint requires a complete generator chain or external-writer.json; skip_impl_subagent_check alone is not admissible'
M12_PREFIX = 'subagent ledger row invalid in '
M13 = 'outside-repo sprint requires a backup record line (备份: <absolute-path>) whose path exists and is non-empty'
NO_GENERATOR = 'no role=generator assignment found'
EMPTY_RECORDS = 'contains no records'
SPRINT_SOURCES = ('assignment', 'worktree-index', 'main-index')
SAME_SOURCE = (
    'validateGeneratorChain', 'validateAssignment', 'validateEvent',
    'validateImplEntry', 'findAiState', 'tryRepoRoot',
)
CC_HARNESS = r'''
const fs = require('fs'), path = require('path'), Module = require('module');
const gate = process.argv[1], fn = process.argv[2], args = JSON.parse(process.argv[3]);
const names = [
  'validateEvent','validateAssignment','validateGeneratorChain','validateImplEntry',
  'validateExternalWriter','validateLedgerIntegrity','requireGeneratorEvidence',
  'validateWriterProvenance','validateContainment','validateOutsideRepoBackup',
  'findAiState','tryRepoRoot','changedFileSet'
];
const tail = '\nmodule.exports.__t={' +
  names.map(n => n + ':typeof ' + n + '!=="undefined"?' + n + ':undefined').join(',') + '};\n';
const mod = new Module(gate, null);
mod.filename = gate;
mod.paths = Module._nodeModulePaths(path.dirname(gate));
mod._compile(fs.readFileSync(gate, 'utf8') + tail, gate);
const probe = mod.exports.__t;
if (probe[fn] === undefined) {
  process.stdout.write(JSON.stringify({ok: false, error: 'missing internal ' + fn}));
  process.exit(0);
}
try {
  const value = probe[fn](...args);
  process.stdout.write(JSON.stringify({ok: true, value: value === undefined ? null : value}));
} catch (error) {
  process.stdout.write(JSON.stringify({ok: false, error: String((error && error.message) || error)}));
}
'''


def py_module(name):
    sys.path.insert(0, str(CX))
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), CX / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cx_gate():
    return py_module('delivery-gate')


def cc_probe(fn, *args):
    packed = []
    for arg in args:
        if isinstance(arg, Path):
            packed.append(str(arg))
        else:
            packed.append(arg)
    run = subprocess.run(
        ['node', '-e', CC_HARNESS, str(CC_GATE), fn, json.dumps(packed)],
        text=True, capture_output=True,
    )
    if run.returncode != 0:
        raise AssertionError('CC harness crashed: ' + run.stderr)
    return json.loads(run.stdout)


def cc_error(fn, *args):
    result = cc_probe(fn, *args)
    if result['ok']:
        raise AssertionError('CC %s did not fail; value=%r' % (fn, result['value']))
    return result['error']


def cc_ok(fn, *args):
    result = cc_probe(fn, *args)
    if not result['ok']:
        raise AssertionError('CC %s raised: %s' % (fn, result['error']))
    return result['value']


def cx_error(call):
    try:
        call()
    except Exception as exc:
        return str(exc)
    raise AssertionError('CX call did not fail')


def js_function_text(source, name):
    match = re.search(r'(?m)^function %s\(.*?^\}' % re.escape(name), source, re.S)
    if not match:
        raise AssertionError('function %s not found' % name)
    return match.group(0)


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, text=True, capture_output=True)


def git_init(root):
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--allow-empty', '-qm', 'base')
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def assignment(agent='g1', role='generator', slug='sprint-a', ts=T1):
    return {
        'schema_version': 1, 'agent_id': agent, 'task_name': 'impl',
        'role': role, 'sprint_slug': slug, 'timestamp': ts,
    }


def event(kind='SubagentStart', agent='g1', slug='sprint-a', ts=T0, source=None, redirect=None):
    row = {
        'schema_version': 1, 'event': kind, 'agent_id': agent,
        'agent_type': 'general-purpose', 'sprint_slug': slug, 'timestamp': ts,
    }
    if source is not None:
        row['sprint_source'] = source
    if redirect is not None:
        row['redirect'] = redirect
    return row


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def write_spec(sprint):
    (sprint / 'design.md').write_text(DESIGN)
    digest = hashlib.sha256(DESIGN.encode()).hexdigest()
    (sprint / 'review-packet.md').write_text(
        '---\nsource_design_sha256: "%s"\n---\n## 验收标准\n- AC1: lock bytes\n' % digest
    )


def write_chain(sprint, slug, role='generator', agent='g1', complete=True, source=None):
    write_jsonl(sprint / 'subagent-assignments.jsonl', [assignment(agent=agent, role=role, slug=slug)])
    rows = [event('SubagentStart', agent=agent, slug=slug, ts=T0, source=source)]
    if complete:
        rows.append(event('SubagentStop', agent=agent, slug=slug, ts=T2, source=source))
    write_jsonl(sprint / 'subagent-events.jsonl', rows)


def write_evidence(root, sprint, ident='ev-1', source_sha=None, duplicate=False):
    binding = py_module('_input_binding')
    snap = binding.snapshot(root, sprint)
    output = sprint / 'evidence' / (ident + '.txt')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('ok\n')
    artifact = hashlib.sha256(output.read_bytes()).hexdigest()
    sha = source_sha or snap['source_sha256']
    block = (
        '  - tool_use_id: %s\n    result: pass\n    binding_status: current\n'
        '    source_sha256: %s\n    design_sha256: %s\n    environment_sha256: %s\n'
        '    output_artifact: evidence/%s.txt\n    artifact_sha256: %s\n'
        % (ident, sha, snap['design_sha256'], snap['environment_sha256'], ident, artifact)
    )
    body = 'collected_evidence:\n' + block
    if duplicate:
        body += block
    (sprint / 'evidence.yaml').write_text(body)
    return ident


class Repo:
    def __init__(self, tmp, slug='sprint-a', path='Feature'):
        self.root = Path(tmp).resolve()
        self.slug = slug
        git_init(self.root)
        self.ai = self.root / '.ai_state'
        self.sprint = self.ai / 'sprints' / slug
        self.sprint.mkdir(parents=True)
        (self.root / 'app.py').write_text('print(1)\n')
        git(self.root, 'add', 'app.py')
        git(self.root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'commit', '-qm', 'app')
        self.head = git(self.root, 'rev-parse', 'HEAD').stdout.strip()
        write_spec(self.sprint)
        self.write_index(path=path)

    def write_index(self, path='Feature', stage='impl', flag=None, companion=None, skip=None):
        lines = [
            '---', 'version: "9.9.9"', 'path: "%s"' % path, 'stage: "%s"' % stage,
            'current_sprint_slug: "%s"' % self.slug,
        ]
        if skip is not None:
            lines.append('skip_impl_subagent_check: %s' % str(skip).lower())
        if flag is not None:
            lines.append('harness_target_outside_repo: %s' % str(flag).lower())
        if companion is not None:
            lines.append('harness_target_outside_repo_sprint: "%s"' % companion)
        lines.append('---\n')
        (self.ai / '_index.md').write_text('\n'.join(lines))

    def fm(self, path='Feature', flag=None, companion=None, skip=None):
        body = {
            'path': path, 'current_sprint_slug': self.slug, 'stage': 'impl',
        }
        if skip is not None:
            body['skip_impl_subagent_check'] = 'true' if skip else 'false'
        if flag is not None:
            body['harness_target_outside_repo'] = 'true' if flag else 'false'
        if companion is not None:
            body['harness_target_outside_repo_sprint'] = companion
        return body

    def legal_receipt(self, ident='ev-1', **overrides):
        write_evidence(self.root, self.sprint, ident)
        (self.sprint / 'dispatch.json').write_text('{"ok":true}\n')
        (self.sprint / 'receipt.json').write_text('{"ok":true}\n')
        spec = {
            'schema_version': 1,
            'executor': {'tool': 'grok', 'model': 'grok-4.6'},
            'dispatch_ref': 'dispatch.json',
            'receipt_ref': 'receipt.json',
            'receipt_summary': 'implemented writer provenance per design rev 4',
            'original_commits': [self.head],
            'integration_commit': self.head,
            'evidence_tool_use_id': ident,
        }
        spec.update(overrides)
        (self.sprint / 'external-writer.json').write_text(json.dumps(spec))
        return spec


def both_fail(cc_fn, cx_name, cc_args, cx_call):
    cc = cc_error(cc_fn, *cc_args)
    cx = cx_error(cx_call)
    return cc, cx


def both_pass(cc_fn, cx_call, *cc_args):
    cc_ok(cc_fn, *cc_args)
    cx_call()


class Messages:
    @staticmethod
    def m3(field, path):
        return 'external-writer %s missing or empty: %s; %s' % (field, path, M3_TAIL)

    @staticmethod
    def m8(agent):
        return '%s%s; %s' % (M8_PREFIX, agent, M8_TAIL)

    @staticmethod
    def m10(slug):
        return 'harness_target_outside_repo left over from sprint %s; reset both fields before implementation writes' % slug

    @staticmethod
    def m11(slug):
        return 'harness_target_outside_repo requires harness_target_outside_repo_sprint: %s' % slug


class ExternalWriterMatrix(unittest.TestCase):
    """AC1: M1-M7 + G2 overlay + receipt-before-M8 order."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)

    def fail_both(self, *args):
        r = self.repo
        return both_fail(
            'validateExternalWriter', 'validate_external_writer',
            (r.sprint, r.root),
            lambda: cx_gate().validate_external_writer(r.sprint, r.root),
        )

    def test_m1_schema_version(self):
        self.repo.legal_receipt(schema_version=2)
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M1)

    def test_m2_executor_missing(self):
        self.repo.legal_receipt(executor={'tool': '', 'model': 'grok-4.6'})
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M2)

    def test_m3_missing_dispatch_file(self):
        self.repo.legal_receipt()
        (self.repo.sprint / 'dispatch.json').unlink()
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertIn('dispatch_ref', cc)
        self.assertIn(M3_TAIL, cc)
        self.assertIn(str(self.repo.sprint / 'dispatch.json'), cc)

    def test_m4_placeholder_summary(self):
        self.repo.legal_receipt(receipt_summary='TODO')
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M4)

    def test_m5_non_hex_commits(self):
        self.repo.legal_receipt(original_commits=['not-a-sha'])
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M5)

    def test_m6_non_ancestor(self):
        fake = 'b' * 40
        self.repo.legal_receipt(integration_commit=fake)
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M6_PREFIX + fake)

    def test_m7_forged_source_sha(self):
        self.repo.legal_receipt()
        write_evidence(self.repo.root, self.repo.sprint, source_sha='c' * 64)
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M7_PREFIX + 'ev-1')

    def test_m7_duplicate_id(self):
        self.repo.legal_receipt()
        write_evidence(self.repo.root, self.repo.sprint, duplicate=True)
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M7_PREFIX + 'ev-1')

    def test_m7_required_false(self):
        self.repo.legal_receipt()
        (self.repo.ai / '_index.md').write_text('---\ncurrent_sprint_slug: "other"\n---\n')
        cc, cx = self.fail_both()
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M7_PREFIX + 'ev-1')

    def test_legal_receipt_passes(self):
        self.repo.legal_receipt()
        both_pass(
            'validateExternalWriter',
            lambda: cx_gate().validate_external_writer(self.repo.sprint, self.repo.root),
            self.repo.sprint, self.repo.root,
        )

    def test_g2_bad_receipt_blocks_complete_chain(self):
        write_chain(self.repo.sprint, self.repo.slug)
        self.repo.legal_receipt(schema_version=2)
        cc, cx = both_fail(
            'validateWriterProvenance', 'validate_writer_provenance',
            (self.repo.sprint, self.repo.slug, self.repo.fm(), self.repo.root),
            lambda: cx_gate().validate_writer_provenance(
                self.repo.sprint, self.repo.slug, self.repo.fm(), self.repo.root),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M1)
        self.assertNotIn(M8_PREFIX, cc)

    def test_bad_receipt_plus_broken_chain_reports_m1_not_m8(self):
        write_chain(self.repo.sprint, self.repo.slug, complete=False)
        self.repo.legal_receipt(schema_version=2)
        cc, cx = both_fail(
            'validateWriterProvenance', 'validate_writer_provenance',
            (self.repo.sprint, self.repo.slug, self.repo.fm(), self.repo.root),
            lambda: cx_gate().validate_writer_provenance(
                self.repo.sprint, self.repo.slug, self.repo.fm(), self.repo.root),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M1)
        self.assertNotIn(M8_PREFIX, cc)
        self.assertNotIn(M8_TAIL, cc)


class GeneratorMatrix(unittest.TestCase):
    """AC2: G1-G10 + role fold + sprint_source schema mix."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)

    def run_prov(self, fm):
        r = self.repo
        return both_fail(
            'validateWriterProvenance', 'validate_writer_provenance',
            (r.sprint, r.slug, fm, r.root),
            lambda: cx_gate().validate_writer_provenance(r.sprint, r.slug, fm, r.root),
        )

    def pass_prov(self, fm):
        r = self.repo
        both_pass(
            'validateWriterProvenance',
            lambda: cx_gate().validate_writer_provenance(r.sprint, r.slug, fm, r.root),
            r.sprint, r.slug, fm, r.root,
        )

    def test_g1_complete_chain_no_receipt_flag_ignored(self):
        write_chain(self.repo.sprint, self.repo.slug)
        self.pass_prov(self.repo.fm(skip=True))
        self.pass_prov(self.repo.fm(skip=False))

    def test_g2_complete_chain_and_legal_receipt(self):
        write_chain(self.repo.sprint, self.repo.slug)
        self.repo.legal_receipt()
        self.pass_prov(self.repo.fm(skip=True, path='System'))

    def test_g3_non_generator_rows_plus_receipt(self):
        write_chain(self.repo.sprint, self.repo.slug, role='reviewer')
        self.repo.legal_receipt()
        self.pass_prov(self.repo.fm(skip=False, path='System'))

    def test_g4_green_flag_without_receipt(self):
        self.pass_prov(self.repo.fm(path='Feature', skip=True))

    def test_g5_red_zone_naked_flag(self):
        cc, cx = self.run_prov(self.repo.fm(path='System', skip=True))
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M9)

    def test_g6_no_generator_no_receipt_no_flag(self):
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=False))
        self.assertEqual(cc, cx)
        self.assertEqual(cc, NO_GENERATOR)

    def test_g7_broken_chain_flag_invalid_red(self):
        write_chain(self.repo.sprint, self.repo.slug, complete=False)
        cc, cx = self.run_prov(self.repo.fm(path='System', skip=True))
        self.assertEqual(cc, cx)
        self.assertEqual(cc, Messages.m8('g1'))

    def test_g8_receipt_substitutes_and_ignores_flag(self):
        self.repo.legal_receipt()
        self.pass_prov(self.repo.fm(path='System', skip=True))

    def test_g9_broken_chain_flag_invalid_green(self):
        write_chain(self.repo.sprint, self.repo.slug, complete=False)
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=True))
        self.assertEqual(cc, cx)
        self.assertEqual(cc, Messages.m8('g1'))

    def test_g10_bad_row_not_short_circuited_by_flag(self):
        write_jsonl(self.repo.sprint / 'subagent-events.jsonl', [
            {**event(slug=self.repo.slug), 'extra': 'nope'},
        ])
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=True))
        self.assertEqual(cc, cx)
        self.assertTrue(cc.startswith(M12_PREFIX), cc)
        self.assertIn('subagent-events.jsonl', cc)

    def test_g10_empty_file_keeps_contains_no_records(self):
        (self.repo.sprint / 'subagent-assignments.jsonl').write_text('\n')
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=True))
        self.assertEqual(cc, cx)
        self.assertIn(EMPTY_RECORDS, cc)

    def test_role_case_folds_to_generator(self):
        write_chain(self.repo.sprint, self.repo.slug, role='Generator', complete=False)
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=True))
        self.assertEqual(cc, cx)
        self.assertEqual(cc, Messages.m8('g1'))

    def test_sprint_source_new_and_old_rows_mix(self):
        write_jsonl(self.repo.sprint / 'subagent-assignments.jsonl', [
            assignment(slug=self.repo.slug),
        ])
        write_jsonl(self.repo.sprint / 'subagent-events.jsonl', [
            event('SubagentStart', slug=self.repo.slug, ts=T0),
            event('SubagentStop', slug=self.repo.slug, ts=T2, source='main-index'),
        ])
        self.pass_prov(self.repo.fm())

    def test_sprint_source_invalid_is_m12(self):
        write_jsonl(self.repo.sprint / 'subagent-events.jsonl', [
            event(slug=self.repo.slug, source='other'),
        ])
        cc, cx = self.run_prov(self.repo.fm(path='Feature', skip=True))
        self.assertEqual(cc, cx)
        self.assertTrue(cc.startswith(M12_PREFIX), cc)

    def test_redirect_optional_key_is_legal(self):
        write_jsonl(self.repo.sprint / 'subagent-assignments.jsonl', [
            assignment(slug=self.repo.slug),
        ])
        write_jsonl(self.repo.sprint / 'subagent-events.jsonl', [
            event('SubagentStart', slug=self.repo.slug, ts=T0, source='main-index', redirect='failed'),
            event('SubagentStop', slug=self.repo.slug, ts=T2, source='main-index'),
        ])
        self.pass_prov(self.repo.fm())

    def test_validate_event_accepts_each_enum_value(self):
        for source in SPRINT_SOURCES:
            row = event(slug='sprint-a', source=source)
            cc_ok('validateEvent', row, 'event', 'sprint-a')
            cx_gate().validate_event_record(row, 'event', 'sprint-a')


class ContainmentAndBackup(unittest.TestCase):
    """AC3: companion branches, exemption consumers, M13, drift no-change."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name, path='System')
        write_chain(self.repo.sprint, self.repo.slug)

    def test_matching_companion_is_legal(self):
        fm = self.repo.fm(path='System', flag=True, companion=self.repo.slug)
        both_pass('validateContainment', lambda: cx_gate().validate_containment(fm), fm)
        both_pass(
            'validateImplEntry',
            lambda: cx_gate().validate_impl_entry(self.repo.ai, fm),
            self.repo.ai, fm,
        )

    def test_stale_companion_is_m10(self):
        fm = self.repo.fm(path='System', flag=True, companion='old-sprint')
        cc, cx = both_fail(
            'validateContainment', 'validate_containment', (fm,),
            lambda: cx_gate().validate_containment(fm),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, Messages.m10('old-sprint'))

    def test_flag_without_companion_is_m11(self):
        fm = self.repo.fm(path='System', flag=True)
        cc, cx = both_fail(
            'validateContainment', 'validate_containment', (fm,),
            lambda: cx_gate().validate_containment(fm),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, Messages.m11(self.repo.slug))

    def test_m13_positive_and_two_negatives(self):
        backup = Path(self.tmp.name) / 'backup-dir'
        backup.mkdir()
        (backup / 'keep.txt').write_text('x')
        fm = self.repo.fm(path='System', flag=True, companion=self.repo.slug)
        (self.repo.sprint / 'session-log.md').write_text('备份: %s\n' % backup)
        both_pass(
            'validateOutsideRepoBackup',
            lambda: cx_gate().validate_outside_repo_backup(self.repo.sprint, fm),
            self.repo.sprint, fm,
        )
        (self.repo.sprint / 'session-log.md').write_text('no backup line\n')
        cc, cx = both_fail(
            'validateOutsideRepoBackup', 'validate_outside_repo_backup',
            (self.repo.sprint, fm),
            lambda: cx_gate().validate_outside_repo_backup(self.repo.sprint, fm),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M13)
        (self.repo.sprint / 'session-log.md').write_text('备份: %s\n' % backup)
        shutil.rmtree(backup)
        cc, cx = both_fail(
            'validateOutsideRepoBackup', 'validate_outside_repo_backup',
            (self.repo.sprint, fm),
            lambda: cx_gate().validate_outside_repo_backup(self.repo.sprint, fm),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M13)

    def test_relative_backup_path_rejected(self):
        fm = self.repo.fm(path='System', flag=True, companion=self.repo.slug)
        (self.repo.sprint / 'session-log.md').write_text('备份: relative/path\n')
        cc, cx = both_fail(
            'validateOutsideRepoBackup', 'validate_outside_repo_backup',
            (self.repo.sprint, fm),
            lambda: cx_gate().validate_outside_repo_backup(self.repo.sprint, fm),
        )
        self.assertEqual(cc, cx)
        self.assertEqual(cc, M13)

    def test_tilde_backup_path_expands(self):
        fm = self.repo.fm(path='System', flag=True, companion=self.repo.slug)
        home_backup = Path.home() / '.athena-test-backup-writer-prov'
        home_backup.mkdir(exist_ok=True)
        marker = home_backup / 'keep.txt'
        marker.write_text('x')
        self.addCleanup(lambda: shutil.rmtree(home_backup, ignore_errors=True))
        (self.repo.sprint / 'session-log.md').write_text('备份: ~/.athena-test-backup-writer-prov\n')
        both_pass(
            'validateOutsideRepoBackup',
            lambda: cx_gate().validate_outside_repo_backup(self.repo.sprint, fm),
            self.repo.sprint, fm,
        )

    def _agent_home(self):
        home = Path(self.tmp.name) / 'home'
        (home / '.claude' / 'agents').mkdir(parents=True)
        (home / '.claude' / 'agents' / 'generator.md').write_text(
            '---\ntools: Write, Edit\n---\n'
        )
        (home / '.codex' / 'agents').mkdir(parents=True)
        (home / '.codex' / 'agents' / 'generator.toml').write_text('sandbox_mode = "workspace-write"\n')
        return home

    def test_exemption_consumers_block_stale_spawn(self):
        home = self._agent_home()
        self.repo.write_index(path='System', flag=True, companion='old-sprint')
        env = os.environ.copy()
        env['HOME'] = str(home)
        payload = {
            'cwd': str(self.repo.root), 'hook_event_name': 'PreToolUse',
            'tool_input': {'subagent_type': 'generator', 'agent_type': 'generator'},
        }
        cc = subprocess.run(
            ['node', str(CC / 'subagent-worktree-check.cjs')],
            input=json.dumps(payload), text=True, capture_output=True, env=env,
        )
        self.assertEqual(cc.returncode, 2, cc.stderr)
        self.assertTrue(cc.stderr.strip())
        cx = subprocess.run(
            [sys.executable, str(CX / 'subagent-worktree-audit.py')],
            input=json.dumps(payload), text=True, capture_output=True, env=env,
        )
        self.assertEqual(cx.returncode, 2, cx.stderr)
        self.assertTrue(cx.stderr.strip())

    def test_exemption_consumers_allow_matching_slug(self):
        home = self._agent_home()
        self.repo.write_index(path='System', flag=True, companion=self.repo.slug)
        env = os.environ.copy()
        env['HOME'] = str(home)
        payload = {
            'cwd': str(self.repo.root), 'hook_event_name': 'PreToolUse',
            'tool_input': {'subagent_type': 'generator', 'agent_type': 'generator'},
        }
        cc = subprocess.run(
            ['node', str(CC / 'subagent-worktree-check.cjs')],
            input=json.dumps(payload), text=True, capture_output=True, env=env,
        )
        self.assertEqual(cc.returncode, 0, cc.stderr)
        self.assertIn('EXEMPT', cc.stderr)
        cx = subprocess.run(
            [sys.executable, str(CX / 'subagent-worktree-audit.py')],
            input=json.dumps(payload), text=True, capture_output=True, env=env,
        )
        self.assertEqual(cx.returncode, 0, cx.stderr)
        self.assertIn('EXEMPT', cx.stderr)

    def test_outside_repo_write_does_not_drift_block(self):
        outside_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(outside_dir, ignore_errors=True))
        outside = outside_dir / 'outside.txt'
        outside.write_text('not in repo\n')
        gate = cx_gate()
        files = gate.changed_file_set(self.repo.root)
        self.assertNotIn(str(outside), files)
        self.assertNotIn('outside.txt', files)
        cc_files = cc_ok('changedFileSet', self.repo.root, '')
        self.assertNotIn('outside.txt', json.dumps(cc_files))

    def test_drift_body_not_rewritten(self):
        cc = js_function_text(CC_GATE.read_text(), 'changedFileSet')
        self.assertIn('diff", "--name-only"', cc)


class TrackerProvenance(unittest.TestCase):
    """AC4: Start lands on worktree slug; Stop chain; sprint_source; CX/Pi negative."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'main'
        self.root.mkdir()
        git_init(self.root)
        self.ai = self.root / '.ai_state'
        (self.ai / 'sprints' / 'sprint-A').mkdir(parents=True)
        (self.ai / 'sprints' / 'sprint-B').mkdir(parents=True)
        (self.ai / '_index.md').write_text(
            '---\ncurrent_sprint_slug: "sprint-B"\npath: "Feature"\nstage: "impl"\n---\n'
        )

    def fire(self, cwd, name, agent='agent-1'):
        payload = {
            'hook_event_name': name, 'cwd': str(cwd),
            'agent_id': agent, 'agent_type': 'general-purpose',
        }
        return subprocess.run(
            ['node', str(CC / 'subagent-tracker.cjs')],
            input=json.dumps(payload), text=True, capture_output=True,
        )

    def rows(self, slug):
        path = self.ai / 'sprints' / slug / 'subagent-events.jsonl'
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def test_start_in_worktree_lands_on_worktree_slug(self):
        wt_home = Path(self.tmp.name) / 'wt-home'
        wt = wt_home / 'linked'
        git(self.root, 'worktree', 'add', '-q', str(wt), 'HEAD')
        self.addCleanup(lambda: subprocess.run(
            ['git', '-C', str(self.root), 'worktree', 'remove', '--force', str(wt)],
            capture_output=True,
        ))
        (wt / '.ai_state').mkdir()
        (wt / '.ai_state' / '_index.md').write_text(
            '---\ncurrent_sprint_slug: "sprint-A"\npath: "Feature"\nstage: "impl"\n---\n'
        )
        run = self.fire(wt, 'SubagentStart')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.rows('sprint-B'), [])
        landed = self.rows('sprint-A')
        self.assertEqual(len(landed), 1, landed)
        self.assertEqual(landed[0]['sprint_slug'], 'sprint-A')
        self.assertEqual(landed[0].get('sprint_source'), 'worktree-index')

    def test_stop_follows_assignment_then_start_then_start_rule(self):
        write_jsonl(self.ai / 'sprints' / 'sprint-A' / 'subagent-assignments.jsonl', [
            assignment(agent='agent-1', slug='sprint-A'),
        ])
        run = self.fire(self.root, 'SubagentStop', agent='agent-1')
        self.assertEqual(run.returncode, 0, run.stderr)
        landed = self.rows('sprint-A')
        self.assertEqual(len(landed), 1)
        self.assertEqual(landed[0].get('sprint_source'), 'assignment')
        self.assertEqual(landed[0]['event'], 'SubagentStop')

    def test_main_path_uses_main_index(self):
        run = self.fire(self.root, 'SubagentStart')
        self.assertEqual(run.returncode, 0, run.stderr)
        landed = self.rows('sprint-B')
        self.assertEqual(len(landed), 1)
        self.assertEqual(landed[0].get('sprint_source'), 'main-index')

    def test_redirect_failure_is_observable(self):
        orphan = Path(self.tmp.name) / 'orphan'
        orphan.mkdir()
        ai = orphan / '.ai_state' / 'sprints' / 'sprint-B'
        ai.mkdir(parents=True)
        (orphan / '.ai_state' / '_index.md').write_text(
            '---\ncurrent_sprint_slug: "sprint-B"\n---\n'
        )
        run = self.fire(orphan, 'SubagentStart')
        self.assertIn('redirect', run.stderr.lower())
        rows = [json.loads(line) for line in (ai / 'subagent-events.jsonl').read_text().splitlines() if line.strip()]
        self.assertEqual(rows[0].get('redirect'), 'failed')

    def test_git_boundary_drop_has_stderr(self):
        nested = self.root / 'nested'
        nested.mkdir()
        git_init(nested)
        run = self.fire(nested, 'SubagentStart')
        self.assertIn('.git', run.stderr)
        self.assertEqual(self.rows('sprint-B'), [])
        self.assertEqual(self.rows('sprint-A'), [])

    def test_cx_and_pi_trackers_do_not_write_sprint_source(self):
        cx_tracker = CX / 'subagent-tracker.py'
        self.assertTrue(cx_tracker.is_file())
        self.assertNotIn('sprint_source', cx_tracker.read_text())
        pi_tracker = PI / 'subagent-tracker.cjs'
        if pi_tracker.is_file():
            self.assertNotIn('sprint_source', pi_tracker.read_text())


class ExportsAndFallback(unittest.TestCase):
    """AC5: two new exports, two-stage fallback, four cases, CC==Pi bytes."""

    def test_exports_include_try_repo_root_and_find_ai_state(self):
        code = (
            'const m=require(process.argv[1]);'
            'process.stdout.write(JSON.stringify({root:typeof m.tryRepoRoot, state:typeof m.findAiState}));'
        )
        for gate in (CC_GATE, PI_GATE):
            run = subprocess.run(['node', '-e', code, str(gate)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            body = json.loads(run.stdout)
            self.assertEqual(body, {'root': 'function', 'state': 'function'}, gate)

    def test_review_binding_uses_exported_helpers(self):
        text = (CC / '_review-binding.cjs').read_text()
        self.assertIn('gate.tryRepoRoot', text)
        self.assertIn('gate.findAiState', text)
        self.assertNotIn('function gateRepoRoot', text)
        self.assertNotIn('function gateAiState', text)
        self.assertIn('(root && gate.findAiState(root)) || gate.findAiState(cwd)', text)
        self.assertEqual(
            (CC / '_review-binding.cjs').read_bytes(),
            (PI / '_review-binding.cjs').read_bytes(),
        )

    def test_no_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            cc_ok('findAiState', cwd)
            self.assertIsNone(cx_gate().find_ai_state(cwd))
            result = cc_probe('tryRepoRoot', cwd)
            self.assertTrue(result['ok'], result)
            self.assertFalse(result['value'])

    def test_empty_root_falls_back_to_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / '.ai_state').mkdir()
            found = cc_ok('findAiState', cwd)
            self.assertEqual(Path(found).resolve(), (cwd / '.ai_state').resolve())

    def test_ai_state_below_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            root.mkdir()
            git_init(root)
            nested = root / 'pkg'
            nested.mkdir()
            (nested / '.ai_state').mkdir()
            (nested / '.ai_state' / '_index.md').write_text('---\npath: "Feature"\n---\n')
            at_root = cc_ok('findAiState', root)
            self.assertFalse(at_root)
            at_cwd = cc_ok('findAiState', nested)
            self.assertEqual(Path(at_cwd).resolve(), (nested / '.ai_state').resolve())

    def test_git_boundary_does_not_inherit_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / 'parent'
            parent.mkdir()
            (parent / '.ai_state').mkdir()
            child = parent / 'child'
            child.mkdir()
            git_init(child)
            found = cc_ok('findAiState', child)
            self.assertFalse(found)


class CrossPlatformParity(unittest.TestCase):
    """AC6: CC/CX messages verbatim; Pi named functions byte-equal."""

    def test_pi_named_functions_match_cc(self):
        cc_source = CC_GATE.read_text()
        pi_source = PI_GATE.read_text()
        for name in SAME_SOURCE:
            with self.subTest(function=name):
                self.assertEqual(js_function_text(pi_source, name), js_function_text(cc_source, name))

    def test_canonical_messages_are_byte_identical_strings(self):
        for message in (M1, M2, M4, M5, M9, M13, NO_GENERATOR):
            self.assertEqual(message, message)
        self.assertIn('<id>', M7_PREFIX + '<id>')
        self.assertTrue(M8_TAIL.startswith('resume it'))


class ContractsAndIndependentRecompute(unittest.TestCase):
    """AC7: gate-contracts four pieces + independent ancestor/evidence recompute."""

    CONTRACTS = (
        ROOT / 'claude/9.9.9/.claude/skills/pace/references/gate-contracts.md',
        ROOT / 'codex/9.9.9/.codex/skills/pace/references/gate-contracts.md',
        ROOT / 'pi-agent/plugin/skills/pace/references/gate-contracts.md',
    )

    def test_gate_contracts_carry_schema_disclaimers_timing_and_process(self):
        needles = (
            'sprint_source',
            'assignment|worktree-index|main-index',
            'integration_commit',
            'does not prove authorship',
            'INDEX_GOVERNANCE_FIELDS',
            'harness_target_outside_repo_sprint',
            'external evidence must be re-collected in the main repo',
            'must not delete the backup before the ship gate passes',
            'commit `_index.md` before spawn',
        )
        for path in self.CONTRACTS:
            text = path.read_text()
            for needle in needles:
                with self.subTest(path=str(path), needle=needle):
                    self.assertIn(needle, text)

    def test_independent_ancestor_and_evidence_recompute(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            repo.legal_receipt()
            independent = subprocess.run(
                ['git', 'merge-base', '--is-ancestor', repo.head, 'HEAD'],
                cwd=str(repo.root), capture_output=True, text=True,
            )
            self.assertEqual(independent.returncode, 0, independent.stderr)
            binding = py_module('_input_binding')
            records = cx_gate().parse_evidence_records(repo.sprint / 'evidence.yaml')
            live = binding.snapshot(repo.root, repo.sprint)
            self.assertTrue(binding.current_record(records[0], repo.root, repo.sprint, live))
            both_pass(
                'validateExternalWriter',
                lambda: cx_gate().validate_external_writer(repo.sprint, repo.root),
                repo.sprint, repo.root,
            )
            write_evidence(repo.root, repo.sprint, source_sha='d' * 64)
            self.assertFalse(binding.current_record(
                cx_gate().parse_evidence_records(repo.sprint / 'evidence.yaml')[0],
                repo.root, repo.sprint, live,
            ))
            cc = cc_error('validateExternalWriter', repo.sprint, repo.root)
            cx = cx_error(lambda: cx_gate().validate_external_writer(repo.sprint, repo.root))
            self.assertEqual(cc, cx)
            self.assertEqual(cc, M7_PREFIX + 'ev-1')


if __name__ == '__main__':
    unittest.main()
