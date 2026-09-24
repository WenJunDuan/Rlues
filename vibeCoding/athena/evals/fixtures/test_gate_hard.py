"""H1–H4 hard gates through cc / cx / pi, plus fail-closed internals (athena-10-1 S2 AC1, AC2).

H5 lives in test_gate_shell.py; evidence (H2 inputs) in test_gate_evidence.py.
"""
import json
from pathlib import Path
import subprocess
import unittest

from gate_harness import (green, red, ENV, GATE, GOOD_DESIGN, PLATFORMS, athena, call, git, project, set_index, sprint_dir, tmpdir)


class H1DesignFirst(unittest.TestCase):
    def write(self, root, target, platforms=PLATFORMS):
        return {p: call(p, 'write', root, file=target) for p in platforms}

    def assert_all(self, root, target, expected, label):
        for platform, verdict in self.write(root, target).items():
            with self.subTest(label=label, platform=platform):
                self.assertEqual(verdict.blocked, expected, verdict.reason)
                if expected:
                    self.assertIn('H1', verdict.reason)

    def test_missing_design_blocks_and_valid_design_allows(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        self.assert_all(root, root / 'app.js', True, 'no design')
        (sprint_dir(root) / 'design.md').write_text(GOOD_DESIGN, encoding='utf-8')
        self.assert_all(root, root / 'app.js', False, 'design with AC1')

    def test_placeholder_fence_and_prose_do_not_count(self):
        root = project(tmpdir(self), path='Bugfix', stage='design')
        for text in ('## AC\n- AC1: TODO\n- AC2: 功能正常\n', '## AC\n```\n- AC1: example only\n```\n',
                     '## 验收标准\nAC1 is described in prose\n', '- AC1:\n'):
            (sprint_dir(root) / 'design.md').write_text(text, encoding='utf-8')
            self.assert_all(root, root / 'app.js', True, text.splitlines()[-1])
        verdict = call('cc', 'write', root, file=root / 'app.js')
        self.assertIn('合法形态', verdict.reason)

    def test_accepted_line_forms(self):
        root = project(tmpdir(self), path='Quick', stage='impl')
        for text in ('- AC1: returns 2\n', '* AC3：返回 2\n', '- [ ] AC2: returns 2\n', '| AC1 | returns 2 |\n', '- **AC4**: x works for y\n'):
            (sprint_dir(root) / 'design.md').write_text(text, encoding='utf-8')
            self.assert_all(root, root / 'app.js', False, text.strip())

    def test_exempt_targets_paths_and_stages(self):
        tmp = tmpdir(self)
        root = project(tmp, path='System', stage='impl')
        self.assert_all(root, root / '.ai_state/sprints/2026-09-24-s/design.md', False, '.ai_state write')
        self.assert_all(root, tmp / 'outside.txt', False, 'outside the repository')
        self.assert_all(root, Path('/tmp') / 'athena-fixture-scratch.txt', False, '/tmp scratch')
        set_index(root, path='Hotfix')
        self.assert_all(root, root / 'app.js', False, 'Hotfix')
        set_index(root, path='Feature', stage='review')
        self.assert_all(root, root / 'app.js', False, 'stage review (not design/impl)')
        set_index(root, path='', stage='', current_sprint_slug='')
        self.assert_all(root, root / 'app.js', False, 'idle')
        plain = tmp / 'plain'
        plain.mkdir()
        self.assert_all(plain, plain / 'x.js', False, 'no .ai_state')

    def test_cx_apply_patch_any_target_inside_repo_counts(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        mixed = [str(root / '.ai_state/notes.md'), 'src/new.js']
        self.assertTrue(call('cx', 'write', root, file=mixed).blocked)
        only_state = [str(root / '.ai_state/notes.md')]
        self.assertFalse(call('cx', 'write', root, file=only_state).blocked)
        move = {'hook_event_name': 'PreToolUse', 'cwd': str(root), 'tool_name': 'apply_patch',
                'tool_input': {'input': '*** Begin Patch\n*** Update File: .ai_state/a.md\n*** Move to: lib/a.js\n*** End Patch\n'}}
        proc = subprocess.run(['node', str(GATE / 'hook.cjs'), 'PreToolUse', '--platform', 'cx'], input=json.dumps(move),
                              text=True, capture_output=True, env=ENV)
        self.assertEqual(proc.returncode, 2, 'a Move target inside the repo is an implementation write')

    def test_worktree_write_reads_main_checkout_state(self):
        tmp = tmpdir(self)
        root = project(tmp, path='Feature', stage='impl')
        git(root, 'worktree', 'add', '-q', str(tmp / 'wt'))
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertTrue(call(platform, 'write', tmp / 'wt', file=tmp / 'wt/app.js').blocked)
        (sprint_dir(root) / 'design.md').write_text(GOOD_DESIGN, encoding='utf-8')
        for platform in PLATFORMS:
            with self.subTest(platform=platform, design='main'):
                self.assertFalse(call(platform, 'write', tmp / 'wt', file=tmp / 'wt/app.js').blocked)


class H2H3Ship(unittest.TestCase):
    def ship_project(self, path='Feature'):
        root = project(tmpdir(self), path=path, stage='impl', design=GOOD_DESIGN)
        return root

    def stop(self, root, platform='cc', session='s-1'):
        return call(platform, 'stop', root, session=session)

    def test_stop_is_read_only_outside_ship(self):
        root = self.ship_project()
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertFalse(self.stop(root, platform).blocked)

    def test_evidence_then_review_then_pass(self):
        root = self.ship_project()
        set_index(root, stage='ship')
        for platform in PLATFORMS:
            with self.subTest(platform=platform, step='no evidence'):
                verdict = self.stop(root, platform, session=f'a-{platform}')
                self.assertTrue(verdict.blocked)
                self.assertIn('H2', verdict.reason)
        self.assertEqual(red(root).returncode, 1)
        self.assertIn('exited 1', self.stop(root, session='b').reason)
        self.assertEqual(green(root).returncode, 0)
        verdict = self.stop(root, session='c')
        self.assertIn('H3', verdict.reason)
        self.assertIn('missing', verdict.reason)
        tree = json.loads((root / '.ai_state/.runtime/evidence/2026-09-24-s.jsonl').read_text().splitlines()[-1])['tree_sha']
        review = sprint_dir(root) / 'review.json'
        review.write_text(json.dumps({'verdict': 'CONCERNS', 'tree_sha': tree}), encoding='utf-8')
        self.assertIn('CONCERNS', self.stop(root, session='d').reason)
        review.write_text(json.dumps({'verdict': 'PASS', 'tree_sha': tree, 'reviewer': {'family': 'openai'}}), encoding='utf-8')
        for platform in PLATFORMS:
            with self.subTest(platform=platform, step='pass'):
                self.assertFalse(self.stop(root, platform, session=f'e-{platform}').blocked)
        (root / 'app.js').write_text('module.exports = 2;\n', encoding='utf-8')
        verdict = self.stop(root, session='f')
        self.assertTrue(verdict.blocked, 'source changed after evidence + review')
        self.assertIn('H2', verdict.reason)
        (sprint_dir(root) / 'log.md').write_text('- note\n', encoding='utf-8')
        (root / 'app.js').write_text('module.exports = 1;\n', encoding='utf-8')
        self.assertFalse(self.stop(root, session='g').blocked, '.ai_state edits never invalidate the tree')

    def test_quick_and_hotfix_need_no_review(self):
        for path in ('Quick', 'Hotfix'):
            root = self.ship_project(path)
            set_index(root, stage='ship')
            self.assertEqual(green(root).returncode, 0)
            with self.subTest(path=path):
                self.assertFalse(self.stop(root).blocked, self.stop(root).reason)

    def test_cross_family_review_flag_makes_a10_hard(self):
        root = self.ship_project()
        set_index(root, stage='ship', flags='{cross_family_review: true}')
        green(root)
        tree = json.loads((root / '.ai_state/.runtime/evidence/2026-09-24-s.jsonl').read_text().splitlines()[-1])['tree_sha']
        (sprint_dir(root) / 'review.json').write_text(json.dumps({'verdict': 'PASS', 'tree_sha': tree, 'reviewer': {'family': 'anthropic'}}))
        self.assertIn('cross_family_review', self.stop(root, 'cc').reason)
        self.assertFalse(self.stop(root, 'cx').blocked, 'openai author, anthropic reviewer')


class H4Isolation(unittest.TestCase):
    def test_red_zone_writer_needs_isolation(self):
        tmp = tmpdir(self)
        root = project(tmp, path='System', stage='impl', design=GOOD_DESIGN)
        for platform in ('cc', 'cx'):
            with self.subTest(platform=platform):
                verdict = call(platform, 'agent', root, type='generator', task='implement AC1')
                self.assertTrue(verdict.blocked)
                self.assertIn('H4', verdict.reason)
                self.assertFalse(call(platform, 'agent', root, type='explorer', task='read').blocked)
                self.assertFalse(call(platform, 'agent', root, type='polish-worker').blocked)
        self.assertFalse(call('cc', 'agent', root, type='generator', isolation='worktree').blocked)
        git(root, 'worktree', 'add', '-q', str(tmp / 'wt-gen'))
        task = f'worktree: {tmp / "wt-gen"}\nimplement AC1'
        for platform in ('cc', 'cx'):
            with self.subTest(platform=platform, declared='worktree'):
                self.assertFalse(call(platform, 'agent', root, type='generator', task=task).blocked)
                bogus = f'worktree: {tmp}/not-a-worktree\nimplement'
                self.assertTrue(call(platform, 'agent', root, type='generator', task=bogus).blocked)

    def test_yellow_zone_needs_isolation_only_with_parallel_writers(self):
        root = project(tmpdir(self), path='Feature', stage='impl', design=GOOD_DESIGN)
        self.assertFalse(call('cc', 'agent', root, type='generator').blocked)
        set_index(root, parallel_writers=2)
        self.assertTrue(call('cc', 'agent', root, type='generator').blocked)

    def test_exemption_with_expiry(self):
        from datetime import date, timedelta
        root = project(tmpdir(self), path='Refactor', stage='impl', design=GOOD_DESIGN)
        soon = (date.today() + timedelta(days=3)).isoformat()
        past = (date.today() - timedelta(days=1)).isoformat()
        far = (date.today() + timedelta(days=40)).isoformat()
        for until, expected in ((soon, False), (past, True), (far, True)):
            set_index(root, exemptions=f'[{{key: h4_worktree, until: "{until}", reason: "target is ~/.claude"}}]')
            with self.subTest(until=until):
                self.assertEqual(call('cc', 'agent', root, type='generator').blocked, expected)
        set_index(root, exemptions=f'[{{key: h4_worktree, until: "{soon}"}}]')
        self.assertTrue(call('cc', 'agent', root, type='generator').blocked, 'an exemption without reason is void')


class FailClosed(unittest.TestCase):
    """Hard-rule exceptions block; advisory exceptions allow with a warning."""

    DRIVER = r"""
const Module = require('module');
const path = require('path');
const [gate, target, cwd, event, tool] = process.argv.slice(1);
const original = Module._load;
Module._load = function (request, parent, isMain) {
  const resolved = Module._resolveFilename(request, parent, isMain);
  if (resolved === path.join(gate, target)) {
    const real = original.apply(this, arguments);
    return new Proxy(real, { get: (o, k) => (typeof o[k] === 'function' ? () => { throw new Error('boom'); } : o[k]) });
  }
  return original.apply(this, arguments);
};
const core = require(path.join(gate, 'core.cjs'));
const ev = { platform: 'cc', event, tool, cwd, paths: [path.join(cwd, 'app.js')], command: 'ls', session_id: 'x' };
process.stdout.write(JSON.stringify(core.handle(ev)));
"""

    def run_with_broken(self, target, cwd, event, tool=''):
        proc = subprocess.run(['node', '-e', self.DRIVER, str(GATE), target, str(cwd), event, tool],
                              text=True, capture_output=True, env=ENV)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_hard_rule_crash_blocks(self):
        root = project(tmpdir(self), path='Feature', stage='impl', design=GOOD_DESIGN)
        for target, tool in (('rules/h1-design.cjs', 'write'), ('rules/h5-shell.cjs', 'bash')):
            with self.subTest(target=target):
                result = self.run_with_broken(target, root, 'pre_tool', tool)
                self.assertEqual(result['decision'], 'block')
                self.assertIn('internal fail-closed', result['reason'])
        set_index(root, stage='ship')
        result = self.run_with_broken('rules/h2-evidence.cjs', root, 'stop')
        self.assertEqual(result['decision'], 'block')

    def test_advisory_crash_allows_with_warning(self):
        root = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN)
        green(root)
        tree = json.loads((root / '.ai_state/.runtime/evidence/2026-09-24-s.jsonl').read_text().splitlines()[-1])['tree_sha']
        (sprint_dir(root) / 'review.json').write_text(json.dumps({'verdict': 'PASS', 'tree_sha': tree}))
        (sprint_dir(root) / 'log.md').write_text('- 残留问题 记 issues\n', encoding='utf-8')  # makes A4 consult issues.md
        result = self.run_with_broken('lib/issues.cjs', root, 'stop')
        self.assertEqual(result['decision'], 'allow')
        self.assertTrue(any('internal error' in w['message'] for w in result['warnings']), result)

    def test_unreadable_payload_blocks_pre_tool_only(self):
        for event, code in (('PreToolUse', 2), ('Stop', 0), ('SessionStart', 0)):
            proc = subprocess.run(['node', str(GATE / 'hook.cjs'), event, '--platform', 'cc'], input='{not json',
                                  text=True, capture_output=True, env=ENV)
            with self.subTest(event=event):
                self.assertEqual(proc.returncode, code, proc.stderr)


if __name__ == '__main__':
    unittest.main()
