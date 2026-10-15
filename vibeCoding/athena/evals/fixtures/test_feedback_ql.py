"""quantum-links feedback: evidence / H1 attributed by worktree, tidy keeps paused sprints, state unstaged.

G-008/G-009/G-012/G-013: `athena run` and the post-tool collector charged commands run in a sibling
worktree (or aimed at one with --prefix / -C / cd) to whatever sprint the main checkout had active.
G-010: H1 judged an isolated worktree writer by the main checkout's active sprint.
G-011: `athena tidy` archived paused in-flight sprints (item → deferred) when the hot layer was > 3.
Merge: CLI state writes were staged, so a plain `git merge` refused until `git reset`.
"""
import json
from pathlib import Path
import unittest

from gate_harness import GOOD_DESIGN, PLATFORMS, athena, call, check_file, git, project, tmpdir
from test_state_cli import item, ok, v2project

GOOD_AC = '\n- AC1: add returns 2\n'


def evidence(root, slug):
    path = Path(root) / f'.ai_state/.runtime/evidence/{slug}.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def with_ac(root, slug):
    design = Path(root) / f'.ai_state/sprints/{slug}/design.md'
    design.write_text(design.read_text(encoding='utf-8') + GOOD_AC, encoding='utf-8')


class Fixture(unittest.TestCase):
    """Sprint `x-feat` started then paused; sprint `y-bug` active. Worktrees are siblings of root."""

    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = root = v2project(self.tmp)
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'x-feat', cwd=root))
        with_ac(root, 'x-feat')
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=root))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 'y-bug', '--path', 'Feature', cwd=root))
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'state')

    def worktree(self, name, branch):
        wt = self.tmp / name
        git(self.root, 'worktree', 'add', '-q', str(wt), '-b', branch)
        return wt


class EvidenceAttribution(Fixture):
    def test_run_in_worktree_named_after_paused_sprint_goes_to_it(self):
        wt = self.worktree('proj-x', 'feat/x-feat')
        run = athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(self.root), cwd=wt)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(evidence(self.root, 'y-bug'), [], 'never charged to the active sprint')
        rows = evidence(self.root, 'x-feat')
        self.assertEqual(len(rows), 1, run.stderr)
        self.assertEqual((rows[0]['sprint'], rows[0]['provable'], rows[0]['covers']), ('x-feat', True, ['AC1']))

    def test_run_in_unmapped_worktree_is_not_recorded(self):
        wt = self.worktree('proj-other', 'misc')
        run = athena('run', '--', 'node', '--test', check_file(self.root), cwd=wt)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('maps to no sprint', run.stderr)
        self.assertEqual(evidence(self.root, 'y-bug') + evidence(self.root, 'x-feat'), [])

    def test_design_frontmatter_worktree_maps(self):
        wt = self.worktree('proj-anything', 'anything')
        design = self.root / '.ai_state/sprints/x-feat/design.md'
        design.write_text(design.read_text(encoding='utf-8').replace('---\n', f'---\nworktree: "../proj-anything"\n', 1), encoding='utf-8')
        ok(self, athena('run', '--', 'node', '--test', check_file(self.root), cwd=wt))
        self.assertEqual(len(evidence(self.root, 'x-feat')), 1)
        self.assertEqual(evidence(self.root, 'y-bug'), [])

    def test_cd_and_prefix_targets_attribute_by_target(self):
        wt = self.worktree('proj-x', 'feat/x-feat')
        other = self.worktree('proj-other', 'misc')
        test = check_file(self.root)
        ok(self, athena('run', '--', f'cd {wt} && node --test {test}', cwd=self.root))
        self.assertEqual(len(evidence(self.root, 'x-feat')), 1)
        ok(self, athena('run', '--', 'git', '-C', str(other), 'diff', '--check', cwd=self.root))
        ok(self, athena('run', '--', 'npm', '--prefix', str(other), '--version', cwd=self.root))
        self.assertEqual(evidence(self.root, 'y-bug'), [], 'aimed at an unmapped worktree → not the active sprint')
        ok(self, athena('run', '--', 'node', '--test', test, cwd=self.root))
        self.assertEqual(len(evidence(self.root, 'y-bug')), 1, 'the main checkout still records to the active sprint')

    def test_collector_attributes_by_worktree(self):
        mapped = self.worktree('proj-x', 'feat/x-feat')
        other = self.worktree('proj-other', 'misc')
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                before = len(evidence(self.root, 'x-feat'))
                call(platform, 'post_bash', mapped, command='npm test', exit=0)
                call(platform, 'post_bash', other, command='npm test', exit=1)
                self.assertEqual(len(evidence(self.root, 'x-feat')), before + 1)
                self.assertEqual(evidence(self.root, 'y-bug'), [])


