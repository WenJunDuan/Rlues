"""2026-09-24 S0 gate hotfix (athena-10-1): push target, git/gh heredoc bodies,
design-change baseline, vm-pending path mentions, stale facts, init-platforms detection.

CC and CX share one fixture; Pi must stay byte-identical to CC where it vendors the guard.
Run: python3 -m unittest discover -s vibeCoding/scripts/tests/athena999 -t vibeCoding/scripts/tests/athena999
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CC = ROOT / 'claude/9.9.9/.claude'
CX = ROOT / 'codex/9.9.9/.codex'
PI = ROOT / 'pi-agent'
ENV = {**os.environ,
       'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
       'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
       'PYTHONDONTWRITEBYTECODE': '1'}
PLATFORMS = ('cc', 'cx')


def git(root, *args):
    subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True, env=ENV)


def project(base, name, stage):
    """A git repo; stage None = no .ai_state at all, '' = idle."""
    root = Path(base) / name
    root.mkdir()
    git(root, 'init', '-q')
    if stage is not None:
        (root / '.ai_state').mkdir()
        (root / '.ai_state/_index.md').write_text(
            f'---\nstage: "{stage}"\ndesign_changed_after_impl: false\n---\n', encoding='utf-8')
    return root


def run_guard(platform, command, cwd):
    payload = json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                          'tool_input': {'command': command}, 'cwd': str(cwd)})
    script = ['node', str(CC / 'hooks/pre-bash-guard.cjs')] if platform == 'cc' \
        else [sys.executable, str(CX / 'hooks/pre-bash-guard.py')]
    return subprocess.run(script, input=payload, text=True, capture_output=True, cwd=str(cwd), env=ENV)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PushTarget(unittest.TestCase):
    """AC1 — the push is judged by the stage of the repository it pushes."""

    def test_push_follows_target_repository_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp).resolve()
            here = project(tmp, 'here', 'impl')
            other = project(tmp, 'other', None)
            idle = project(tmp, 'idle', '')
            (here / 'README.md').write_text('x\n', encoding='utf-8')
            (here / 'sub').mkdir()
            git(here, 'add', 'README.md')
            git(here, 'commit', '-qm', 'base')
            git(here, 'worktree', 'add', '-q', str(tmp / 'wt'))
            subprocess.run(['git', 'init', '-q', '--bare', str(tmp / 'upstream.git')], check=True, env=ENV)
            git(here, 'remote', 'add', 'origin', str(tmp / 'upstream.git'))
            git(here, 'push', '-q', 'origin', 'HEAD:main')
            subprocess.run(['git', 'clone', '-q', str(tmp / 'upstream.git'), str(tmp / 'sibling')], check=True, env=ENV)
            subprocess.run(['git', 'clone', '-q', str(here), str(tmp / 'fromhere')], check=True, env=ENV)
            git(other, 'remote', 'add', 'origin', 'git@github.com:Example/Other.git')
            git(here, 'remote', 'add', 'backup', 'git@github.com:Example/Proj.git')
            (tmp / 'alias').symlink_to(tmp, target_is_directory=True)
            subprocess.run(['git', 'clone', '-q', str(tmp / 'alias/upstream.git'), str(tmp / 'sib_alias')], check=True, env=ENV)
            git(other, 'config', 'url.git@github.com:Example/.insteadOf', 'gh:')
            (tmp / 'xy/sub').mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', '--bare', str(tmp / 'xy/mac.git')], check=True, env=ENV)
            git(here, 'remote', 'add', 'mac', str(tmp / 'xy/mac.git'))
            (tmp / 'alias2').symlink_to(tmp / 'xy/sub', target_is_directory=True)
            cases = (
                ('git push origin main', 2, 'own repo, impl'),
                (f'git -C {here} push origin main', 2, '-C own repo'),
                (f'git -C {other} push origin main', 0, '-C repo without .ai_state'),
                (f'cd {other} && git push origin main', 0, 'cd into other repo'),
                (f'git -C {idle} push', 0, '-C idle repo'),
                ('git -C ../other push', 0, 'relative -C'),
                ('git -C "$HOME/x" push', 2, 'unexpanded variable falls back to cwd'),
                (f'git -C {tmp}/missing push', 2, 'missing dir falls back to cwd'),
                (f'cd {other} && git -C {here} push', 2, '-C back into own repo'),
                (f'cd {other}; cd {here} && git push', 2, 'last cd wins'),
                (f'git -C {tmp}/wt push', 2, 'worktree of own repo is own repo'),
                (f'cd {here}/sub && git push', 2, 'subdirectory of own repo'),
                (f'GIT_DIR={here}/.git git -C {other} push origin main', 2, 'inline GIT_DIR redirect'),
                (f'export GIT_DIR={here}/.git && git -C {other} push origin main', 2, 'exported GIT_DIR redirect'),
                (f'env GIT_WORK_TREE={here} GIT_DIR={here}/.git git -C {other} push', 2, 'env wrapper redirect'),
                (f'cd {other} && GIT_COMMON_DIR={here}/.git git push', 2, 'GIT_COMMON_DIR redirect'),
                (f'git --git-dir={here}/.git -C {other} push', 2, '--git-dir= option'),
                (f'git -C {other} --work-tree {here} push', 2, '--work-tree option'),
                ('env FOO=1 git push origin main', 2, 'env wrapper push (CX parity)'),
                ('sudo git push origin main', 2, 'sudo wrapper push (CX parity)'),
                ('command git push origin main', 2, 'command wrapper push'),
                (f'git -C {tmp}/sibling push origin main', 2, 'sibling clone sharing the project remote'),
                (f'git -C {tmp}/fromhere push origin main', 2, 'clone whose remote is the project itself'),
                (f'git -C {other} push {tmp}/upstream.git main', 2, 'push into a project remote'),
                (f'git -C {other} push "$REMOTE" main', 2, 'unreadable destination'),
                (f'git -C {other} push --repo={tmp}/upstream.git', 2, '--repo= project remote'),
                (f'git -C {other} push git@github.com:example/other.git main', 0, 'unrelated remote, other scheme case'),
                (f'git -C {tmp}/sib_alias push origin main', 2, 'project upstream via symlinked spelling'),
                (f'git -C {other} push {tmp}/alias/upstream.git main', 2, 'destination via symlinked spelling'),
                (f'git -C {other} push file://{tmp}/upstream.git main', 2, 'file:// spelling of project remote'),
                (f'git -C {other} push git@github.com:/example/proj.git main', 2, 'scp spelling with leading slash'),
                (f'git -C {other} push https://github.com/Example/Proj main', 2, 'https spelling of project remote'),
                (f'git -C {other} push gh:Proj.git main', 2, 'insteadOf rewrite to project remote'),
                (f'git -C {other} push {tmp}/alias2/../mac.git main', 2, 'dot-dot after a symlink resolves like the OS'),
            )
            for platform in PLATFORMS:
                for command, expected, label in cases:
                    with self.subTest(platform=platform, case=label):
                        run = run_guard(platform, command, here)
                        self.assertEqual(run.returncode, expected, run.stderr)


class DataConsumers(unittest.TestCase):
    """AC2 — git and gh read a heredoc body as data, not as shell commands."""

    COMMIT = "git commit -F - <<'EOF'\nfix: x\n\ngit push origin main\nEOF"
    GH = "gh pr create --title x --body-file - <<'EOF'\ngit push origin main\nEOF"

    def test_git_and_gh_bodies_are_not_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            here = project(Path(tmp).resolve(), 'here', 'impl')
            for platform in PLATFORMS:
                for command in (self.COMMIT, self.GH):
                    with self.subTest(platform=platform, consumer=command.split()[0]):
                        run = run_guard(platform, command, here)
                        self.assertEqual(run.returncode, 0, run.stderr)

    def test_interpreters_and_trailing_commands_still_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            here = project(Path(tmp).resolve(), 'here', 'impl')
            for platform in PLATFORMS:
                for command in ("bash <<'EOF'\ngit push origin main\nEOF",
                                "git commit -F - <<'EOF'\nx\nEOF\ngit push origin main",
                                "git commit -F - <<'EOF'\nrm -rf /\nEOF\nrm -rf /"):
                    with self.subTest(platform=platform, command=command.splitlines()[-1]):
                        self.assertEqual(run_guard(platform, command, here).returncode, 2)

    def test_cc_and_pi_ship_identical_guard_bytes(self):
        for name in ('_shell-lex.cjs', 'pre-bash-guard.cjs'):
            with self.subTest(name):
                self.assertEqual((CC / 'hooks' / name).read_bytes(),
                                 (PI / 'plugin/extensions/cc-core' / name).read_bytes())


class DesignChangeBaseline(unittest.TestCase):
    """AC3 — only a design that already existed at HEAD can be 'changed after impl'."""

    def run_detector(self, platform, root, design):
        payload = json.dumps({'hook_event_name': 'PostToolUse', 'tool_name': 'Write',
                              'tool_input': {'file_path': str(design)}, 'cwd': str(root)})
        script = ['node', str(CC / 'hooks/design-change-detector.cjs')] if platform == 'cc' \
            else [sys.executable, str(CX / 'hooks/design-change-detector.py')]
        subprocess.run(script, input=payload, text=True, capture_output=True, cwd=str(root), env=ENV)
        text = (root / '.ai_state/_index.md').read_text(encoding='utf-8')
        return re.search(r'^design_changed_after_impl:\s*(\S+)', text, re.M).group(1)

    def test_new_design_is_not_flagged_existing_design_is(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                root = project(Path(tmp).resolve(), 'p', 'impl')
                (root / 'README.md').write_text('x\n', encoding='utf-8')
                git(root, 'add', 'README.md')
                git(root, 'commit', '-qm', 'base')
                design = root / '.ai_state/sprints/s/design.md'
                design.parent.mkdir(parents=True)
                design.write_text('## Done Contract\n- AC1: x\n', encoding='utf-8')
                self.assertEqual(self.run_detector(platform, root, design), 'false', 'new design')
                git(root, 'add', '.ai_state/sprints/s/design.md')
                git(root, 'commit', '-qm', 'design')
                design.write_text('## Done Contract\n- AC1: y\n', encoding='utf-8')
                self.assertEqual(self.run_detector(platform, root, design), 'true', 'baseline design edited')


class VmPendingPromises(unittest.TestCase):
    """AC4 — a path mention of vm-pending.md is not a promise; Quick that writes the ledger is exempt."""

    def check(self, platform, ai, sprint, path_type):
        if platform == 'cc':
            code = ('const m=require(process.argv[1]);'
                    'm.validateVmPendingPromises(process.argv[2],process.argv[3],process.argv[4],process.argv[5]);')
            run = subprocess.run(['node', '-e', code, str(CC / 'hooks/delivery-gate.cjs'),
                                  str(ai), str(sprint), 's', path_type], text=True, capture_output=True, env=ENV)
            return run.returncode == 0
        code = ('import sys; sys.path.insert(0, sys.argv[1]);'
                'import importlib.util as u; s=u.spec_from_file_location("g", sys.argv[2]); g=u.module_from_spec(s);'
                's.loader.exec_module(g); from pathlib import Path;'
                'g.validate_vm_pending_promises(Path(sys.argv[3]), Path(sys.argv[4]), "s", sys.argv[5])')
        run = subprocess.run([sys.executable, '-c', code, str(CX / 'hooks'), str(CX / 'hooks/delivery-gate.py'),
                              str(ai), str(sprint), path_type], text=True, capture_output=True, env=ENV)
        return run.returncode == 0

    def test_path_mentions_and_quick_ledger_writes_pass(self):
        cases = (
            ('允许写集：`src/a.ts`、`.ai_state/vm-pending.md`\n', 'Feature', True, 'path in write set'),
            ('收口 → `vm-pending.md` 追加一行\n', 'Feature', True, 'arrow to file path'),
            ('后续记 vm-pending\n允许写集：`.ai_state/vm-pending.md`\n', 'Quick', True, 'Quick writes ledger'),
            ('后续记 vm-pending\n允许写集：`.ai_state/vm-pending.md`\n', 'Feature', False, 'Feature promise still gated'),
            ('后续记 vm-pending\n', 'Quick', False, 'Quick without ledger in write set'),
        )
        for platform in PLATFORMS:
            for text, path_type, ok, label in cases:
                with self.subTest(platform=platform, case=label), tempfile.TemporaryDirectory() as tmp:
                    ai = Path(tmp) / '.ai_state'
                    sprint = ai / 'sprints/s'
                    sprint.mkdir(parents=True)
                    (sprint / 'design.md').write_text(text, encoding='utf-8')
                    self.assertEqual(self.check(platform, ai, sprint, path_type), ok)


class StaleFacts(unittest.TestCase):
    """AC5 — outdated platform claims and paths are gone."""

    def test_constitution_no_longer_denies_goal(self):
        self.assertNotIn('CC 无原生 `/goal`', (CC / 'CLAUDE.md').read_text(encoding='utf-8'))

    def test_pi_docs_point_at_existing_directory(self):
        for doc in ('README.md', 'config/README.md', 'plugin/README.md'):
            with self.subTest(doc):
                self.assertNotIn('vibeCoding/pi/', (PI / doc).read_text(encoding='utf-8'))

    def test_pi_peer_is_pinned(self):
        peer = json.loads((PI / 'plugin/package.json').read_text(encoding='utf-8'))['peerDependencies']
        self.assertEqual(peer['@earendil-works/pi-coding-agent'], '>=0.87 <0.88')


class InitPlatformDetection(unittest.TestCase):
    """AC6 — the package directory, not any '.claude' path segment, decides the platform."""

    def test_package_platform(self):
        cases = (
            ('/w/.claude/worktrees/x/vibeCoding/codex/9.9.9/.codex/skills/athena-init/scripts/init-platforms.py', 'cx'),
            ('/w/vibeCoding/claude/9.9.9/.claude/skills/athena-init/scripts/init-platforms.py', 'cc'),
            ('/home/u/.claude/skills/athena-init/scripts/init-platforms.py', 'cc'),
            ('/home/u/.agents/skills/athena-init/scripts/init-platforms.py', 'cx'),
        )
        for script in (CC, CX):
            module = load(script / 'skills/athena-init/scripts/init-platforms.py', 'init_platforms_' + script.name[1:])
            for path, expected in cases:
                with self.subTest(copy=script.name, path=path):
                    self.assertEqual(module.package_platform(Path(path)), expected)


if __name__ == '__main__':
    unittest.main()
