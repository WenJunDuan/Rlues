"""athena writer dispatch / collect / status on real git repos (athena-10-1-5 S2 AC5)."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from gate_harness import GATE, athena, call, git, tmpdir
from test_state_cli import fm, ok, snapshot, v2project
from test_status_matrix import sprint


def record(root, slug='s-x'):
    return json.loads((root / f'.ai_state/sprints/{slug}/external-writer.json').read_text(encoding='utf-8'))


def a1(root):
    """Advisory A1 (writer provenance) for the project, as the ship gate would compute it."""
    script = ("const ctx=require(process.argv[1]+'/lib/context.cjs').load(process.argv[2]);"
              "process.stdout.write(JSON.stringify(require(process.argv[1]+'/rules/advisory.cjs').CHECKS.A1(ctx)));")
    return subprocess.run(['node', '-e', script, str(GATE), str(root)], capture_output=True, text=True, check=True).stdout


def dispatch(testcase, root, *extra):
    run = ok(testcase, athena('writer', 'dispatch', '--tool', 'grok', '--family', 'xai', *extra, cwd=root))
    return run, Path(record(root)['worktree'])


def writer_commit(wt, name='app.js', body='module.exports = 2;\n'):
    (wt / name).write_text(body, encoding='utf-8')
    git(wt, 'add', '-A')
    git(wt, 'commit', '-qm', f'writer: {name}')
    return git(wt, 'rev-parse', 'HEAD').stdout.strip()


def main_commit(root, name, body):
    (root / name).write_text(body, encoding='utf-8')
    git(root, 'add', '--', name)
    git(root, 'commit', '-qm', f'main: {name}', '--', name)


def refused(testcase, run, code=1):
    testcase.assertEqual(run.returncode, code, run.stderr + run.stdout)
    testcase.assertRegex(run.stderr.rstrip('\n').split('\n')[-1], r'^next: \S')
    return run


class WriterDispatch(unittest.TestCase):
    def setUp(self):
        self.root = v2project(tmpdir(self))
        sprint(self, self.root)

    def test_dispatch_creates_worktree_record_and_parallel_writers(self):
        root = self.root
        base = git(root, 'rev-parse', 'HEAD').stdout.strip()
        brief = root.parent / 'brief.md'
        brief.write_text('do the thing\n', encoding='utf-8')
        run, wt = dispatch(self, root, '--model', 'grok-5', '--brief', str(brief))
        self.assertEqual(wt, Path(f'{root}-wt') / 's-x-grok')  # sibling of the repo, not nested in it
        self.assertTrue((wt / 'app.js').is_file())
        self.assertIn(str(wt), git(root, 'worktree', 'list', '--porcelain').stdout)
        self.assertEqual(git(wt, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip(), 'writer/s-x-grok')
        rec = record(root)
        self.assertEqual((rec['tool'], rec['family'], rec['model'], rec['status'], rec['external']), ('grok', 'xai', 'grok-5', 'dispatched', True))
        self.assertEqual((rec['base_commit'], rec['branch'], rec['parallel_writers_before']), (base, 'writer/s-x-grok', 1))
        self.assertEqual(rec['brief_sha256'], hashlib.sha256(b'do the thing\n').hexdigest())
        self.assertTrue(rec['dispatched_at'])
        self.assertEqual(fm(root / '.ai_state/_index.md')['parallel_writers'], '2')
        for needle in (str(wt), 'writer/s-x-grok', 'Do not push', '.ai_state/', 'not evidence', 'athena writer collect'):
            self.assertIn(needle, run.stdout)
        shown = ok(self, athena('writer', 'status', cwd=root)).stdout
        self.assertIn('writer grok (xai, grok-5) [dispatched]', shown)
        self.assertEqual(json.loads(ok(self, athena('writer', 'status', '--json', cwd=root)).stdout)['branch'], 'writer/s-x-grok')

    def test_record_satisfies_a1_and_window_turns_h4_on(self):
        root = self.root
        self.assertIn('no generator/external writer recorded', a1(root))
        dispatch(self, root)
        self.assertEqual(a1(root), 'null')
        self.assertFalse(call('cc', 'agent', root, type='general-purpose', task='edit app.js', isolation='worktree').blocked)
        verdict = call('cc', 'agent', root, type='general-purpose', task='edit app.js')
        self.assertTrue(verdict.blocked)
        self.assertIn('parallel_writers=2', verdict.reason)

    def test_second_dispatch_is_refused(self):
        root = self.root
        dispatch(self, root)
        before = snapshot(root)
        run = refused(self, athena('writer', 'dispatch', '--tool', 'codex', '--family', 'openai', cwd=root))
        self.assertIn('already open', run.stderr)
        self.assertIn('next: athena writer collect', run.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertFalse((Path(f'{root}-wt') / 's-x-codex').exists())

    def test_usage_and_refusals_name_the_next_command(self):
        root = self.root
        for argv in (['writer'], ['writer', 'nope'], ['writer', 'dispatch'], ['writer', 'dispatch', '--tool', 'grok'],
                     ['writer', 'dispatch', '--tool', 'a b', '--family', 'xai'], ['writer', 'collect', '--bogus']):
            run = refused(self, athena(*argv, cwd=root), code=2)
            self.assertIn('usage:', run.stderr)
        self.assertIn('no external writer recorded', refused(self, athena('writer', 'collect', cwd=root)).stderr)
        self.assertEqual(athena('writer', 'status', cwd=root).returncode, 0)
        idle = v2project(tmpdir(self), 'idle')
        self.assertIn('no sprint in flight', refused(self, athena('writer', 'dispatch', '--tool', 'grok', '--family', 'xai', cwd=idle)).stderr)


class WriterCollect(unittest.TestCase):
    def setUp(self):
        self.root = v2project(tmpdir(self))
        sprint(self, self.root)
        _, self.wt = dispatch(self, self.root)

    def test_collect_fast_forward(self):
        root, wt = self.root, self.wt
        tip = writer_commit(wt)
        run = ok(self, athena('writer', 'collect', cwd=root))
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout.strip(), tip)
        self.assertEqual((root / 'app.js').read_text(), 'module.exports = 2;\n')
        rec = record(root)
        self.assertEqual((rec['status'], rec['merge'], rec['head'], rec['commits']), ('collected', 'ff', tip, [tip]))
        self.assertTrue(rec['collected_at'])
        self.assertEqual(fm(root / '.ai_state/_index.md')['parallel_writers'], '1')  # restored
        self.assertFalse(wt.exists())
        self.assertNotIn(str(wt), git(root, 'worktree', 'list', '--porcelain').stdout)
        self.assertEqual(git(root, 'rev-parse', 'refs/heads/writer/s-x-grok').stdout.strip(), tip)  # branch kept
        for needle in ('athena run', 'not evidence', 'athena review prepare', 'writer family is xai', 'different family'):
            self.assertIn(needle, run.stdout)
        self.assertIn('already collected', refused(self, athena('writer', 'collect', cwd=root)).stderr)
        # a collected window is closed: the next dispatch is allowed and keeps the history
        ok(self, athena('writer', 'dispatch', '--tool', 'codex', '--family', 'openai', cwd=root))
        self.assertEqual([p['tool'] for p in record(root)['previous']], ['grok'])

    def test_collect_keep_worktree(self):
        writer_commit(self.wt)
        (self.wt / 'scratch.txt').write_text('left over\n', encoding='utf-8')  # dirty is fine when kept
        ok(self, athena('writer', 'collect', '--keep-worktree', cwd=self.root))
        self.assertTrue(self.wt.exists())
        self.assertFalse(record(self.root)['worktree_removed'])

    def test_collect_conflict_changes_nothing(self):
        root, wt = self.root, self.wt
        writer_commit(wt, body='module.exports = "writer";\n')
        main_commit(root, 'app.js', 'module.exports = "main";\n')
        head, before = git(root, 'rev-parse', 'HEAD').stdout, snapshot(root)
        porcelain = git(root, 'status', '--porcelain').stdout
        run = refused(self, athena('writer', 'collect', cwd=root))
        self.assertIn('conflicts in 1 file(s)', run.stderr)
        self.assertIn('\n  app.js\n', run.stderr)
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout, head)
        self.assertEqual(snapshot(root), before)
        self.assertEqual(git(root, 'status', '--porcelain').stdout, porcelain)
        self.assertFalse((root / '.git/MERGE_HEAD').exists())
        self.assertEqual(record(root)['status'], 'dispatched')
        self.assertEqual(fm(root / '.ai_state/_index.md')['parallel_writers'], '2')  # window still open
        self.assertTrue(wt.exists())

    def test_clean_non_ff_prints_the_merge_and_collects_after_it(self):
        root, wt = self.root, self.wt
        tip = writer_commit(wt)
        main_commit(root, 'other.js', 'module.exports = 0;\n')
        head, before = git(root, 'rev-parse', 'HEAD').stdout, snapshot(root)
        run = refused(self, athena('writer', 'collect', cwd=root))
        self.assertIn(f'git -C {root} merge --no-ff writer/s-x-grok', run.stderr)
        self.assertIn(f'next: git -C {root} status', run.stderr)  # sprint state is staged: git would refuse the merge
        self.assertIn('commit staged state together with implementation', run.stderr)
        self.assertEqual((git(root, 'rev-parse', 'HEAD').stdout, snapshot(root)), (head, before))  # no merge commit made
        git(root, 'commit', '-qm', 'chore: athena state')
        self.assertIn(f'next: git -C {root} merge --no-ff writer/s-x-grok', refused(self, athena('writer', 'collect', cwd=root)).stderr)
        git(root, 'merge', '--no-ff', '-qm', 'merge writer', 'writer/s-x-grok')
        ok(self, athena('writer', 'collect', cwd=root))
        rec = record(root)
        self.assertEqual((rec['status'], rec['merge'], rec['head']), ('collected', 'already-merged', tip))
        self.assertEqual(fm(root / '.ai_state/_index.md')['parallel_writers'], '1')
        self.assertFalse(wt.exists())

    def test_no_commit_or_dirty_worktree_is_refused(self):
        root, wt = self.root, self.wt
        self.assertIn('no commit beyond base', refused(self, athena('writer', 'collect', cwd=root)).stderr)
        writer_commit(wt)
        (wt / 'app.js').write_text('module.exports = 9;\n', encoding='utf-8')
        head = git(root, 'rev-parse', 'HEAD').stdout
        self.assertIn('uncommitted changes', refused(self, athena('writer', 'collect', cwd=root)).stderr)
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout, head)
        self.assertEqual(record(root)['status'], 'dispatched')

    def test_collect_refuses_a_different_target_branch(self):
        root, wt = self.root, self.wt
        original = git(root, 'symbolic-ref', '--short', 'HEAD').stdout.strip()
        writer_commit(wt)
        git(root, 'switch', '-c', 'other-work')
        before, head = snapshot(root), git(root, 'rev-parse', 'HEAD').stdout
        run = refused(self, athena('writer', 'collect', cwd=root))
        self.assertIn('target branch changed', run.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout, head)
        self.assertTrue(wt.exists())
        git(root, 'switch', original)
        ok(self, athena('writer', 'collect', cwd=root))

    def test_collect_refuses_writer_changes_to_main_state(self):
        root, wt = self.root, self.wt
        writer_commit(wt, '.ai_state/queue.md', '# External rewrite\n')
        before, head = snapshot(root), git(root, 'rev-parse', 'HEAD').stdout
        run = refused(self, athena('writer', 'collect', cwd=root))
        self.assertIn('.ai_state/queue.md', run.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertEqual(git(root, 'rev-parse', 'HEAD').stdout, head)
        self.assertEqual(record(root)['status'], 'dispatched')
        self.assertTrue(wt.exists())

    def test_rebased_writer_can_inherit_main_agents_state_commit(self):
        root, wt = self.root, self.wt
        writer_commit(wt)
        (root / 'main.js').write_text('module.exports = 3;\n')
        git(root, 'add', 'main.js')  # commit the staged sprint state with implementation
        git(root, 'commit', '-qm', 'main implementation and state')
        head = git(root, 'rev-parse', 'HEAD').stdout.strip()
        git(wt, 'rebase', head)
        ok(self, athena('writer', 'collect', cwd=root))
        self.assertEqual((root / 'main.js').read_text(), 'module.exports = 3;\n')
        self.assertEqual(record(root)['status'], 'collected')

    def test_parallel_writers_above_two_is_kept_and_restored(self):
        root = v2project(tmpdir(self), 'three')
        index = root / '.ai_state/_index.md'
        index.write_text(index.read_text().replace('parallel_writers: 1', 'parallel_writers: 3'), encoding='utf-8')
        sprint(self, root)
        _, wt = dispatch(self, root)
        self.assertEqual(fm(index)['parallel_writers'], '3')
        writer_commit(wt)
        ok(self, athena('writer', 'collect', cwd=root))
        self.assertEqual(fm(index)['parallel_writers'], '3')


if __name__ == '__main__':
    unittest.main()
