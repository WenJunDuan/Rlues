"""Regressions for the S2 independent review (round 1): fail-open paths that must stay closed."""
import json
import os
from pathlib import Path
import subprocess
import unittest

from gate_harness import (ENV, GATE, GOOD_DESIGN, HOOK, PLATFORMS, athena, call, git, green, project, set_index,
                          sprint_dir, tmpdir)
from test_gate_shell import blocked_by_core, verdicts, FROZEN_GUARD

SPRINT = '2026-09-24-s'


def rows(root):
    path = Path(root) / '.ai_state/.runtime/evidence' / f'{SPRINT}.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def raw_hook(platform, event, body, env=None):
    return subprocess.run(['node', str(HOOK), event, '--platform', platform], input=json.dumps(body), text=True,
                          capture_output=True, env={**ENV, **(env or {})})


class EvidenceByFiat(unittest.TestCase):
    """P1: H2 must not be satisfiable without running a real check."""

    def test_no_kind_override_and_argv_quoting(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        self.assertEqual(athena('run', '--kind', 'test', '--', 'true', cwd=root).returncode, 2)
        athena('run', '--', 'echo', '; pytest', cwd=root)
        athena('run', '--', 'bash', '-c', 'npm test --version || true', cwd=root)
        athena('run', '--', 'true || python3 -m pytest', cwd=root)
        athena('run', '--', 'exit 0; npm test', cwd=root)
        got = [(r['kind'], r['provable'], r['reason']) for r in rows(root)]
        self.assertEqual(got, [('other', False, None), ('other', False, 'wrapped_command'),
                               ('test', False, 'validation_may_not_run'), ('test', False, 'validation_may_not_run')])

    def test_venv_and_runner_forms_are_provable(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        driver = ("const e=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                  "process.stdout.write(JSON.stringify(cs.map(c=>[e.classify(c),e.policy(c).provable])));")
        lines = ['source venv/bin/activate && pytest', '. .venv/bin/activate && python3 -m pytest', '.venv/bin/pytest -q',
                 '.venv/bin/python -m pytest', 'uv run pytest', 'poetry run pytest', 'node_modules/.bin/jest']
        out = subprocess.run(['node', '-e', driver, str(GATE / 'lib/evidence.cjs')], input=json.dumps(lines), text=True,
                             capture_output=True, env=ENV)
        self.assertEqual(json.loads(out.stdout), [['test', True]] * len(lines))
        outside = ['/tmp/fakebin/pytest', '~/../../tmp/fakebin/pytest', '../x/bin/pytest']
        out = subprocess.run(['node', '-e', driver, str(GATE / 'lib/evidence.cjs')], input=json.dumps(outside), text=True,
                             capture_output=True, env=ENV)
        self.assertEqual([k for k, _ in json.loads(out.stdout)], [None] * len(outside), 'a tool outside the tree is not evidence')
        shadow = ['source /tmp/ev/bin/activate && pytest', 'source ../v/bin/activate && pytest']
        out = subprocess.run(['node', '-e', driver, str(GATE / 'lib/evidence.cjs')], input=json.dumps(shadow), text=True,
                             capture_output=True, env=ENV)
        self.assertEqual([p for _, p in json.loads(out.stdout)], [False, False])

    def test_tree_change_during_run_and_signal_exit(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        (root.parent / 'athena-x.test.cjs').write_text("require('node:test')('ok',()=>{});\n")
        athena('run', '--', 'node --test ../athena-x.test.cjs && echo change >> app.js', cwd=root)
        self.assertEqual((rows(root)[-1]['provable'], rows(root)[-1]['reason']), (False, 'tree_changed_during_run'))
        run = athena('run', '--', 'node', '-e', "process.kill(process.pid, 'SIGKILL')", cwd=root)
        self.assertEqual(run.returncode, 137)
        self.assertEqual(rows(root)[-1]['exit'], 137)

    def test_shadowed_validations_are_unprovable(self):
        root = project(tmpdir(self), design=GOOD_DESIGN)
        for line in ('trap "exit 0" EXIT; npm test --bad', 'npm() ( true ) && npm test', 'PATH=/tmp/fakebin:$PATH npm test',
                     'shopt -s expand_aliases; alias npm=true\nnpm test', 'function npm { true; } && npm test',
                     '. ./shim.sh && npm test', 'source ./shim.sh && npm test'):
            athena('run', '--', line, cwd=root)
            with self.subTest(line=line):
                self.assertEqual((rows(root)[-1]['provable'], rows(root)[-1]['reason']), (False, 'validation_shadowable'))

    def test_ledger_and_review_json_cannot_be_written_by_tools(self):
        root = project(tmpdir(self), stage='ship', design=GOOD_DESIGN)
        for platform in PLATFORMS:
            for target in (root / f'.ai_state/.runtime/evidence/{SPRINT}.jsonl', sprint_dir(root) / 'review.json'):
                with self.subTest(platform=platform, target=target.name):
                    verdict = call(platform, 'write', root, file=target)
                    self.assertTrue(verdict.blocked)
                    self.assertIn('H2 ledger', verdict.reason)
            self.assertFalse(call(platform, 'write', root, file=sprint_dir(root) / 'log.md').blocked)

    def test_ledger_guard_resolves_symlinks_and_case(self):
        tmp = tmpdir(self)
        root = project(tmp, stage='ship', design=GOOD_DESIGN)
        (tmp / 'link').symlink_to(root, target_is_directory=True)
        (root / 'alias').symlink_to(sprint_dir(root), target_is_directory=True)
        for cwd, target in ((tmp / 'link', tmp / f'link/.ai_state/sprints/{SPRINT}/review.json'),
                            (root, root / 'alias/review.json'), (root, sprint_dir(root) / 'Review.json')):
            with self.subTest(target=str(target)):
                self.assertTrue(call('cc', 'write', cwd, file=target).blocked)

    def test_ledger_and_review_json_cannot_be_written_by_shell(self):
        root = project(tmpdir(self), stage='ship', design=GOOD_DESIGN)
        for platform in PLATFORMS:
            for command in (f'echo x >> .ai_state/.runtime/evidence/{SPRINT}.jsonl',
                            f'cp /tmp/r .ai_state/sprints/{SPRINT}/review.json',
                            f"tee .ai_state/sprints/{SPRINT}/review.json <<'EOF'\n{{}}\nEOF",
                            f'mv /tmp/review.json .ai_state/sprints/{SPRINT}', f'git checkout other -- .ai_state/sprints/{SPRINT}/review.json',
                            f'curl -so .ai_state/sprints/{SPRINT}/review.json https://x', f'cp /tmp/e.jsonl .ai_state/.runtime/evidence/'):
                with self.subTest(platform=platform, command=command[:40]):
                    self.assertTrue(call(platform, 'bash', root, command=command).blocked)
            for command in (f'cat .ai_state/sprints/{SPRINT}/review.json', f'cp .ai_state/sprints/{SPRINT}/review.json /tmp/bak.json'):
                self.assertFalse(call(platform, 'bash', root, command=command).blocked, command)


class CodexWorkdir(unittest.TestCase):
    """P1: a model-chosen workdir must not move the project that governs the event."""

    def test_workdir_is_a_leading_cd_not_the_project(self):
        tmp = tmpdir(self)
        proj = project(tmp, 'proj', stage='impl')
        other = project(tmp, 'other', stage=None)
        base = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'cwd': str(proj)}
        for command, workdir, expected in (
                (['bash', '-lc', f'GIT_DIR={proj}/.git git push origin HEAD'], '/tmp', 2),
                (['bash', '-lc', f'git --git-dir={proj}/.git push'], '/tmp', 2),
                (['bash', '-lc', 'git push origin HEAD'], str(proj / 'sub'), 2),
                (['bash', '-lc', 'git push origin HEAD'], str(other), 0),
                (['/bin/sh', '-euc', 'rm -rf /'], str(other), 2)):
            body = {**base, 'tool_input': {'command': command, 'workdir': workdir}}
            with self.subTest(command=command[-1], workdir=workdir):
                self.assertEqual(raw_hook('cx', 'PreToolUse', body).returncode, expected)

    def test_relative_write_resolves_against_workdir_but_state_against_session(self):
        tmp = tmpdir(self)
        proj = project(tmp, 'proj', stage='impl')
        body = {'hook_event_name': 'PreToolUse', 'tool_name': 'apply_patch', 'cwd': str(proj),
                'tool_input': {'workdir': str(tmp), 'command': '*** Begin Patch\n*** Add File: scratch.txt\n*** End Patch\n'}}
        self.assertEqual(raw_hook('cx', 'PreToolUse', body).returncode, 0, 'tmp/scratch.txt is outside the repo')
        body['tool_input']['workdir'] = str(proj)
        self.assertEqual(raw_hook('cx', 'PreToolUse', body).returncode, 2)


class UnknownState(unittest.TestCase):
    """P1/P2: an unparseable or unknown _index is never idle."""

    def index(self, root, text):
        (root / '.ai_state/_index.md').write_text(text, encoding='utf-8')

    def test_malformed_and_unknown_values_are_strict(self):
        root = project(tmpdir(self), stage='impl', design=GOOD_DESIGN)
        for label, text in (('no frontmatter', 'stage: impl\n'), ('no keys', '---\nversion: 1\n---\n'),
                            ('unknown stage', '---\npath: "Feature"\nstage: "Impl"\n---\n'),
                            ('unknown stage 2', '---\npath: "Feature"\nstage: "done"\ncurrent_sprint_slug: "x"\n---\n'),
                            ('unknown path', f'---\npath: "feature"\nstage: "ship"\ncurrent_sprint_slug: "{SPRINT}"\n---\n')):
            self.index(root, text)
            for platform in PLATFORMS:
                with self.subTest(label=label, platform=platform):
                    self.assertTrue(call(platform, 'bash', root, command='git push origin main').blocked)
                    self.assertTrue(call(platform, 'write', root, file=root / 'app.js').blocked)
                    self.assertFalse(call(platform, 'stop', root, session=f'{label}-{platform}').blocked, 'read-only Stop only warns (AC7)')
                    self.assertFalse(call(platform, 'write', root, file=root / '.ai_state/_index.md').blocked, 'the fix stays possible')

    def test_bom_and_trailing_space_still_parse(self):
        root = project(tmpdir(self), stage='impl', design=GOOD_DESIGN)
        for text in ('﻿---\npath: "Feature"\nstage: "impl"\n---\n', '--- \npath: "Feature"\nstage: "impl"\n---  \n'):
            self.index(root, text)
            with self.subTest(text=repr(text[:5])):
                verdict = call('cc', 'bash', root, command='git push origin main')
                self.assertTrue(verdict.blocked)
                self.assertIn('stage=impl', verdict.reason)


class TreeBinding(unittest.TestCase):
    def test_hidden_index_bits_do_not_hide_edits(self):
        for flag in ('--assume-unchanged', '--skip-worktree'):
            root = project(tmpdir(self), stage='ship', path='Quick', design=GOOD_DESIGN)
            (root / 'other.js').write_text('1\n', encoding='utf-8')
            git(root, 'add', 'other.js')
            git(root, 'commit', '-qm', 'two files')
            green(root)
            with self.subTest(flag=flag):
                self.assertFalse(call('cc', 'stop', root).blocked)
                git(root, 'update-index', flag, 'app.js')
                (root / 'app.js').write_text('module.exports = 99;\n', encoding='utf-8')
                self.assertTrue(call('cc', 'stop', root, session='x2').blocked)
                self.assertEqual(git(root, 'ls-files', '-v', 'app.js').stdout[0], 'h' if flag == '--assume-unchanged' else 'S',
                                 "the user's index keeps its bits")

    def test_match_all_review_ignore_is_dropped_and_ignore_changes_invalidate(self):
        root = project(tmpdir(self), stage='ship', path='Quick', design='---\nreview_ignore: ["**"]\n---\n- AC1: x works\n')
        green(root)
        tree = rows(root)[-1]['tree_sha']
        self.assertNotEqual(tree, '4b825dc642cb6eb9a060e54bf8d69288fbee4904', 'empty tree')
        self.assertEqual(rows(root)[-1]['ignore'], [])
        (root / 'docs').mkdir()
        (root / 'docs/a.md').write_text('x\n')
        (sprint_dir(root) / 'design.md').write_text('---\nreview_ignore: ["docs/**"]\n---\n- AC1: x works\n')
        verdict = call('cc', 'stop', root, session='ig')
        self.assertTrue(verdict.blocked)
        self.assertIn('review_ignore', verdict.reason)
        green(root)
        self.assertFalse(call('cc', 'stop', root, session='ig2').blocked)


class CodexPatchShapes(unittest.TestCase):
    def test_union_of_path_and_patch_and_shell_apply_patch(self):
        root = project(tmpdir(self), stage='impl')
        patch = '*** Begin Patch\n*** Add File: src/x.js\n+x\n*** End Patch\n'
        for tool_name, tool_input in (
                ('apply_patch', {'path': '.ai_state/n.md', 'command': patch}),
                ('Bash', {'command': ['apply_patch', patch]}),
                ('Bash', {'command': f"apply_patch <<'EOF'\n{patch}EOF"}),
                ('Bash', {'command': ['bash', '-lc', f"apply_patch <<'EOF'\n{patch}EOF"]}),
                ('Bash', {'command': ['bash', '-lc', f"cd . && apply_patch <<'EOF'\n{patch}EOF"]})):
            body = {'hook_event_name': 'PreToolUse', 'tool_name': tool_name, 'cwd': str(root), 'tool_input': tool_input}
            with self.subTest(tool=tool_name, shape=str(tool_input)[:40]):
                run = raw_hook('cx', 'PreToolUse', body)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn('H1', run.stderr)


class CodexAgents(unittest.TestCase):
    def test_isolation_field_ignored_and_definition_beats_name(self):
        tmp = tmpdir(self)
        root = project(tmp, stage='impl', path='System', design=GOOD_DESIGN)
        home = tmp / 'home'
        (home / '.codex/agents').mkdir(parents=True)
        (home / '.codex/agents/explorer.toml').write_text('sandbox_mode = "workspace-write"\n')
        (home / '.codex/agents/scout.toml').write_text('sandbox_mode = "read-only"\n')
        base = {'hook_event_name': 'PreToolUse', 'tool_name': 'spawn_agent', 'cwd': str(root)}
        for tool_input, expected in (({'agent_type': 'generator', 'isolation': 'worktree', 'message': 'x'}, 2),
                                     ({'agent_type': 'explorer', 'message': 'x'}, 2),
                                     ({'agent_type': 'scout', 'message': 'x'}, 0)):
            with self.subTest(agent=tool_input['agent_type']):
                self.assertEqual(raw_hook('cx', 'PreToolUse', {**base, 'tool_input': tool_input}, {'HOME': str(home)}).returncode, expected)


class ShellAdditions(unittest.TestCase):
    ADDED = ('bash -ec "rm -rf /"', 'sh -xc "rm -rf ~"', 'rm -Rf /', 'timeout 5 rm -rf /', 'nice -n 2 rm -rf ~',
             'nohup rm -rf / &', '(rm -rf /)', 'exec rm -rf ~', 'git push origin :main', 'git push --delete origin master',
             'git push --force-with-lease origin main', '{ rm -rf /; }', 'if true; then rm -rf /; fi',
             'while x; do rm -rf ~; done', 'bash -c -e "rm -rf /"', 'coproc rm -rf /')

    def test_new_dangers(self):
        self.assertEqual([bool(v.get('danger')) for v in verdicts(GATE / 'rules/h5-shell.cjs', self.ADDED)], [True] * len(self.ADDED))
        frozen = [bool(v.get('danger')) for v in verdicts(FROZEN_GUARD, self.ADDED)]
        self.assertIn(False, frozen, 'these are 10.1 additions over 9.9.9')

    def test_force_push_on_checked_out_main(self):
        root = project(tmpdir(self), stage='ship', design=GOOD_DESIGN)
        git(root, 'branch', '-M', 'main')
        for command in ('git push -f', 'git push --force origin HEAD', 'git push -f origin +HEAD'):
            with self.subTest(command=command):
                self.assertTrue(call('cc', 'bash', root, command=command).blocked)
        git(root, 'checkout', '-qb', 'feature')
        self.assertFalse(call('cc', 'bash', root, command='git push -f origin HEAD').blocked)


class SubshellCd(unittest.TestCase):
    def test_conditional_or_scoped_cd_does_not_move_the_push(self):
        tmp = tmpdir(self)
        root = project(tmp, stage='impl')
        other = project(tmp, 'other', stage=None)
        self.assertFalse(call('cc', 'bash', root, command=f'cd {other} && git push origin $(git rev-parse --abbrev-ref HEAD)').blocked,
                         'a $( … ) substitution is not a subshell scope')
        for command in ('(cd /tmp) && git push origin HEAD', '(cd /tmp); git push origin HEAD', '( cd /tmp ) && git push',
                        'true && (cd /tmp) && git push', '(cd /tmp && git push)', 'if false; then cd /tmp; fi; git push',
                        'while false; do cd /tmp; done; git push', '! cd /tmp; git push', 'true || cd /tmp; git push',
                        'false && cd /tmp; git push', 'echo x; cd /tmp && git push', '{ cd /tmp; }; git push',
                        'nohup cd /tmp; git push', 'timeout 5 cd /tmp; git push', 'nice cd /tmp; git push',
                        'env cd /tmp; git push', 'sudo cd /tmp; git push', 'xargs cd /tmp; git push'):
            for platform in PLATFORMS:
                with self.subTest(command=command, platform=platform):
                    self.assertTrue(call(platform, 'bash', root, command=command).blocked)


class Misc(unittest.TestCase):
    def test_null_payload_blocks_pre_tool(self):
        for payload in ('null', '[]', '"x"'):
            run = subprocess.run(['node', str(HOOK), 'PreToolUse', '--platform', 'cc'], input=payload, text=True, capture_output=True, env=ENV)
            with self.subTest(payload=payload):
                self.assertEqual(run.returncode, 2)

    def test_breaker_sessions_do_not_mix(self):
        root = project(tmpdir(self), stage='ship', design=GOOD_DESIGN)
        for i in range(4):
            call('cc', 'stop', root, session=f'other-{i % 2}')
        self.assertTrue(call('pi', 'stop', root).blocked, 'first Pi stop is a first block, not a release')


if __name__ == '__main__':
    unittest.main()
