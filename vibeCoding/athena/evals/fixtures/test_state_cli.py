"""State v2: templates, athena sprint/ship/status/issue/tidy/migrate (athena-10-1 S4 AC1–AC6)."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import unittest

from gate_harness import GATE, athena, call, check_file, git, tmpdir

TODAY = datetime.date.today().isoformat()
MONTH = TODAY[:7]


def v2project(base, name='proj'):
    root = Path(base) / name
    (root / '.ai_state/roadmap/r').mkdir(parents=True)
    git(root, 'init', '-q')
    (root / 'app.js').write_text('module.exports = 1;\n', encoding='utf-8')
    tpl = (GATE / 'templates/_index.md').read_text(encoding='utf-8').replace('{{version}}', '10.1.0')
    (root / '.ai_state/_index.md').write_text(tpl, encoding='utf-8')
    (root / '.ai_state/roadmap/r/items.yaml').write_text(
        'roadmap_slug: r\nitems:\n  - slug: x\n    title: "the x slice"\n    status: pending\n    sprint: ""\n    path: Feature\n'
        '  - slug: y\n    title: "the y slice"\n    status: pending\n    sprint: ""\n    path: Bugfix\n', encoding='utf-8')
    (root / '.ai_state/queue.md').write_text('# Queue\n\n1. r/x — 用户裁定\n2. r/y\n', encoding='utf-8')
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', 'base')
    return root


def fm(path):
    text = Path(path).read_text(encoding='utf-8')
    out = {}
    for line in text.split('---')[1].splitlines():
        m = re.match(r'^([\w.-]+):\s*(.*)$', line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def item(root, slug, roadmap='r'):
    text = (Path(root) / f'.ai_state/roadmap/{roadmap}/items.yaml').read_text(encoding='utf-8')
    block = text.split(f'- slug: {slug}')[1].split('\n  - slug:')[0]
    return dict(re.findall(r'^\s+(\w+):\s*(.*)$', block, re.M))


def snapshot(root):
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob('*')):
        if '.git' in p.parts or not p.is_file():
            continue
        h.update(str(p.relative_to(root)).encode() + p.read_bytes())
    return h.hexdigest()


def ok(testcase, run):
    testcase.assertEqual(run.returncode, 0, run.stderr + run.stdout)
    return run


def last_tree(root, slug):
    rows = (root / f'.ai_state/.runtime/evidence/{slug}.jsonl').read_text().splitlines()
    return json.loads(rows[-1])['tree_sha']


def ship_ready(testcase, root, slug):
    """AC line + implementation + covered evidence + PASS review on the current tree."""
    design = root / f'.ai_state/sprints/{slug}/design.md'
    design.write_text(design.read_text(encoding='utf-8') + '\n- AC1: add returns 2\n', encoding='utf-8')
    ok(testcase, athena('sprint', 'stage', 'impl', cwd=root))
    (root / 'app.js').write_text('module.exports = 2;\n', encoding='utf-8')
    ok(testcase, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
    review = {'run': 'run-1', 'verdict': 'PASS', 'tree_sha': last_tree(root, slug)}
    (root / f'.ai_state/sprints/{slug}/review.json').write_text(json.dumps(review))


class SprintLifecycle(unittest.TestCase):
    def test_start_writes_design_index_and_item(self):
        root = v2project(tmpdir(self))
        slug = f'{TODAY}-x'
        self.assertIn(slug, ok(self, athena('sprint', 'start', 'r/x', cwd=root)).stdout)
        design = fm(root / f'.ai_state/sprints/{slug}/design.md')
        self.assertEqual((design['path'], design['roadmap'], design['item']), ('Feature', 'r', 'x'))
        self.assertRegex(design['base_commit'], r'^[0-9a-f]{7,}$')
        index = fm(root / '.ai_state/_index.md')
        self.assertEqual((index['path'], index['stage'], index['sprint']), ('Feature', 'design', slug))
        self.assertLessEqual((root / '.ai_state/_index.md').stat().st_size, 3072)
        self.assertEqual(item(root, 'x')['status'], '"active"')
        self.assertTrue(call('cc', 'write', root, file=root / 'app.js').blocked, 'template AC is a placeholder')
        self.assertEqual(athena('sprint', 'start', 'r/y', cwd=root).returncode, 2, 'one sprint in flight')

    def test_bugfix_template_and_usage_errors(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 'bug-1', cwd=root))
        self.assertIn('## 不变行为', (root / '.ai_state/sprints/bug-1/design.md').read_text(encoding='utf-8'))
        for args in (('sprint',), ('sprint', 'stage', 'nope'), ('sprint', 'start', 'r/zzz'), ('sprint', 'pause'),
                     ('issue', 'add', '--type', 'nope', '--text', 'x'), ('migrate', '--to', '9'), ('ship', '--bogus')):
            with self.subTest(args=args):
                self.assertEqual(athena(*args, cwd=root).returncode, 2)

    def test_ship_archives_and_updates_everything(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / '.gitignore').write_text('*.scratch\n')
        (root / '.ai_state/sprints/s-x/notes.scratch').write_text('ignored but travels\n')
        (root / '.ai_state/archive/sprints/2020-01/old').mkdir(parents=True)
        (root / '.ai_state/archive/sprints/2020-01/old/design.md').write_text('old\n')
        (root / '.ai_state/archive/sprints/2019-12/loose').mkdir(parents=True)
        (root / '.ai_state/archive/sprints/2019-12/loose/untracked.md').write_text('never tracked\n')
        git(root, 'add', '.ai_state/archive/sprints/2020-01')
        git(root, 'commit', '-qm', 'old archive')
        ship_ready(self, root, 's-x')
        run = ok(self, athena('ship', cwd=root))
        dest = root / f'.ai_state/archive/sprints/{MONTH}/s-x'
        self.assertTrue((dest / 'design.md').is_file())
        self.assertTrue((dest / 'notes.scratch').is_file(), 'gitignored files move with the sprint')
        self.assertFalse((root / '.ai_state/sprints/s-x').exists())
        summary = (dest / 'evidence.yaml').read_text(encoding='utf-8')
        self.assertRegex(summary, r'id: AC1, text: "add returns 2", evidence: \["[0-9a-f]+"\]')
        self.assertIn('run-1', summary)
        self.assertEqual(item(root, 'x')['status'], '"done"')
        self.assertIn('"after"', item(root, 'x')['done'])
        self.assertNotIn('r/x', (root / '.ai_state/queue.md').read_text(encoding='utf-8'))
        index = fm(root / '.ai_state/_index.md')
        self.assertEqual((index['path'], index['stage'], index['sprint']), ('', '', ''))
        self.assertIn('shipped s-x', index['route'])
        packed = [p.name for p in (root / '.ai_state/archive').iterdir() if p.name.startswith('2020-01.tar')]
        self.assertEqual(len(packed), 1, run.stdout)
        self.assertFalse((root / '.ai_state/archive/sprints/2020-01').exists())
        self.assertTrue((root / '.ai_state/archive/sprints/2019-12/loose/untracked.md').is_file(), 'a month with loose files is not packed')
        self.assertIn('untracked/ignored', run.stderr)
        self.assertNotIn('notes.scratch', git(root, 'diff', '--cached', '--name-only').stdout, 'ignored files are never staged')
        self.assertIn('| sprints/s-x/ |', (root / '.ai_state/archive/README.md').read_text(encoding='utf-8'))
        staged = git(root, 'diff', '--cached', '--name-only').stdout
        self.assertIn(f'.ai_state/archive/sprints/{MONTH}/s-x/design.md', staged)
        self.assertIn('.ai_state/_index.md', staged)
        self.assertTrue((root / '.ai_state/.runtime/archive/evidence/s-x.jsonl').is_file())

    def test_ship_refusals_change_nothing(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        before = snapshot(root)
        run = athena('ship', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('H2', run.stderr)
        self.assertEqual(snapshot(root), before)
        ship_ready(self, root, 's-x')
        (root / 'loader.js').write_text("require('./.ai_state/sprints/s-x/fixture.json')\n")
        ok(self, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
        review = {'verdict': 'PASS', 'tree_sha': last_tree(root, 's-x')}
        (root / '.ai_state/sprints/s-x/review.json').write_text(json.dumps(review))
        run = athena('ship', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('loader.js', run.stderr)
        self.assertTrue((root / '.ai_state/sprints/s-x').is_dir())

    def test_pause_resume_drop_and_resume_readiness(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        ok(self, athena('sprint', 'stage', 'impl', cwd=root))
        ok(self, athena('sprint', 'pause', '--resume-when', 'after r/y', cwd=root))
        self.assertEqual(fm(root / '.ai_state/_index.md')['stage'], '')
        self.assertEqual(item(root, 'x')['status'], '"paused"')
        self.assertNotIn('READY', ok(self, athena('status', cwd=root)).stdout)
        items = root / '.ai_state/roadmap/r/items.yaml'
        items.write_text(items.read_text().replace('"the y slice"\n    status: pending', '"the y slice"\n    status: done'))
        self.assertIn('READY', ok(self, athena('status', cwd=root)).stdout)
        self.assertIn('resume ready r/x', call('cc', 'session', root).context)
        ok(self, athena('sprint', 'resume', 's-x', cwd=root))
        index = fm(root / '.ai_state/_index.md')
        self.assertEqual((index['stage'], index['sprint']), ('impl', 's-x'))
        ok(self, athena('sprint', 'drop', '--reason', 'superseded', cwd=root))
        self.assertTrue((root / f'.ai_state/archive/sprints/{MONTH}/s-x/log.md').is_file())
        self.assertEqual(item(root, 'x')['status'], '"dropped"')
        status = json.loads(ok(self, athena('status', '--json', cwd=root)).stdout)
        self.assertEqual(status['route']['sprint'], '')


class IssuesAndTidy(unittest.TestCase):
    def test_issue_ledger_and_month_close(self):
        root = v2project(tmpdir(self))
        ids = [ok(self, athena('issue', 'add', '--type', t, '--text', f'{t} one', '--sev', 'P2', cwd=root)).stdout.strip()
               for t in ('bug', 'gate', 'question')]
        self.assertEqual(ids, ['B-001', 'G-001', 'Q-001'])
        self.assertIn('Q-001', call('cc', 'session', root).context)
        ok(self, athena('issue', 'close', 'G-001', '--note', 'fixed in S2', cwd=root))
        self.assertNotIn('G-001', ok(self, athena('issue', 'list', cwd=root)).stdout)
        self.assertIn('| proj | B-001 | bug |', ok(self, athena('issue', 'list', '--type', 'bug', '--export', cwd=root)).stdout)
        before = snapshot(root)
        self.assertIn('1 closed row', ok(self, athena('tidy', '--dry-run', cwd=root)).stdout)
        self.assertEqual(snapshot(root), before)
        ok(self, athena('tidy', cwd=root))
        self.assertNotIn('G-001', (root / '.ai_state/issues.md').read_text())
        self.assertIn('G-001', (root / f'.ai_state/archive/issues-{MONTH}.md').read_text())

    def test_tidy_runtime_retention_and_hot_limit(self):
        root = v2project(tmpdir(self))
        old = root / '.ai_state/.runtime/subagents.jsonl'
        old.parent.mkdir(parents=True)
        old.write_text('{}\n')
        os.utime(old, (1, 1))
        probe = root / '.ai_state/.runtime/probe.json'
        probe.write_text('{}')
        os.utime(probe, (1, 1))
        for i in range(5):
            d = root / f'.ai_state/sprints/2026-01-0{i}-p'
            d.mkdir(parents=True)
            (d / 'design.md').write_text(f'---\nstatus: "{"paused" if i < 3 else "active"}"\nroadmap: ""\n---\n')
        out = ok(self, athena('tidy', cwd=root)).stdout
        self.assertFalse(old.exists())
        self.assertTrue(probe.exists())
        self.assertEqual(sum(1 for d in (root / '.ai_state/sprints').iterdir() if d.is_dir()), 3, out)


class V1Compatibility(unittest.TestCase):
    def test_in_place_write_keeps_v1_spelling_and_comments(self):
        root = v2project(tmpdir(self))
        (root / '.ai_state/_index.md').write_text(
            '---\n# v1 header comment\nversion: "9.9.9"\npath: ""  # route\nstage: ""\n'
            'current_sprint_slug: ""\ncurrent_roadmap_slug: ""\nroute_history: []\n'
            'counts:\n  features_count: 1\n---\n\nbody kept\n', encoding='utf-8')
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'v1-s', cwd=root))
        text = (root / '.ai_state/_index.md').read_text(encoding='utf-8')
        for needle in ('# v1 header comment', 'current_sprint_slug: "v1-s"', 'path: "Feature"  # route',
                       '  features_count: 1', 'body kept'):
            self.assertIn(needle, text)
        self.assertNotIn('\nsprint:', text)


class Migration(unittest.TestCase):
    def v1repo(self, base):
        root = Path(base) / 'legacy'
        s = root / '.ai_state'
        for d in ('requirements', 'compound', 'docs/2026-09-01-q12-acceptance', 'docs/2026-08-01-recon',
                  'sprints/archive/2026/2026-07-01-a', 'sprints/2026-09-01-done-one', 'sprints/2026-09-02-half',
                  '.snapshots', 'roadmap/r'):
            (s / d).mkdir(parents=True)
        git(root, 'init', '-q')
        (s / '_index.md').write_text(
            '---\nversion: "9.9.9"\npath: ""\nstage: ""\ncurrent_sprint_slug: ""\ncurrent_roadmap_slug: "r"\n'
            'route_history: ["a", "b", "c", "d"]\nskip_polish: true\ncc_version: "x"\nplatform_features:\n  cc: true\n'
            'counts:\n  features_count: 3\nfingerprint: ""\nnext_action: "go"\n---\nold body\n')
        files = {
            'requirements/req.md': 'r\n', 'compound/2026-07-01-decision-a.md': 'd\n', 'compound/2026-07-02-learning-b.md': 'l\n',
            'docs/2026-09-01-q12-acceptance/x.md': 'x\n', 'docs/2026-08-01-recon/y.md': 'y\n',
            'sprints/archive/2026/2026-07-01-a/design.md': 'a\n', 'sprints/2026-09-01-done-one/design.md': '---\npath: "Quick"\n---\n',
            'sprints/2026-09-02-half/design.md': '---\npath: "Feature"\n---\n', '.snapshots/config-events.jsonl': '{}\n',
            'proposals.md': '# P\n\n## P13 · binding trap\n\ntext\n', 'vm-pending.md': '# VM\n\n- verify deploy on RHEL\n',
            'harness-patches.md': 'h\n',
            'roadmap/r/items.yaml': 'roadmap_slug: r\nitems:\n  - slug: one\n    status: completed\n    sprint_slug: "2026-09-01-done-one"\n',
        }
        for rel, body in files.items():
            (s / rel).write_text(body, encoding='utf-8')
        (root / 'app.js').write_text('1\n')
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'v1')
        return root

    def test_dry_run_changes_nothing_and_reports(self):
        root = self.v1repo(tmpdir(self))
        before = snapshot(root)
        out = ok(self, athena('migrate', '--to', '10.1', '--dry-run', cwd=root)).stdout
        self.assertEqual(snapshot(root), before)
        for needle in ('cc_version', 'skip_polish: true dropped', 'docs/reports/2026-09-01-q12-acceptance',
                       'docs/research/2026-08-01-recon', 'decisions/2026-07-01-decision-a.md', 'compound/2026-07-02-learning-b.md',
                       'archive/sprints/2026-07/2026-07-01-a', 'archive/sprints/2026-09/2026-09-01-done-one',
                       'pause | sprints/2026-09-02-half', 'untrack | .snapshots', 'debt: P13 · binding trap', 'env: verify deploy on RHEL'):
            with self.subTest(needle=needle):
                self.assertIn(needle, out)

    def test_real_run_and_rollback(self):
        root = self.v1repo(tmpdir(self))
        head = git(root, 'rev-parse', 'HEAD').stdout.strip()
        ok(self, athena('migrate', '--to', '10.1', '--report', str(root / '.ai_state/docs/reports/migration.md'), cwd=root))
        s = root / '.ai_state'
        index = (s / '_index.md').read_text(encoding='utf-8')
        self.assertIn('schema: athena-state/2', index)
        for gone in ('counts', 'fingerprint', 'platform_features', 'cc_version', 'current_sprint_slug'):
            self.assertNotIn(gone, index)
        self.assertIn('route: ["a","b","c"]', index)
        self.assertEqual(json.loads((s / '.runtime/probe.json').read_text())['cc_version'], 'x')
        self.assertTrue((s / 'decisions/2026-07-01-decision-a.md').is_file())
        self.assertTrue((s / 'docs/requirements/req.md').is_file())
        self.assertTrue(list((s / 'archive').glob('2026-07.tar.*')), 'months outside the retention window are packed')
        self.assertIn('status: "paused"', (s / 'sprints/2026-09-02-half/design.md').read_text())
        for name in ('issues.draft.md', 'issues.md', 'queue.md', 'docs/reports/migration.md'):
            self.assertTrue((s / name).is_file(), name)
        self.assertIn('.ai_state/.snapshots/', (root / '.gitignore').read_text())
        self.assertNotIn('.ai_state/.snapshots/config-events.jsonl', git(root, 'ls-files').stdout)
        self.assertEqual(athena('migrate', '--to', '10.1', cwd=root).returncode, 1, 'staged changes → refuse')
        git(root, 'reset', '-q', '--hard', 'pre-athena-10.1-state')
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout.strip(), head)
        self.assertIn('current_sprint_slug', (s / '_index.md').read_text())
        self.assertTrue((s / 'compound/2026-07-01-decision-a.md').is_file())


class Contracts(unittest.TestCase):
    def test_templates_carry_no_retired_fields(self):
        for path in (GATE / 'templates').iterdir():
            text = path.read_text(encoding='utf-8')
            with self.subTest(template=path.name):
                for retired in ('counts', 'fingerprint', 'platform_features', 'tools_available', 'last_subagent', 'breadcrumb'):
                    self.assertNotIn(retired, text)


if __name__ == '__main__':
    unittest.main()
