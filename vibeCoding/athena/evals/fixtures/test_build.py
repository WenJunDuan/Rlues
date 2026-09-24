"""athena-10-1 S1/S2: the single-source build reproduces the 9.9.9 packages byte for byte,
except for the changes each 10.1 slice declares in DELTA (S2: declared-delta, not silent drift).

Run: python3 -m unittest discover -s vibeCoding/athena/evals/fixtures -t vibeCoding/athena/evals/fixtures
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

ATHENA = Path(__file__).resolve().parents[2]          # vibeCoding/athena
VIBE = ATHENA.parent                                  # vibeCoding
BUILD = ATHENA / 'build.mjs'
IGNORED = {'__pycache__', '.DS_Store'}
GENERATED_EXTRAS = {'manifest.json', 'GENERATED.md', 'contracts.json'}
BASELINES = {
    'claude': VIBE / 'old/04-athena-8.9-9.9.9/claude/9.9.9',
    'codex': VIBE / 'old/04-athena-8.9-9.9.9/codex/9.9.9',
    'pi': VIBE / 'old/04-athena-8.9-9.9.9/pi-agent',
}
# Every difference from the 9.9.9 baseline must be declared here (prefixes end with "/").
DELTA = {  # S2 gate core · S3 review CLI · S6 installer (entries ending in "/" are prefixes)
    'claude': {'removed': ['.claude/hooks/', '.claude/skills/pace/scripts/review-binding.cjs', '.claude/skills/athena-review/REVIEW.md',
                           '.claude/skills/athena-migrate/', '.claude/skills/athena-setup/scripts/', '.claude/skills/athena-setup/tests/'],
               'changed': ['.claude/settings.json', '.claude/agents/reviewer.md', '.claude/skills/athena-review/SKILL.md',
                           '.claude/skills/athena-setup/SKILL.md', 'RELEASE.md'],
               'added': ['.claude/workflows/athena-review.js']},
    'codex': {'removed': ['.codex/hooks/', '.codex/skills/athena-review/REVIEW.md', '.codex/skills/athena-migrate/',
                          '.codex/skills/athena-setup/scripts/', '.codex/skills/athena-setup/tests/'],
              'changed': ['.codex/hooks.json', '.codex/agents/reviewer.toml', '.codex/skills/athena-review/SKILL.md',
                          '.codex/skills/athena-setup/SKILL.md', 'RELEASE.md'], 'added': []},
    'pi': {'removed': ['plugin/extensions/cc-core/', 'plugin/skills/pace/scripts/review-binding.cjs', 'plugin/skills/athena-review/REVIEW.md'],
           'added': ['plugin/core/gate/'],
           'changed': ['README.md', 'config/README.md', 'plugin/README.md', 'plugin/extensions/athena-gates.ts', 'plugin/extensions/athena-lifecycle.ts',
                       'plugin/prompts/reviewer.md', 'plugin/skills/athena-review/SKILL.md']},
}
# S5 prompts-v2 rewrites constitution, rules, skills and agents wholesale (one core source, generated
# per platform); the per-file checks for that layer live in test_prompts.py.
S5 = {
    'claude': {'removed': ['.claude/rules/', '.claude/skills/', '.claude/agents/'],
               'changed': ['.claude/CLAUDE.md', '.claude/rules/', '.claude/skills/', '.claude/agents/', 'AI-MIGRATION-GUIDE.md'],
               'added': ['.claude/rules/', '.claude/skills/']},
    'codex': {'removed': ['.codex/standards/', '.codex/skills/', '.codex/agents/'],
              'changed': ['.codex/AGENTS.md', '.codex/standards/', '.codex/skills/', '.codex/agents/', '.codex/config.toml', 'AI-MIGRATION-GUIDE.md', 'CHANGELOG.md'],
              'added': ['.codex/standards/', '.codex/skills/']},
    'pi': {'removed': ['config/rules/', 'plugin/skills/'],
           'changed': ['plugin/core/IRON.md', 'config/AGENTS.md', 'config/rules/', 'plugin/skills/', 'plugin/prompts/'],
           'added': ['config/rules/', 'plugin/skills/']},
}
for _p, _d in S5.items():
    for _k, _entries in _d.items():
        DELTA[_p][_k] = DELTA[_p][_k] + _entries
NEW_DISTS = ('athena',)   # S2: gate core → ~/.athena/<ver>/


def declared(rel, entries):
    return any(rel == e or (e.endswith('/') and rel.startswith(e)) for e in entries)


STAGE_DOCS = (
    VIBE / 'old/04-athena-8.9-9.9.9/claude/9.9.9/.claude/skills/pace/references/stages.md',
    VIBE / 'old/04-athena-8.9-9.9.9/codex/9.9.9/.codex/skills/pace/references/stages.md',
    VIBE / 'old/04-athena-8.9-9.9.9/pi-agent/plugin/skills/pace/references/stages.md',
)


def tree(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob('*')):
        if path.is_file() and not (IGNORED & set(path.relative_to(root).parts)):
            out[path.relative_to(root).as_posix()] = path.read_bytes()
    return out


def build(out: Path, src: Path = ATHENA, *extra):
    return subprocess.run(['node', str(src / 'build.mjs'), '--src', str(src), '--out', str(out), *extra],
                          text=True, capture_output=True)


class BuildBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / 'dist'
        cls.run_result = build(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def dist(self, platform):
        return self.out / platform / '10.1'

    def test_ac1_build_succeeds_with_generated_extras(self):
        self.assertEqual(self.run_result.returncode, 0, self.run_result.stderr)
        for platform in (*BASELINES, *NEW_DISTS):
            for name in GENERATED_EXTRAS:
                with self.subTest(platform=platform, file=name):
                    self.assertTrue((self.dist(platform) / name).is_file())

    def test_ac2_output_equals_999_packages_except_declared_delta(self):
        for platform, baseline in BASELINES.items():
            delta = DELTA[platform]
            with self.subTest(platform=platform):
                expected = tree(baseline)
                actual = {k: v for k, v in tree(self.dist(platform)).items() if k not in GENERATED_EXTRAS}
                missing = sorted(set(expected) - set(actual))
                extra = sorted(set(actual) - set(expected))
                differing = sorted(k for k in set(expected) & set(actual) if expected[k] != actual[k])
                self.assertEqual([k for k in missing if not declared(k, delta['removed'])], [], 'undeclared removals')
                self.assertEqual([k for k in extra if not declared(k, delta['added'])], [], 'undeclared additions')
                self.assertEqual([k for k in differing if not declared(k, delta['changed'])], [], 'undeclared byte differences')
                for entry in delta['changed']:
                    self.assertTrue(any(declared(k, [entry]) for k in differing), f'declared change {entry} did not happen')
                for entry in delta['removed']:
                    self.assertTrue(any(declared(k, [entry]) for k in missing), f'declared removal {entry} did not happen')
                for entry in delta['added']:
                    self.assertTrue(any(declared(k, [entry]) for k in extra), f'declared addition {entry} did not happen')

    def test_ac2_executable_bits_follow_sources(self):
        for platform, baseline in BASELINES.items():
            for rel in tree(baseline):
                built = self.dist(platform) / rel
                if not built.exists():
                    continue
                source_exec = bool((baseline / rel).stat().st_mode & 0o111)
                with self.subTest(platform=platform, file=rel):
                    self.assertEqual(bool(built.stat().st_mode & 0o111), source_exec)

    def test_root_docs_ship_in_core_dist(self):
        """INSTALL / MIGRATION / RELEASE are single-source at vibeCoding/athena/ and land at ~/.athena/<ver>/."""
        for name in ('INSTALL.md', 'MIGRATION.md', 'RELEASE.md'):
            with self.subTest(doc=name):
                self.assertEqual((self.dist('athena') / name).read_bytes(), (ATHENA / name).read_bytes())
        self.assertFalse((self.dist('athena') / 'AI-MIGRATION-GUIDE.md').exists())

    def test_version_single_source(self):
        """Every version string the installer reads comes from VERSION (no hardcoded release in adapters)."""
        version = (ATHENA / 'VERSION').read_text(encoding='utf-8').strip()
        settings = json.loads((self.dist('claude') / '.claude/settings.json').read_text(encoding='utf-8'))
        self.assertEqual(settings['env']['VIBECODING_ATHENA_VERSION'], version)
        self.assertIn(f'VIBECODING_VERSION = "{version}"', (self.dist('codex') / '.codex/config.toml').read_text(encoding='utf-8'))
        for platform in (*BASELINES, *NEW_DISTS):
            with self.subTest(platform=platform):
                self.assertEqual(json.loads((self.dist(platform) / 'manifest.json').read_text(encoding='utf-8'))['version'], version)

    def test_ac5_manifest_matches_files(self):
        for platform in (*BASELINES, *NEW_DISTS):
            root = self.dist(platform)
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
            listed = {entry['path']: entry for entry in manifest['files']}
            on_disk = {k for k in tree(root) if k != 'manifest.json'}
            with self.subTest(platform=platform):
                self.assertEqual(set(listed), on_disk)
                self.assertEqual([e['path'] for e in manifest['files']], sorted(listed))
                for rel, entry in listed.items():
                    self.assertEqual(entry['sha256'], hashlib.sha256((root / rel).read_bytes()).hexdigest(), rel)
                    self.assertIn(entry['mode'], ('0644', '0755'), rel)
                    on_disk_exec = bool((root / rel).stat().st_mode & 0o111)
                    self.assertEqual(entry['mode'] == '0755', on_disk_exec, rel)

    def test_ac5_contracts_follow_stages_yaml(self):
        ids = None
        for platform in (*BASELINES, *NEW_DISTS):
            contracts = json.loads((self.dist(platform) / 'contracts.json').read_text(encoding='utf-8'))
            stage_ids = [stage['id'] for stage in contracts['stages']]
            if ids is None:
                ids = stage_ids
            self.assertEqual(stage_ids, ids, platform)
        self.assertEqual(ids, ['brainstorm', 'roadmap', 'plan', 'design', 'impl',
                               'runtime-verify', 'polish', 'review', 'ship'])
        for doc in STAGE_DOCS:
            text = doc.read_text(encoding='utf-8')
            for stage_id in ids:
                with self.subTest(doc=str(doc.relative_to(VIBE)), stage=stage_id):
                    self.assertIn(f'\n## {stage_id}\n', text)


class BuildProperties(unittest.TestCase):
    def test_ac3_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'a', Path(tmp) / 'b'
            self.assertEqual(build(first).returncode, 0)
            self.assertEqual(build(second).returncode, 0)
            self.assertEqual(tree(first), tree(second))

    def test_check_mode_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out).returncode, 0)
            self.assertEqual(build(out, ATHENA, '--check').returncode, 0)
            target = out / 'claude/10.1/.claude/CLAUDE.md'
            target.write_text(target.read_text(encoding='utf-8') + 'hand edit\n', encoding='utf-8')
            drift = build(out, ATHENA, '--check')
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn('.claude/CLAUDE.md', drift.stderr)

    def copy_source(self, tmp):
        src = Path(tmp) / 'athena'
        shutil.copytree(ATHENA, src, ignore=shutil.ignore_patterns('__pycache__', 'evals'))
        return src

    def test_ac4_undefined_variable_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.copy_source(tmp)
            bad = src / 'core/package/skills/zz-probe/SKILL.md'
            bad.parent.mkdir(parents=True)
            bad.write_text('uses {{athena:NOT_DEFINED}}\n', encoding='utf-8')
            run = build(Path(tmp) / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('NOT_DEFINED', run.stderr)
            self.assertIn('skills/zz-probe/SKILL.md', run.stderr)

    def test_ac4_core_adapter_conflict_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.copy_source(tmp)
            shared = next(p for p in sorted((src / 'core/package/skills').rglob('*')) if p.is_file())
            rel = shared.relative_to(src / 'core/package')
            clash = src / 'adapters/cc/package' / rel
            clash.parent.mkdir(parents=True, exist_ok=True)
            clash.write_bytes(shared.read_bytes())
            run = build(Path(tmp) / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn(rel.as_posix(), run.stderr)

    def test_single_source_counts(self):
        """The shared layer really is shared: every core file ships to both CC and CX (after renames)."""
        core = sorted(p.relative_to(ATHENA / 'core/package').as_posix()
                      for p in (ATHENA / 'core/package').rglob('*') if p.is_file())
        self.assertGreaterEqual(len(core), 70)
        templated = [rel for rel in core if b'{{athena:' in (ATHENA / 'core/package' / rel).read_bytes()]
        self.assertGreaterEqual(len(templated), 5)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(build(Path(tmp) / 'dist').returncode, 0)
            for platform, dist, root in (('cc', 'claude', '.claude'), ('cx', 'codex', '.codex')):
                config = json.loads((ATHENA / 'adapters' / platform / 'platform.json').read_text(encoding='utf-8'))
                self.assertTrue(config['core'], platform)
                rename = config.get('rename', {})
                for rel in core:
                    out = next((to + rel[len(fr):] for fr, to in rename.items() if rel == fr or (fr.endswith('/') and rel.startswith(fr))), rel)
                    with self.subTest(platform=platform, core=rel):
                        self.assertTrue((Path(tmp) / 'dist' / dist / '10.1' / root / out).is_file())
                        self.assertFalse((ATHENA / 'adapters' / platform / 'package' / rel).exists())

    def test_executable_source_builds_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.copy_source(tmp)
            probe = src / 'core/package/skills/zz-probe/run.sh'
            probe.parent.mkdir(parents=True)
            probe.write_text('#!/bin/sh\necho ok\n', encoding='utf-8')
            probe.chmod(0o700)
            plain = src / 'core/package/skills/zz-probe/notes.md'
            plain.write_text('x\n', encoding='utf-8')
            plain.chmod(0o700 & ~0o111 | 0o600)
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out, src).returncode, 0)
            for dist, root in (('claude', '.claude'), ('codex', '.codex')):
                base = out / dist / '10.1' / root / 'skills/zz-probe'
                manifest = {e['path']: e for e in json.loads((out / dist / '10.1/manifest.json').read_text())['files']}
                with self.subTest(dist=dist):
                    self.assertTrue((base / 'run.sh').stat().st_mode & 0o111)
                    self.assertFalse((base / 'notes.md').stat().st_mode & 0o111)
                    self.assertEqual(manifest[f'{root}/skills/zz-probe/run.sh']['mode'], '0755')
                    self.assertEqual(manifest[f'{root}/skills/zz-probe/notes.md']['mode'], '0644')

    def test_check_mode_detects_mode_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out).returncode, 0)
            target = out / 'claude/10.1/.claude/CLAUDE.md'
            target.chmod(0o755)
            drift = build(out, ATHENA, '--check')
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn('mode .claude/CLAUDE.md', drift.stderr)

    def probe(self, tmp, name, data: bytes):
        src = self.copy_source(tmp)
        path = src / 'core/package/skills/zz-probe' / name
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        return src

    def test_bom_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.probe(tmp, 'bom.md', b'\xef\xbb\xbfpath {{athena:SKILLS_DIR}}\n')
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out, src).returncode, 0)
            built = (out / 'claude/10.1/.claude/skills/zz-probe/bom.md').read_bytes()
            self.assertEqual(built, b'\xef\xbb\xbfpath ~/.claude/skills\n')

    def test_malformed_and_binary_markers_fail(self):
        cases = (
            ('lower.md', b'{{athena:skills_dir}}\n'),
            ('space.md', b'{{athena:SKILLS_DIR }}\n'),
            ('binary.bin', b'\x00\x01{{athena:SKILLS_DIR}}'),
        )
        for name, data in cases:
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                src = self.probe(tmp, name, data)
                run = build(Path(tmp) / 'dist', src)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(f'skills/zz-probe/{name}', run.stderr)

    def test_literal_marker_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.probe(tmp, 'doc.md', b'write {{athena:!SKILLS_DIR}} in sources\n')
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out, src).returncode, 0)
            built = (out / 'codex/10.1/.codex/skills/zz-probe/doc.md').read_bytes()
            self.assertEqual(built, b'write {{athena:SKILLS_DIR}} in sources\n')

    def test_case_only_conflict_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.copy_source(tmp)
            clash = src / 'adapters/cc/package/skills/polish/skill.md'
            clash.parent.mkdir(parents=True, exist_ok=True)
            clash.write_text('x\n', encoding='utf-8')
            run = build(Path(tmp) / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('skills/polish/skill.md', run.stderr)

    def test_refuses_to_replace_non_build_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # empty VERSION would otherwise make the release dir the platform dir
            src = self.copy_source(tmp)
            (src / 'VERSION').write_text('\n', encoding='utf-8')
            keep = tmp / 'dist/claude/precious.txt'
            keep.parent.mkdir(parents=True)
            keep.write_text('keep\n', encoding='utf-8')
            run = build(tmp / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('VERSION', run.stderr)
            self.assertTrue(keep.is_file())
            # an existing non-build target is never deleted
            foreign = tmp / 'dist2/claude/10.1/user-file.txt'
            foreign.parent.mkdir(parents=True)
            foreign.write_text('mine\n', encoding='utf-8')
            run = build(tmp / 'dist2')
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('not a previous build output', run.stderr)
            self.assertTrue(foreign.is_file())
            # nothing is written when any platform fails
            self.assertFalse((tmp / 'dist2/codex').exists())
            # unknown or path-like platforms are rejected
            for platform in ('../x', 'nope'):
                with self.subTest(platform=platform):
                    run = build(tmp / 'dist3', ATHENA, '--platform', platform)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('unknown platform', run.stderr)
            self.assertFalse((tmp / 'dist3').exists())

    def test_nothing_written_when_a_later_target_is_foreign(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'dist'
            foreign = out / 'codex/10.1/f'
            foreign.parent.mkdir(parents=True)
            foreign.write_text('k\n', encoding='utf-8')
            run = build(out)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((out / 'claude').exists())
            self.assertTrue(foreign.is_file())

    def test_duplicate_dist_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.copy_source(tmp)
            config = src / 'adapters/cx/platform.json'
            data = json.loads(config.read_text(encoding='utf-8'))
            data['dist_dir'] = 'claude'
            config.write_text(json.dumps(data), encoding='utf-8')
            run = build(Path(tmp) / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('share dist_dir claude', run.stderr)

    def test_rebuild_replaces_previous_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'dist'
            self.assertEqual(build(out).returncode, 0)
            stale = out / 'claude/10.1/stale.txt'
            stale.write_text('old\n', encoding='utf-8')
            self.assertEqual(build(out).returncode, 0)
            self.assertFalse(stale.exists())
            self.assertEqual(build(out, ATHENA, '--check').returncode, 0)


if __name__ == '__main__':
    unittest.main()
