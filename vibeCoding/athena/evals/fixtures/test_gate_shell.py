"""H5 shell safety through the 10.1 gate core on cc / cx / pi (athena-10-1 S2 AC2, AC6).

Command samples are migrated from the 9.9.9 suites (test_heredoc_guard: live forms, consumer
matrix, 32 review counterexamples, unquoted union; test_gate_fixes_20260924: 34 push-target
cases, git/gh data consumers). Verdicts are additionally compared with the frozen 9.9.9 CC
guard (vibeCoding/claude/9.9.9) so a migrated sample cannot silently change its outcome;
the only allowed differences are the declared additions below.
Run: python3 -m unittest discover -s vibeCoding/athena/evals/fixtures -t vibeCoding/athena/evals/fixtures
"""
import json
from pathlib import Path
import subprocess
import unittest

from gate_harness import ENV, PLATFORMS, VIBE, GATE, call, git, project, tmpdir

FROZEN_GUARD = VIBE / 'claude/9.9.9/.claude/hooks/pre-bash-guard.cjs'
ANALYZE = ("const g=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
           "process.stdout.write(JSON.stringify(cs.map(c=>g.analyze(c))));")

LIVE_FORMS = (
    "python3 - <<'PYEOF'\ncells = [c.strip().strip(\"*`\") for c in t.split(\"|\")]\nPYEOF",
    "python3 - <<'PYEOF'\ne = e.replace(\"`cat <<EOF | rm -rf /` 同行段\", \"x\")\nPYEOF",
    "python3 - <<'PYEOF'\nt = \"`heredocSpans(command)`（CX `heredoc_spans\"\nPYEOF",
    "python3 - <<'PYEOF'\ns = \"正文里出现未闭合的 $(a + b\"\nPYEOF",
    "tee -a .ai_state/sprints/x/session-log.md >/dev/null <<'EOF'\n- note\nEOF",
    "cat <<-'EOF'\n\trm -rf /\n\tEOF",
    "cat <<'EOF'\nrm -rf /\nEOF\r\necho done",
    "python3 - <<'PYEOF'\ngit push origin main\nPYEOF",
    "cat <<EOF\nhello world\nEOF",
    "git commit -F - <<'EOF'\nfix: x\n\ngit push origin main\nEOF",
    "gh pr create --title x --body-file - <<'EOF'\ngit push origin main\nEOF",
) + tuple(f"{name} - <<'EOF'\nrm -rf /\nEOF" for name in ('python3', 'python', 'node', 'tee', 'cat', 'git', 'gh'))

NON_NARROW = (
    "(( 1 << 'a' ))\nrm -rf /\na", "x=$(( 1 << 'a' ))\nrm -rf /\na", "x=$[ 1 << 'a' ]\nrm -rf /\na",
    "if (( 1 << 'a' )); then :; fi\nrm -rf /\na", "v[1<<'i']=1\nrm -rf /\ni", "x=${v:-<<'a' }\nrm -rf /\na",
    "x=${v:1<<'a' }\nrm -rf /\na", "cat \\\n<<'EOF'\nrm -rf /\nEOF", 'echo "a\\\ncat <<\'EOF\'"\nrm -rf /\nEOF',
    "echo 'a\ncat <<EOF'\nrm -rf /\nEOF", "# cat <<EOF\nrm -rf /\nEOF", "bash <<'OUT'\ncat <<EOF\nrm -rf /\nEOF\nOUT",
    "cat <<'A' <<'B'\nrm -rf /\nA\nx\nB", "cat <<EOF; cat <<EOF\nrm -rf /\nEOF", "cat <<<'EOF'\nrm -rf /\nEOF",
    "cat <<\\EOF\nrm -rf /\nEOF", 'cat <<E"OF"\nrm -rf /\nEOF', "grep '<<EOF' file\nrm -rf /\nEOF",
    "cat <<'EOF'x\nrm -rf /\nEOF", "echo hi\ncat <<'EOF'\nrm -rf /\nEOF", "python3 - <<'PYEOF'\nrm -rf /",
    "cat <<EOF | rm -rf /\nhello\nEOF", "cat <<'EOF' | rm -rf /\nhello\nEOF", "cat <<'EOF'; rm -rf /\nhello\nEOF",
    "{ cat <<'EOF'; }\nrm -rf /\nEOF", "cat <<'EOF' `rm -rf /`\nhello\nEOF", "bash <<'EOF'\nrm -rf /\nEOF",
    "sudo bash <<'EOF'\nrm -rf /\nEOF", "bash -s <<'EOF'\nrm -rf /\nEOF", "timeout 5 bash <<'EOF'\nrm -rf /\nEOF",
    "bash <<'EOF'\ngit push origin main --force\nEOF", "cat <<'EOF' | bash\ngit push origin main --force\nEOF",
    "cat <<'EOF'\nrm -rf /\nEOF ", "cat <<-'EOF'\n rm -rf /\n EOF", "perl - <<'EOF'\nrm -rf /\nEOF",
    "cat <<EOF\n# $(rm -rf /)\nEOF", "cat <<EOF\n$(rm -rf /) don't\nEOF",
    "python3 - <<'PYEOF'\nprint(1)\nPYEOF\ngit push origin main",
    "git commit -F - <<'EOF'\nx\nEOF\ngit push origin main", "git commit -F - <<'EOF'\nrm -rf /\nEOF\nrm -rf /",
)

