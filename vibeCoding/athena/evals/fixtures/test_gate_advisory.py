"""A1–A10 advisories, the Stop circuit breaker, and context injection (athena-10-1 S2 AC3, AC4, AC7)."""
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import unittest

from gate_harness import green, red, ENV, GATE, GOOD_DESIGN, PLATFORMS, athena, call, git, project, set_index, sprint_dir, tmpdir

DRIVER = ("const core=require(process.argv[1]+'/core.cjs');const ctx=require(process.argv[1]+'/lib/context.cjs').load(process.argv[2]);"
          "const adv=require(process.argv[1]+'/rules/advisory.cjs');"
          "process.stdout.write(JSON.stringify(adv.run(ctx,{platform:process.argv[4]||'cc'},process.argv[3].split(','))));")


def advisories(root, names, platform='cc'):
    proc = subprocess.run(['node', '-e', DRIVER, str(GATE), str(root), ','.join(names), platform], text=True, capture_output=True, env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return {w['rule']: w['message'] for w in json.loads(proc.stdout)}


def base_commit(root):
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


class Advisories(unittest.TestCase):
    def test_a1_writer_provenance_is_a_warning(self):
        root = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN)
        self.assertIn('A1', advisories(root, ['A1']))
        call('cc', 'subagent_start', root, type='generator')
        self.assertNotIn('A1', advisories(root, ['A1']))
        quick = project(tmpdir(self), path='Quick', stage='ship', design=GOOD_DESIGN)
        self.assertNotIn('A1', advisories(quick, ['A1']))

    def test_a2_runtime_verify_and_polish(self):
        root = project(tmpdir(self), path='System', stage='ship', design=GOOD_DESIGN)
        self.assertIn('runtime-verify + polish', advisories(root, ['A2'])['A2'])
        (sprint_dir(root) / 'log.md').write_text('- runtime-verify: PASS\n- polish: done\n', encoding='utf-8')
        self.assertNotIn('A2', advisories(root, ['A2']))

    def test_a3_architecture_anchored_on_base_commit(self):
        root = project(tmpdir(self), path='Refactor', stage='ship')
        design = sprint_dir(root) / 'design.md'
        design.write_text(f'---\nbase_commit: "{base_commit(root)}"\n---\n- AC1: x\n', encoding='utf-8')
        for i in range(5):
            (root / f'm{i}.js').write_text('1\n', encoding='utf-8')
        self.assertIn('no architecture/', advisories(root, ['A3'])['A3'])
        (root / 'architecture').mkdir()
        (root / 'architecture/ARCHITECTURE.md').write_text('x\n', encoding='utf-8')
        self.assertNotIn('A3', advisories(root, ['A3']))
        design.write_text('- AC1: x\n', encoding='utf-8')
        self.assertIn('base_commit', advisories(root, ['A3'])['A3'])

    def test_a4_promise_closure_and_quick_exemption(self):
        root = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN + '\n真机部分 记 vm-pending\n')
        self.assertIn('A4', advisories(root, ['A4']))
        (root / '.ai_state/vm-pending.md').write_text(f'- 2026-09-24-s: 真机待验\n', encoding='utf-8')
        self.assertNotIn('A4', advisories(root, ['A4']))
        path_only = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN + '\n见 `vm-pending.md`\n')
        self.assertNotIn('A4', advisories(path_only, ['A4']), 'a bare path is not a promise')

    def test_a5_only_when_baseline_had_the_design(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        design = sprint_dir(root) / 'design.md'
        design.write_text(f'---\nbase_commit: "{base_commit(root)}"\n---\n- AC1: x\n', encoding='utf-8')
        self.assertNotIn('A5', advisories(root, ['A5']), 'new design')
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'design')
        design.write_text(f'---\nbase_commit: "{base_commit(root)}"\n---\n- AC1: x\n', encoding='utf-8')
        git(root, 'add', '-A')
        git(root, 'commit', '-qm', 'rebase design')
        design.write_text(design.read_text() + '- AC2: y\n', encoding='utf-8')
        self.assertIn('A5', advisories(root, ['A5']))

    def test_a6_a7_a8(self):
        root = project(tmpdir(self), path='Feature', stage='impl', design=GOOD_DESIGN,
                       extra_index='pointers: {design: "sprints/2026-09-24-s/design.md", review: "sprints/nope/review.json"}\n')
        self.assertIn('review→sprints/nope/review.json', advisories(root, ['A6'])['A6'])
        for i in range(4):
            (root / f'.ai_state/sprints/2026-09-2{i}-x').mkdir()
        self.assertIn('hot sprints', advisories(root, ['A7'])['A7'])
        soon = (date.today() + timedelta(days=1)).isoformat()
        set_index(root, exemptions=f'[{{key: skip_polish, until: "{soon}", reason: "lib only"}}, {{key: skip_h2, until: "{soon}", reason: "x"}}]')
        message = advisories(root, ['A8'])['A8']
        self.assertIn('skip_polish: expires', message)
        self.assertIn('unknown key skip_h2', message)

    def test_a9_bugfix_repro_test_lock(self):
        root = project(tmpdir(self), path='Bugfix', stage='impl',
                       design='---\nrepro_test: "test_bug.js"\n---\n- AC1: bug fixed\n')
        (root / 'test_bug.js').write_text('process.exit(1)\n', encoding='utf-8')
        self.assertIn('no failing', advisories(root, ['A9'])['A9'])
        athena('run', '--', 'node', '--test', 'test_bug.js', cwd=root)
        self.assertNotIn('A9', advisories(root, ['A9']))
        import os, time
        later = time.time() + 5
        os.utime(root / 'test_bug.js', (later, later))
        self.assertIn('modified after', advisories(root, ['A9'])['A9'])

    def test_a10_same_family(self):
        root = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN)
        (sprint_dir(root) / 'review.json').write_text(json.dumps({'verdict': 'PASS', 'reviewer': {'family': 'anthropic'}}))
        self.assertIn('A10', advisories(root, ['A10'], 'cc'))
        self.assertNotIn('A10', advisories(root, ['A10'], 'cx'))