class BackgroundLoad(unittest.TestCase):
    """G-002: a backgrounded load next to a foreground check; only the foreground status decides."""

    def verdict(self, line):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        test = check_file(root)
        run = athena('run', '--', line.format(t=test), cwd=root)
        return run.stderr

    def test_background_load_then_foreground_check_is_provable(self):
        self.assertIn('provable=true', self.verdict('node --test {t} > /dev/null & node --test {t}'))
        self.assertIn('provable=true', self.verdict('node --test {t} > /dev/null 2>&1 & node --test {t} && node --test {t}'))

    def test_backgrounded_check_alone_stays_unprovable(self):
        self.assertIn('provable=false', self.verdict('node --test {t} & sleep 0'))
        self.assertIn('provable=false', self.verdict('node --test {t} && true & sleep 0'))


class H1ByWorktree(Fixture):
    def test_mapped_worktree_is_judged_by_its_own_design(self):
        wt = self.worktree('proj-x', 'feat/x-feat')
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                verdict = call(platform, 'write', wt, file=wt / 'app.js')
                self.assertFalse(verdict.blocked, verdict.reason)
        # the active sprint (template design, no AC) still gates the main checkout
        self.assertTrue(call('cc', 'write', self.root, file=self.root / 'app.js').blocked)

    def test_mapped_worktree_without_ac_is_blocked_naming_its_sprint(self):
        wt = self.worktree('proj-y', 'fix/y-bug-2')
        verdict = call('cc', 'write', wt, file=wt / 'app.js')
        self.assertTrue(verdict.blocked)
        self.assertIn('y-bug', verdict.reason)

    def test_unmapped_worktree_falls_back_to_active_sprint(self):
        wt = self.worktree('proj-other', 'misc')
        verdict = call('cc', 'write', wt, file=wt / 'app.js')
        self.assertTrue(verdict.blocked)
        self.assertIn('H1', verdict.reason)


class TidyKeepsPaused(unittest.TestCase):
    def test_paused_in_flight_sprints_stay_hot(self):
        root = v2project(tmpdir(self))
        statuses = ['paused', 'paused', 'paused', 'dropped', 'active']
        for i, status in enumerate(statuses):
            d = root / f'.ai_state/sprints/2026-01-0{i}-p'
            d.mkdir(parents=True)
            (d / 'design.md').write_text(f'---\nstatus: "{status}"\nroadmap: "r"\nitem: "x"\n---\n')
        out = ok(self, athena('tidy', cwd=root)).stdout
        left = sorted(d.name for d in (root / '.ai_state/sprints').iterdir() if d.is_dir())
        self.assertEqual(left, ['2026-01-00-p', '2026-01-01-p', '2026-01-02-p', '2026-01-04-p'], out)
        self.assertNotEqual(item(root, 'x')['status'], 'deferred')
        self.assertIn('paused', out)


class StateNotStaged(unittest.TestCase):
    def test_cli_state_writes_leave_the_index_clean_so_git_merge_works(self):
        root = v2project(tmpdir(self))
        git(root, 'switch', '-qc', 'side')
        (root / 'side.js').write_text('1\n')
        git(root, 'add', 'side.js')
        git(root, 'commit', '-qm', 'side')
        git(root, 'switch', '-q', '-')
        (root / 'main.js').write_text('1\n')
        git(root, 'add', 'main.js')
        git(root, 'commit', '-qm', 'main')
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'x-feat', cwd=root))
        ok(self, athena('issue', 'add', '--type', 'gate', '--text', 'a note', cwd=root))
        self.assertEqual(git(root, 'diff', '--cached', '--name-only').stdout, '')
        merge = git(root, 'merge', '--no-ff', '--no-commit', 'side', check=False)
        self.assertEqual(merge.returncode, 0, merge.stdout + merge.stderr)
        git(root, 'add', '-A', '.ai_state')
        git(root, 'commit', '-qm', 'merge side with state')
        files = git(root, 'diff', '--name-only', 'HEAD^1', 'HEAD').stdout
        self.assertIn('.ai_state/sprints/x-feat/design.md', files)


if __name__ == '__main__':
    unittest.main()