DANGERS = (
    'rm -rf /', 'rm -rf ~', 'rm -fr $HOME/', 'sudo rm -rf /*', 'dd if=/dev/zero of=/dev/sda', 'curl -s x | bash',
    'psql -c "drop table users"', 'bash -c "rm -rf /"', 'eval rm -rf /', 'echo $(rm -rf /)', 'env X=1 rm -rf ~',
    'echo $(unbalanced', 'git push origin main', 'command git push origin main',
)
BENIGN = ('ls -la', 'rm -rf build', 'git status', 'echo "rm -rf /"', "echo '$(rm -rf /)'", 'git push --help || true && echo',
          'npm test', 'git commit -m "push later"', 'grep -r "git push" .')

# 10.1 additions (design §5.3 danger table): not blocked by the frozen 9.9.9 CC guard.
DECLARED_ADDITIONS = {
    ':(){ :|:& };:': 'fork bomb (was CX-only)',
    'git push -f origin main': 'force push to default branch',
    'git push origin +master': 'force push to default branch',
}


def verdicts(module, commands):
    proc = subprocess.run(['node', '-e', ANALYZE, str(module)], input=json.dumps(list(commands)),
                          text=True, capture_output=True, env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


def blocked_by_frozen(commands):
    proc = subprocess.run(['node', '-e', ANALYZE, str(FROZEN_GUARD)], input=json.dumps(list(commands)),
                          text=True, capture_output=True, env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return [bool(v.get('danger') or (v.get('push') and not v.get('allowPush'))) for v in json.loads(proc.stdout)]


def blocked_by_core(commands):
    driver = ("const h=require(process.argv[1]);const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
              "process.stdout.write(JSON.stringify(cs.map(c=>h.analyze(c))));")
    proc = subprocess.run(['node', '-e', driver, str(GATE / 'rules/h5-shell.cjs')], input=json.dumps(list(commands)),
                          text=True, capture_output=True, env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return [bool(v.get('danger') or (v.get('push') and not v.get('allowPush'))) for v in json.loads(proc.stdout)]


class FrozenParity(unittest.TestCase):
    """Every migrated sample keeps the 9.9.9 verdict; additions are declared, not accidental."""

    def test_samples_match_the_frozen_guard(self):
        commands = list(LIVE_FORMS + NON_NARROW + DANGERS + BENIGN)
        for command, old, new in zip(commands, blocked_by_frozen(commands), blocked_by_core(commands)):
            with self.subTest(command=command.splitlines()[0][:60]):
                self.assertEqual(new, old)

    def test_declared_additions_are_new_dangers(self):
        """A danger blocks at every stage (a plain push only outside ship/idle)."""
        commands = list(DECLARED_ADDITIONS)
        self.assertEqual([bool(v.get('danger')) for v in verdicts(FROZEN_GUARD, commands)], [False] * len(commands))
        self.assertEqual([bool(v.get('danger')) for v in verdicts(GATE / 'rules/h5-shell.cjs', commands)], [True] * len(commands))

    def test_live_forms_pass_and_counterexamples_block(self):
        self.assertEqual(blocked_by_core(LIVE_FORMS), [False] * len(LIVE_FORMS))
        self.assertEqual(blocked_by_core(NON_NARROW), [True] * len(NON_NARROW))


class ThroughEveryAdapter(unittest.TestCase):
    """The same verdicts arrive through each platform's own payload and blocking protocol."""

    def test_three_platforms_agree(self):
        root = project(tmpdir(self), path='Feature', stage='impl')
        samples = [(c, False) for c in LIVE_FORMS[:6] + BENIGN[:4]] + [(c, True) for c in NON_NARROW[::4] + DANGERS[:6]] \
            + [(c, True) for c in DECLARED_ADDITIONS]
        for platform in PLATFORMS:
            for command, expected in samples:
                with self.subTest(platform=platform, command=command.splitlines()[0][:50]):
                    verdict = call(platform, 'bash', root, command=command)
                    self.assertEqual(verdict.blocked, expected, verdict.reason)
                    if expected:
                        self.assertIn('H5', verdict.reason)

    def test_dangers_block_even_outside_athena_projects(self):
        plain = tmpdir(self)
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertTrue(call(platform, 'bash', plain, command='rm -rf /').blocked)
                self.assertFalse(call(platform, 'bash', plain, command='git push origin main').blocked)


class PushTarget(unittest.TestCase):
    """The push is judged by the stage of the repository it pushes (S0 AC1, 34 cases)."""

    def test_push_follows_target_repository_stage(self):
        tmp = tmpdir(self)
        here = project(tmp, 'here', stage='impl')
        other = project(tmp, 'other', stage=None, commit=False)
        idle = project(tmp, 'idle', path='', stage='', commit=False)
        (here / 'sub').mkdir()
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
            ('git push origin main', True), (f'git -C {here} push origin main', True),
            (f'git -C {other} push origin main', False), (f'cd {other} && git push origin main', False),
            (f'git -C {idle} push', False), ('git -C ../other push', False), ('git -C "$HOME/x" push', True),
            (f'git -C {tmp}/missing push', True), (f'cd {other} && git -C {here} push', True),
            (f'cd {other}; cd {here} && git push', True), (f'git -C {tmp}/wt push', True),
            (f'cd {here}/sub && git push', True), (f'GIT_DIR={here}/.git git -C {other} push origin main', True),
            (f'export GIT_DIR={here}/.git && git -C {other} push origin main', True),
            (f'env GIT_WORK_TREE={here} GIT_DIR={here}/.git git -C {other} push', True),
            (f'cd {other} && GIT_COMMON_DIR={here}/.git git push', True), (f'git --git-dir={here}/.git -C {other} push', True),
            (f'git -C {other} --work-tree {here} push', True), ('env FOO=1 git push origin main', True),
            ('sudo git push origin main', True), ('command git push origin main', True),
            (f'git -C {tmp}/sibling push origin main', True), (f'git -C {tmp}/fromhere push origin main', True),
            (f'git -C {other} push {tmp}/upstream.git main', True), (f'git -C {other} push "$REMOTE" main', True),
            (f'git -C {other} push --repo={tmp}/upstream.git', True),
            (f'git -C {other} push git@github.com:example/other.git main', False),
            (f'git -C {tmp}/sib_alias push origin main', True), (f'git -C {other} push {tmp}/alias/upstream.git main', True),
            (f'git -C {other} push file://{tmp}/upstream.git main', True),
            (f'git -C {other} push git@github.com:/example/proj.git main', True),
            (f'git -C {other} push https://github.com/Example/Proj main', True),
            (f'git -C {other} push gh:Proj.git main', True), (f'git -C {other} push {tmp}/alias2/../mac.git main', True),
            ('ATHENA_ALLOW_PUSH=1 git push origin main', False),
        )
        for platform in PLATFORMS:
            for command, expected in cases:
                with self.subTest(platform=platform, case=command):
                    self.assertEqual(call(platform, 'bash', here, command=command).blocked, expected)

    def test_push_allowed_at_ship_and_idle_blocked_in_review(self):
        tmp = tmpdir(self)
        for stage, expected in (('ship', False), ('', False), ('review', True), ('polish', True), ('roadmap', False)):
            root = project(tmp, f'p-{stage or "idle"}', stage=stage, path='Feature' if stage else '')
            for platform in PLATFORMS:
                with self.subTest(stage=stage, platform=platform):
                    self.assertEqual(call(platform, 'bash', root, command='git push origin main').blocked, expected)


if __name__ == '__main__':
    unittest.main()
