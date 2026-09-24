"""Regressions for the S4 independent review (round 1): data loss, YAML writers, atomicity, staging."""
import json
import os
from pathlib import Path
import subprocess
import unittest

import yaml

from gate_harness import ENV, GATE, athena, git, tmpdir
from test_state_cli import MONTH, Migration, fm, ok, ship_ready, snapshot, v2project

STATE = GATE / 'cli/lib/state.cjs'


def node(code, *args, cwd=None):
    run = subprocess.run(['node', '-e', code, str(STATE), *map(str, args)], text=True, capture_output=True, env=ENV, cwd=cwd)
    if run.returncode:
        raise AssertionError(run.stderr)
    return run.stdout


def staged(root):
    return git(root, 'diff', '--cached', '--name-only').stdout


class YamlWriters(unittest.TestCase):
    def test_set_item_replaces_nested_blocks_and_ignores_nested_ids(self):
        tmp = tmpdir(self)
        items = tmp / 'items.yaml'
        items.write_text('roadmap_slug: r\nitems:\n  - slug: x\n    status: pending\n    deferred:\n      reason: "old"\n'
                         '      resume_when: "after y"\n    acceptance:\n      - id: AC1\n        text: a\n    done:\n      commit: ""\n\n'
                         '  - slug: y\n    status: pending\n', encoding='utf-8')
        node("const s=require(process.argv[1]);s.setItem(process.argv[2],'x',{status:'paused',deferred:{reason:'p',resume_when:'w'},sprint:'s-x',done:{after:'a'}});"
             "process.stdout.write(s.readItems(process.argv[2]).items.map(i=>i.slug).join(','))", items)
        data = yaml.safe_load(items.read_text(encoding='utf-8'))
        x = data['items'][0]
        self.assertEqual([i['slug'] for i in data['items']], ['x', 'y'])
        self.assertEqual((x['status'], x['deferred'], x['sprint'], x['done']), ('paused', {'reason': 'p', 'resume_when': 'w'}, 's-x', {'after': 'a'}))
        self.assertEqual(x['acceptance'], [{'id': 'AC1', 'text': 'a'}])

    def test_set_fields_block_lists_crlf_and_comment_quotes(self):
        tmp = tmpdir(self)
        doc = tmp / 'i.md'
        doc.write_bytes(b'---\r\nroute_history:\r\n- "a"\r\n- "b"\r\nstage: ""  # it\'s the stage\r\n---\r\nbody\r\n')
        node("require(process.argv[1]).setFields(process.argv[2],{route_push:'c',stage:'impl'})", doc)
        raw = doc.read_bytes()
        self.assertNotIn(b'\n', raw.replace(b'\r\n', b''), 'line endings stay CRLF')
        data = yaml.safe_load(raw.decode().split('---')[1])
        self.assertEqual((data['route_history'], data['stage']), (['c', 'a', 'b'], 'impl'))
        self.assertIn(b"# it's the stage", raw)

    def test_queue_remove_matches_whole_words(self):
        tmp = tmpdir(self)
        (tmp / 'queue.md').write_text('# Q\n\n1. s-x now\n2. s-x2 follow-up keep me\n3. see s-x-notes\n4. r/x done\n5. r/xy keep\n')
        node("require(process.argv[1]).queueRemove(process.argv[2],'s-x','r/x')", tmp)
        left = (tmp / 'queue.md').read_text()
        for keep in ('s-x2 follow-up', 's-x-notes', 'r/xy keep'):
            self.assertIn(keep, left)
        self.assertNotIn('s-x now', left)
        self.assertNotIn('r/x done', left)


