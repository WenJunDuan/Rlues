"""G-016: external-only changes can supply H2 evidence through a no-ledger target."""
import json
import unittest

from gate_harness import athena, git, project, tmpdir
from test_feedback_ql import evidence
from test_review_cli import accept
from test_state_cli import ok, v2project


class ExternalOnlyShip(unittest.TestCase):
    def external_ready(self, subdirectory=False):
        tmp = tmpdir(self)
        root = v2project(tmp)
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'external-only', cwd=root))
        design = root / '.ai_state/sprints/external-only/design.md'
        design.write_text(design.read_text() + '\n- AC1: external test passes\n')
        target = project(tmp, name='plugins', stage=None)
        run_dir = target / 'tests' if subdirectory else target
        run_dir.mkdir(exist_ok=True)
        (run_dir / 'check.test.cjs').write_text("require('node:test')('external', () => {});\n")
        # Keep the outside file dirty: a later rewrite leaves porcelain unchanged.
        (target / 'app.js').write_text('before passing test\n')
        source_before = git(root, 'diff', '--', 'app.js').stdout
        run = athena('run', '--covers', 'AC1', '--', f'cd {run_dir} && node --test check.test.cjs', cwd=root)
        ok(self, run)
        self.assertEqual(len(evidence(root, 'external-only')), 1, run.stderr)
        row = evidence(root, 'external-only')[0]
        self.assertEqual((row['target'], row['provable']), (str(run_dir), True))
        self.assertEqual(git(root, 'diff', '--', 'app.js').stdout, source_before)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, 'VERDICT: PASS\n'))
        self.assertRegex(row['target_tree'], r'^[0-9a-f]{40,64}$')
        return root, target

    def test_external_only_change_can_pass_h2_and_ship(self):
        root, _ = self.external_ready()
        ok(self, athena('ship', cwd=root))

    def test_target_edit_after_run_invalidates_evidence_and_blocks_ship(self):
        root, target = self.external_ready()
        (target / 'app.js').write_text('changed after passing test\n')
        run = athena('ship', cwd=root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)

    def test_rebind_reruns_after_target_edit_and_ship_passes(self):
        root, target = self.external_ready()
        (target / 'app.js').write_text('changed after passing test\n')
        run = athena('run', '--rebind', cwd=root)
        ok(self, run)
        self.assertIn('1 re-run, 0 already on this tree', run.stderr)
        self.assertEqual(len(evidence(root, 'external-only')), 2)
        ok(self, athena('ship', cwd=root))

    def test_subdirectory_evidence_blocks_ship_after_outside_edit(self):
        root, target = self.external_ready(subdirectory=True)
        (target / 'app.js').write_text('changed outside test directory\n')
        run = athena('ship', cwd=root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)

    def test_subdirectory_rebind_reruns_after_outside_edit(self):
        root, target = self.external_ready(subdirectory=True)
        unchanged = athena('run', '--rebind', cwd=root)
        ok(self, unchanged)
        self.assertIn('0 re-run, 1 already on this tree', unchanged.stderr)
        (target / 'app.js').write_text('changed outside test directory\n')
        run = athena('run', '--rebind', cwd=root)
        ok(self, run)
        self.assertIn('1 re-run, 0 already on this tree', run.stderr)
        self.assertEqual(len(evidence(root, 'external-only')), 2)
        ok(self, athena('ship', cwd=root))

    def test_legacy_null_target_tree_does_not_pass_ship_or_skip_rebind(self):
        root, target = self.external_ready()
        ledger = root / '.ai_state/.runtime/evidence/external-only.jsonl'
        row = evidence(root, 'external-only')[0]
        row['target_tree'] = None
        row['target'] = str(target.parent)  # Existing non-Git directory.
        ledger.write_text(json.dumps(row) + '\n')
        run = athena('ship', cwd=root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)
        run = athena('run', '--rebind', cwd=root)
        ok(self, run)
        self.assertIn('1 re-run, 0 already on this tree', run.stderr)
