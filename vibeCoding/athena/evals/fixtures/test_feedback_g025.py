"""G-025: a cross-repo check is the caller's evidence, bound to the target repository's tree.

`athena run -- npm test --prefix <other repo>` was charged to the other repo's active sprint (or
dropped when it had none), so a cross-repo AC could not be proven in the repo that ran the check.
"""
import json
import unittest

from gate_harness import PLATFORMS, athena, call, check_file, git, project, tmpdir
from test_feedback_ql import Fixture, evidence
from test_review_cli import accept
from test_state_cli import ok, v2project


def node_target(tmp, name='agent', **kwargs):
    root = project(tmp, name=name, **kwargs)
    (root / 'package.json').write_text(json.dumps({'scripts': {'test': 'node --test check.test.cjs'}}))
    (root / 'check.test.cjs').write_text("require('node:test')('cross', () => {});\n")
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', 'cross test')
    return root


class CrossRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, name='harness', sprint='harness-sprint')

    def test_target_with_active_sprint_records_to_caller_with_target_marks(self):
        target = node_target(self.tmp, sprint='agent-sprint')
        run = athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root)
        ok(self, run)
        self.assertEqual(evidence(target, 'agent-sprint'), [], 'the target sprint did not start this check')
        rows = evidence(self.root, 'harness-sprint')
        self.assertEqual(len(rows), 1, run.stderr)
        row = rows[0]
        self.assertEqual((row['target'], row['target_repo'], row['kind'], row['provable'], row['covers']),
                         (str(target), str(target), 'test', True, ['AC1']))
        self.assertEqual(row['target_head'], git(target, 'rev-parse', 'HEAD').stdout.strip())
        self.assertRegex(row['target_tree'], r'^[0-9a-f]{40,64}$')

    def test_idle_target_ledger_records_to_caller(self):
        target = node_target(self.tmp, path='', stage='', sprint='')
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        self.assertEqual(len(evidence(self.root, 'harness-sprint')), 1)

    def test_idle_caller_records_nowhere(self):
        target = node_target(self.tmp, sprint='agent-sprint')
        idle = project(self.tmp, name='idle', path='', stage='', sprint='')
        run = athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=idle)
        ok(self, run)
        self.assertIn('no active sprint', run.stderr)
        self.assertEqual(evidence(target, 'agent-sprint'), [])

    def test_caller_without_ledger_keeps_target_attribution(self):
        target = node_target(self.tmp, sprint='agent-sprint')
        plain = self.tmp / 'plain'
        plain.mkdir()
        ok(self, athena('run', '--', 'npm', 'test', '--prefix', str(target), cwd=plain))
        self.assertEqual(len(evidence(target, 'agent-sprint')), 1)

    def test_collector_never_charges_the_target_sprint(self):
        target = node_target(self.tmp, sprint='agent-sprint')
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                call(platform, 'post_bash', self.root, command=f'npm test --prefix {target}', exit=0)
                self.assertEqual(evidence(target, 'agent-sprint'), [])


class CrossRepoShip(unittest.TestCase):
    def ready(self):
        tmp = tmpdir(self)
        root = v2project(tmp)
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'cross', cwd=root))
        design = root / '.ai_state/sprints/cross/design.md'
        design.write_text(design.read_text() + '\n- AC1: links test passes\n')
        target = node_target(tmp, sprint='agent-sprint')
        ok(self, athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(target), cwd=root))
        self.assertEqual(len(evidence(root, 'cross')), 1)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, 'VERDICT: PASS\n'))
        return root, target

    def test_cross_repo_evidence_ships(self):
        root, _ = self.ready()
        ok(self, athena('ship', cwd=root))

    def test_target_edit_after_run_blocks_ship(self):
        root, target = self.ready()
        (target / 'app.js').write_text('changed after passing test\n')
        run = athena('ship', cwd=root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)


class SprintOverride(Fixture):
    """Fixture: x-feat paused, y-bug active."""

    def test_paused_sprint_override(self):
        run = athena('run', '--sprint', 'x-feat', '--covers', 'AC1', '--', 'node', '--test', check_file(self.root), cwd=self.root)
        ok(self, run)
        self.assertEqual(evidence(self.root, 'y-bug'), [])
        rows = evidence(self.root, 'x-feat')
        self.assertEqual((len(rows), rows[0]['sprint'], rows[0]['provable']), (1, 'x-feat', True))

    def test_override_with_cross_repo_target_binds_target(self):
        target = node_target(self.tmp, sprint='agent-sprint')
        ok(self, athena('run', '--sprint', 'x-feat', '--', 'npm', 'test', '--prefix', str(target), cwd=self.root))
        rows = evidence(self.root, 'x-feat')
        self.assertEqual((len(rows), rows[0]['target_repo']), (1, str(target)))
        self.assertEqual(evidence(target, 'agent-sprint'), [])

    def test_unknown_sprint_fails_without_running(self):
        marker = self.tmp / 'ran'
        run = athena('run', '--sprint', 'nope', '--', 'touch', str(marker), cwd=self.root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('nope', run.stderr)
        self.assertFalse(marker.exists())

    def test_same_repo_worktree_rules_unchanged(self):
        wt = self.worktree('proj-x', 'feat/x-feat')
        ok(self, athena('run', '--', f'cd {wt} && node --test {check_file(self.root)}', cwd=self.root))
        rows = evidence(self.root, 'x-feat')
        self.assertEqual(len(rows), 1)
        self.assertNotIn('target_repo', rows[0])
        self.assertEqual(evidence(self.root, 'y-bug'), [])


if __name__ == '__main__':
    unittest.main()