class ShipAtomicAndStaging(unittest.TestCase):
    def test_path_ignored_files_are_never_staged(self):
        root = v2project(tmpdir(self))
        (root / '.gitignore').write_text('.ai_state/sprints/*/scratch/\n')
        git(root, 'add', '.gitignore')
        git(root, 'commit', '-qm', 'ignore')
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / '.ai_state/sprints/s-x/scratch').mkdir()
        (root / '.ai_state/sprints/s-x/scratch/secret.env').write_text('TOKEN=1\n')
        ship_ready(self, root, 's-x')
        ok(self, athena('ship', cwd=root))
        self.assertTrue((root / f'.ai_state/archive/sprints/{MONTH}/s-x/scratch/secret.env').is_file())
        self.assertNotIn('secret.env', staged(root))

    def test_ship_prechecks_leave_nothing_half_written(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        ship_ready(self, root, 's-x')
        (root / f'.ai_state/archive/sprints/{MONTH}/s-x').mkdir(parents=True)
        before = snapshot(root)
        run = athena('ship', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('already exists', run.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertEqual(athena('sprint', 'start', 'r/y', '--slug', 's-x', cwd=root).returncode, 2)

    def test_start_refuses_a_slug_already_archived(self):
        root = v2project(tmpdir(self))
        (root / '.ai_state/archive/sprints/2026-01/s-y').mkdir(parents=True)
        run = athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('pick another --slug', run.stderr)

    def test_drop_refuses_when_code_reads_the_sprint(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / 'load.js').write_text("read('.ai_state/sprints/s-x/data.json')\n")
        run = athena('sprint', 'drop', '--reason', 'x', cwd=root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('load.js', run.stderr)
        self.assertTrue((root / '.ai_state/sprints/s-x').is_dir())

    def test_tidy_stages_only_what_it_changed_and_keeps_protected_runtime(self):
        root = v2project(tmpdir(self))
        (root / '.ai_state/roadmap/r/items.yaml').write_text((root / '.ai_state/roadmap/r/items.yaml').read_text() + '# user edit\n')
        (root / '.ai_state/sprints/wip').mkdir(parents=True)
        (root / '.ai_state/sprints/wip/notes.md').write_text('mine\n')
        runtime = root / '.ai_state/.runtime'
        keep = [runtime / 'snapshots/config-events.jsonl', runtime / '_index.v1.md', runtime / 'evidence/wip.jsonl',
                runtime / 'archive/evidence/old.jsonl']
        for f in keep:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('x\n')
            os.utime(f, (1, 1))
        ok(self, athena('tidy', cwd=root))
        self.assertEqual(staged(root).strip(), '')
        for f in keep:
            self.assertTrue(f.exists(), f)


class MigrationSafety(unittest.TestCase):
    def test_loose_files_are_moved_never_staged_and_survive_rollback(self):
        root = Migration().v1repo(tmpdir(self))
        (root / '.gitignore').write_text('.ai_state/sprints/*/scratch/\n')
        git(root, 'add', '.gitignore')
        git(root, 'commit', '-qm', 'ignore')
        (root / '.ai_state/sprints/2026-09-01-done-one/scratch').mkdir()
        (root / '.ai_state/sprints/2026-09-01-done-one/scratch/secret.env').write_text('T=1\n')
        (root / '.ai_state/sprints/archive/2026/2026-07-01-a/untracked-notes.md').write_text('n\n')
        (root / '.ai_state/requirements/draft-untracked.md').write_text('d\n')
        out = ok(self, athena('migrate', '--to', '10.1', cwd=root)).stdout
        self.assertIn('stay untracked', out)
        for name in ('secret.env', 'untracked-notes.md', 'draft-untracked.md'):
            self.assertNotIn(name, staged(root))
        self.assertFalse(list((root / '.ai_state/archive').glob('2026-07.tar.*')), 'a month holding loose files is not packed')
        git(root, 'reset', '-q', '--hard', 'pre-athena-10.1-state')
        for rel in ('archive/sprints/2026-09/2026-09-01-done-one/scratch/secret.env',
                    'archive/sprints/2026-07/2026-07-01-a/untracked-notes.md', 'docs/requirements/draft-untracked.md'):
            self.assertTrue((root / '.ai_state' / rel).is_file(), rel)

    def test_v2_remigrate_keeps_the_current_sprint_and_reports_the_real_tag(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        git(root, 'commit', '-qm', 'start')
        git(root, 'tag', 'pre-athena-10.1-state')
        out = ok(self, athena('migrate', '--to', '10.1', cwd=root)).stdout
        self.assertIn('keep | sprints/s-x', out)
        self.assertNotIn('status: "paused"', (root / '.ai_state/sprints/s-x/design.md').read_text())
        self.assertRegex(out, r'git reset --hard pre-athena-10\.1-state-\d+')

    def test_migrate_refuses_collisions_before_moving_anything(self):
        root = Migration().v1repo(tmpdir(self))
        (root / '.ai_state/decisions').mkdir()
        (root / '.ai_state/decisions/2026-07-01-decision-a.md').write_text('clash\n')
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'clash')
        before = snapshot(root)
        run = athena('migrate', '--to', '10.1', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('already exists', run.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertEqual(git(root, 'tag').stdout.strip(), '')


class Round2(unittest.TestCase):
    def test_comments_inside_blocks_and_other_lists(self):
        tmp = tmpdir(self)
        items = tmp / 'items.yaml'
        items.write_bytes(b'milestones:\r\n  - id: M1\r\nitems:\r\n  - slug: x\r\n    deferred:\r\n      # why we wait\r\n      reason: "old"\r\n'
                          b'    done:\r\n      commit: abc\r\n\r\n      # note\r\n      review: r\r\n  - slug: y\r\n    status: pending\r\n')
        out = node("const s=require(process.argv[1]);s.setItem(process.argv[2],'x',{deferred:{reason:'p'},done:{after:'a'}});"
                   "process.stdout.write(s.readItems(process.argv[2]).items.map(i=>i.slug).join(','))", items)
        self.assertEqual(out, 'x,y')
        raw = items.read_bytes()
        self.assertNotIn(b'\n', raw.replace(b'\r\n', b''))
        data = yaml.safe_load(raw.decode())
        self.assertEqual(data['items'][0], {'slug': 'x', 'deferred': {'reason': 'p'}, 'done': {'after': 'a'}})
        doc = tmp / 'i.md'
        doc.write_text('---\nroute:\n  # history\n  - "a"\n  - "b"\nstage: ""\n---\n')
        node("require(process.argv[1]).setFields(process.argv[2],{route_push:'c'})", doc)
        self.assertEqual(yaml.safe_load(doc.read_text().split('---')[1])['route'], ['c', 'a', 'b'])

    def test_ship_stages_review_json_and_keeps_path_ignored_files_ignored(self):
        root = v2project(tmpdir(self))
        (root / '.gitignore').write_text('.ai_state/sprints/*/scratch/\n')
        git(root, 'add', '.gitignore')
        git(root, 'commit', '-qm', 'ignore')
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / '.ai_state/sprints/s-x/scratch').mkdir()
        (root / '.ai_state/sprints/s-x/scratch/secret.env').write_text('TOKEN=1\n')
        ship_ready(self, root, 's-x')
        ok(self, athena('ship', cwd=root))
        self.assertIn(f'.ai_state/archive/sprints/{MONTH}/s-x/review.json', staged(root))
        self.assertNotIn('secret.env', git(root, 'status', '--porcelain', '--untracked-files=all').stdout, 'still ignored at the new path')
        self.assertIn('.ai_state/archive/.gitignore', staged(root))

    def test_duplicate_destinations_block_before_anything_moves(self):
        root = Migration().v1repo(tmpdir(self))
        (root / '.ai_state/sprints/2026-07-01-a').mkdir()
        (root / '.ai_state/sprints/2026-07-01-a/design.md').write_text('hot twin\n')
        (root / '.ai_state/sprints/2026-07-01-a/log.md').write_text('- 2026-07-01 shipped (evidence x)\n')
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'twin')
        before = snapshot(root)
        run = athena('migrate', '--to', '10.1', cwd=root)
        self.assertEqual(run.returncode, 1)
        self.assertIn('both move to archive/sprints/2026-07/2026-07-01-a', run.stderr)
        self.assertEqual(snapshot(root), before)

    def test_allow_reads_waives_only_the_read_check_and_logs_why(self):
        root = Migration().v1repo(tmpdir(self))
        (root / 'old.js').write_text('// see .ai_state/harness-patches.md\n')
        git(root, 'add', 'old.js')
        git(root, 'commit', '-qm', 'mention')
        self.assertEqual(athena('migrate', '--to', '10.1', cwd=root).returncode, 1)
        out = ok(self, athena('migrate', '--to', '10.1', '--allow-reads', 'frozen comment only', cwd=root)).stdout
        self.assertIn('runtime-read check waived: frozen comment only', out)


if __name__ == '__main__':
    unittest.main()
