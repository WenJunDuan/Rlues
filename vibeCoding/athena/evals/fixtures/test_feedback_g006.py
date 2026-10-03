import re
import unittest
from gate_harness import athena, git, tmpdir
from test_state_cli import v2project, ok, fm

class SprintRotation(unittest.TestCase):
    def test_pause_after_implementation_records_impl(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / 'app.js').write_text('module.exports = 2;\n')
        git(root, 'add', '-A'); git(root, 'commit', '-qm', 'implement x')
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=root))
        self.assertEqual(fm(root / '.ai_state/sprints/s-x/design.md')['paused_stage'], 'impl')

    def test_packet_excludes_paused_interval_commits(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        (root / 'own.js').write_text('own\n')
        git(root, 'add', '-A'); git(root, 'commit', '-qm', 'implement x')
        ok(self, athena('sprint', 'pause', '--resume-when', 'after y', cwd=root))
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=root))
        (root / 'other.js').write_text('other\n')
        git(root, 'add', '-A'); git(root, 'commit', '-qm', 'implement y')
        excluded = git(root, 'rev-parse', 'HEAD').stdout.strip()
        ok(self, athena('sprint', 'pause', '--resume-when', 'after x', cwd=root))
        ok(self, athena('sprint', 'resume', 's-x', cwd=root))
        (root / 'own2.js').write_text('own2\n')
        prep = ok(self, athena('review', 'prepare', cwd=root)).stdout
        run = re.search(r'^run (\S+)', prep, re.M).group(1)
        packet = (root / f'.ai_state/.runtime/review/{run}/packet.md').read_text()
        changes = packet.split('## Changes (base → current tree)')[1].split('## Evidence')[0]
        self.assertIn('own.js', changes); self.assertIn('own2.js', changes)
        self.assertNotIn('other.js', changes)
        self.assertIn(excluded, packet)
        self.assertIn('Excluded commits', packet)