class Breaker(unittest.TestCase):
    def test_third_identical_block_releases_and_files_an_issue(self):
        root = project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN)
        for platform in PLATFORMS:
            session = f'breaker-{platform}'
            verdicts = [call(platform, 'stop', root, session=session).blocked for _ in range(4)]
            with self.subTest(platform=platform):
                self.assertEqual(verdicts, [True, True, False, True], 'block, block, release, new chain')
        issues = (root / '.ai_state/issues.md').read_text(encoding='utf-8')
        rows = [line for line in issues.splitlines() if line.startswith('| G-')]
        self.assertEqual(len(rows), 3)
        self.assertIn('| gate |', rows[0])
        self.assertIn('triage', rows[0])
        self.assertIn('G-003', rows[-1])

    def test_pass_resets_the_chain_and_pre_tool_never_releases(self):
        root = project(tmpdir(self), path='Quick', stage='ship', design=GOOD_DESIGN)
        self.assertTrue(call('cc', 'stop', root, session='r').blocked)
        self.assertTrue(call('cc', 'stop', root, session='r').blocked)
        green(root)
        self.assertFalse(call('cc', 'stop', root, session='r').blocked)
        (root / 'app.js').write_text('changed\n', encoding='utf-8')
        self.assertEqual([call('cc', 'stop', root, session='r').blocked for _ in range(3)], [True, True, False])
        design_first = project(tmpdir(self), path='Feature', stage='impl')
        self.assertTrue(all(call('cc', 'write', design_first, file=design_first / 'app.js').blocked for _ in range(5)))


class Injection(unittest.TestCase):
    def test_session_start_and_prompt(self):
        soon = (date.today() + timedelta(days=5)).isoformat()
        root = project(tmpdir(self), path='Refactor', stage='impl', design=GOOD_DESIGN,
                       extra_index=f'next_action: "finish AC1"\nexemptions:\n  - key: h4_worktree\n    until: "{soon}"\n    reason: "harness outside repo"\n')
        (root / '.ai_state/issues.md').write_text('| id | 类型 | 级别 | 一句话 | 发现于 | 去向 | 状态 |\n|---|---|---|---|---|---|---|\n'
                                                  '| Q-001 | question | — | 选哪个方案 | x | 用户 | open |\n', encoding='utf-8')
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                context = call(platform, 'session', root).context
                self.assertIn('stage=impl', context)
                self.assertIn('finish AC1', context)
                self.assertIn('exemption h4_worktree', context)
                self.assertIn('Q-001', context)
        self.assertEqual(call('cc', 'prompt', root).context, '', 'nothing queued → no per-turn noise')
        call('cc', 'agent', root, type='polish-worker')
        self.assertIn('polish-worker', call('cc', 'prompt', root).context)
        self.assertEqual(call('cc', 'prompt', root).context, '', 'queued advisories are delivered once')


if __name__ == '__main__':
    unittest.main()
