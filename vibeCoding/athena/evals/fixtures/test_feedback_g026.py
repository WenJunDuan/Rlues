"""G-026: a cross-repo sprint (code in another repository, ledger in this one) was reviewed and proven
against the ledger repo's tree: the packet's Changes listed only the ledger's files, and every ledger
source change forced a new packet and new evidence. design frontmatter `repo:` names the repository
under review; review and evidence bind to its tree.
"""
import re
import unittest

from gate_harness import athena, git, tmpdir
from test_feedback_g025 import node_target
from test_review_cli import accept
from test_state_cli import ok, v2project


class RepoField(unittest.TestCase):
    def setUp(self):
        tmp = tmpdir(self)
        self.root = v2project(tmp, name='links')
        self.target = node_target(tmp, name='plugins', path='', stage='', sprint='')
        base = git(self.target, 'rev-parse', '--short', 'HEAD').stdout.strip()
        (self.target / 'skill.js').write_text('module.exports = "skill";\n')
        git(self.target, 'add', '-A')
        git(self.target, 'commit', '-qm', 'feat: skill')
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 'cross', cwd=self.root))
        design = self.root / '.ai_state/sprints/cross/design.md'
        text = re.sub(r'base_commit: "[^"]*"', f'base_commit: "{base}"', design.read_text())
        design.write_text(text.replace('review_ignore: []', 'review_ignore: []\nrepo: "../plugins"') + '\n- AC1: skill test passes\n')
        ok(self, athena('sprint', 'stage', 'impl', cwd=self.root))

    def prepare(self):
        prep = ok(self, athena('review', 'prepare', cwd=self.root)).stdout
        run = re.search(r'^run (\S+)', prep, re.M).group(1)
        return (self.root / f'.ai_state/.runtime/review/{run}/packet.md').read_text()

    def ledger_edit(self):
        (self.root / 'app.js').write_text('module.exports = "ledger moved on";\n')

    def test_packet_changes_are_the_target_repo(self):
        self.ledger_edit()
        packet = self.prepare()
        self.assertIn(f'source repo: {self.target}', packet)
        changes = packet.split('## Changes (base → current tree)')[1].split('## Evidence')[0]
        self.assertIn('skill.js', changes)
        self.assertNotIn('app.js', changes)

    def test_ledger_source_change_keeps_the_packet(self):
        self.prepare()
        self.ledger_edit()
        (self.root / '.ai_state/notes.md').write_text('ledger only\n')
        ok(self, accept(self.root, 'VERDICT: PASS\n'))
        self.assertIn('(current)', ok(self, athena('review', 'show', cwd=self.root)).stdout)

    def test_target_change_invalidates_the_packet(self):
        self.prepare()
        (self.target / 'skill.js').write_text('module.exports = "edited";\n')
        run = accept(self.root, 'VERDICT: PASS\n')
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertIn('skill.js', run.stderr)

    def test_evidence_binds_the_target_tree(self):
        ok(self, athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(self.target), cwd=self.root))
        self.prepare()
        ok(self, accept(self.root, 'VERDICT: PASS\n'))
        self.ledger_edit()
        self.assertNotIn('stale', athena('status', cwd=self.root).stdout)
        (self.target / 'skill.js').write_text('module.exports = "edited";\n')
        run = athena('ship', cwd=self.root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)

    def test_ships_after_ledger_change(self):
        ok(self, athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(self.target), cwd=self.root))
        self.prepare()
        ok(self, accept(self.root, 'VERDICT: PASS\n'))
        self.ledger_edit()
        ok(self, athena('ship', cwd=self.root))

    def test_subdirectory_repo_binds_the_whole_work_tree(self):
        (self.target / 'docs').mkdir()
        (self.target / 'docs/readme.md').write_text('docs\n')
        git(self.target, 'add', '-A')
        git(self.target, 'commit', '-qm', 'docs dir')
        design = self.root / '.ai_state/sprints/cross/design.md'
        design.write_text(design.read_text().replace('repo: "../plugins"', 'repo: "../plugins/docs"'))
        ok(self, athena('run', '--covers', 'AC1', '--', 'npm', 'test', '--prefix', str(self.target), cwd=self.root))
        self.assertIn(f'source repo: {self.target} ', self.prepare())
        ok(self, accept(self.root, 'VERDICT: PASS\n'))
        (self.target / 'skill.js').write_text('module.exports = "edited outside docs/";\n')
        run = athena('ship', cwd=self.root)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('H2', run.stderr)

    def test_missing_repo_is_refused(self):
        design = self.root / '.ai_state/sprints/cross/design.md'
        design.write_text(design.read_text().replace('repo: "../plugins"', 'repo: "../nowhere"'))
        run = athena('review', 'prepare', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('not a git work tree', run.stderr)


if __name__ == '__main__':
    unittest.main()
