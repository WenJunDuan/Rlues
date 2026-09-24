"""Heredoc-aware shell guard (slice 8, design rev 8) — AC1..AC7 regressions.

The guard masks a heredoc body only for the *narrow whitelist form*: a first line
that fully matches the closed grammar in ``_shell-lex`` and whose first token
basename is a known non-shell consumer (python3/python/node/tee/cat).  Everything
else — every counterexample from the seven design-review rounds, and every shell
interpreter or unknown wrapper — stays byte-identical to the pre-change guard.

AC1 fixtures are the four live mis-block forms plus the two positive samples
recorded in the sprint's ``evidence/live-samples.md`` (each one verified to BLOCK
on the pre-change guard before this file was written).
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
REPO = Path(__file__).resolve().parents[6]
CC = ROOT / 'claude/9.9.9/.claude/hooks'
CX = ROOT / 'codex/9.9.9/.codex/hooks'
PI = ROOT / 'pi-agent/plugin/extensions/cc-core'
# Slice 8 baseline: AC3 replays every non-narrow fixture against the guard as it
# stood here and asserts the verdict is unchanged, so the pin must be a commit,
# not a snapshot of the working tree.
BASELINE = '512bb7cbb89231e242df6ef34556c29bf693b8c8'

CONSUMERS = ('python3', 'python', 'node', 'tee', 'cat', 'git', 'gh')

# --- AC1: the four live mis-block forms (evidence/live-samples.md) ------------
FORM_1 = ("python3 - <<'PYEOF'\n"
          'cells = [c.strip().strip("*`") for c in t.split("|")]\n'
          'PYEOF')
FORM_2 = ("python3 - <<'PYEOF'\n"
          'e = e.replace("`cat <<EOF | rm -rf /` 同行段", "x")\n'
          'PYEOF')
FORM_3 = ("python3 - <<'PYEOF'\n"
          't = "`heredocSpans(command)`（CX `heredoc_spans"\n'
          'PYEOF')
FORM_4 = ("python3 - <<'PYEOF'\n"
          's = "正文里出现未闭合的 $(a + b"\n'
          'PYEOF')
LIVE_FORMS = (('form1_odd_backtick', FORM_1),
              ('form2_backticked_danger_text', FORM_2),
              ('form3_truncated_inline_code', FORM_3),
              ('form4_unclosed_substitution', FORM_4))
POSITIVE_TEE = ("tee -a .ai_state/sprints/2026-09-20-review-binding-preflight/session-log.md "
                ">/dev/null <<'EOF'\n- note\nEOF")
POSITIVE_TEE_TRUNCATE = ("tee .ai_state/sprints/2026-09-20-contract-parser-diagnostics/cleanup-pass.md "
                         ">/dev/null <<'EOF'\n- note\nEOF")

# --- AC3: every counterexample raised across the seven design-review rounds ---
# Each body/next line carries a real danger so an equal verdict is never vacuous.
NON_NARROW = (
    ('arith_double_paren', "(( 1 << 'a' ))\nrm -rf /\na"),
    ('arith_dollar_double_paren', "x=$(( 1 << 'a' ))\nrm -rf /\na"),
    ('arith_dollar_bracket', "x=$[ 1 << 'a' ]\nrm -rf /\na"),
    ('arith_if_double_paren', "if (( 1 << 'a' )); then :; fi\nrm -rf /\na"),
    ('arith_array_subscript', "v[1<<'i']=1\nrm -rf /\ni"),
    ('expansion_body_literal', "x=${v:-<<'a' }\nrm -rf /\na"),
    ('expansion_offset_arithmetic', "x=${v:1<<'a' }\nrm -rf /\na"),
    ('line_continuation', "cat \\\n<<'EOF'\nrm -rf /\nEOF"),
    ('double_quoted_trailing_backslash', 'echo "a\\\ncat <<\'EOF\'"\nrm -rf /\nEOF'),
    ('quote_spanning_lines', "echo 'a\ncat <<EOF'\nrm -rf /\nEOF"),
    ('comment_pseudo_declaration', "# cat <<EOF\nrm -rf /\nEOF"),
    ('declaration_nested_in_body', "bash <<'OUT'\ncat <<EOF\nrm -rf /\nEOF\nOUT"),
    ('multiple_heredocs_one_line', "cat <<'A' <<'B'\nrm -rf /\nA\nx\nB"),
    ('two_declarations_one_line', "cat <<EOF; cat <<EOF\nrm -rf /\nEOF"),
    ('herestring', "cat <<<'EOF'\nrm -rf /\nEOF"),
    ('escaped_delimiter', "cat <<\\EOF\nrm -rf /\nEOF"),
    ('mixed_quoted_delimiter', 'cat <<E"OF"\nrm -rf /\nEOF'),
    ('literal_marker_in_quotes', "grep '<<EOF' file\nrm -rf /\nEOF"),
    ('delimiter_residue', "cat <<'EOF'x\nrm -rf /\nEOF"),
    ('declaration_not_on_first_line', "echo hi\ncat <<'EOF'\nrm -rf /\nEOF"),
    ('unterminated', "python3 - <<'PYEOF'\nrm -rf /"),
    ('same_line_trailing_command', "cat <<EOF | rm -rf /\nhello\nEOF"),
    ('pipe_on_first_line', "cat <<'EOF' | rm -rf /\nhello\nEOF"),
    ('semicolon_on_first_line', "cat <<'EOF'; rm -rf /\nhello\nEOF"),
    ('brace_on_first_line', "{ cat <<'EOF'; }\nrm -rf /\nEOF"),
    ('backtick_on_first_line', "cat <<'EOF' `rm -rf /`\nhello\nEOF"),
    # Interpreter family: stdin *is* shell code, so today's BLOCK must survive.
    ('interpreter_bash', "bash <<'EOF'\nrm -rf /\nEOF"),
    ('interpreter_sudo_bash', "sudo bash <<'EOF'\nrm -rf /\nEOF"),
    ('interpreter_bash_dash_s', "bash -s <<'EOF'\nrm -rf /\nEOF"),
    ('interpreter_timeout_bash', "timeout 5 bash <<'EOF'\nrm -rf /\nEOF"),
    ('interpreter_push_bypass', "bash <<'EOF'\ngit push origin main --force\nEOF"),
    ('consumer_piped_to_shell', "cat <<'EOF' | bash\ngit push origin main --force\nEOF"),
)

CC_DRIVER = ("const guard = require(process.argv[1]);"
             "const commands = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));"
             "process.stdout.write(JSON.stringify(commands.map(c => guard.analyze(c))));")
CX_DRIVER = ("import importlib.util, json, sys\n"
             "from pathlib import Path\n"
             "guard = Path(sys.argv[1])\n"
             "sys.path.insert(0, str(guard.parent))\n"
             "spec = importlib.util.spec_from_file_location('cx_guard', guard)\n"
             "mod = importlib.util.module_from_spec(spec)\n"
             "spec.loader.exec_module(mod)\n"
             "commands = json.loads(Path(sys.argv[2]).read_text())\n"
             "sys.stdout.write(json.dumps([mod.analyze(c) for c in commands], ensure_ascii=False))\n")
CC_SCAN_DRIVER = ("const lex = require(process.argv[1]);"
                  "const commands = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));"
                  "process.stdout.write(JSON.stringify(commands.map(c => lex.scan(c))));")
CX_SCAN_DRIVER = ("import importlib.util, json, sys\n"
                  "from pathlib import Path\n"
                  "lex = Path(sys.argv[1])\n"
                  "spec = importlib.util.spec_from_file_location('cx_lex', lex)\n"
                  "mod = importlib.util.module_from_spec(spec)\n"
                  "spec.loader.exec_module(mod)\n"
                  "commands = json.loads(Path(sys.argv[2]).read_text())\n"
                  "sys.stdout.write(json.dumps([mod.scan(c) for c in commands], ensure_ascii=False))\n")


def _with_payload(commands, run):
    handle, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(handle, 'w') as fh:
            json.dump(commands, fh)
        completed = run(path)
    finally:
        os.unlink(path)
    if completed.returncode:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


def node_call(module: Path, driver: str, commands):
    return _with_payload(commands, lambda path: subprocess.run(
        ['node', '-e', driver, str(module), path], text=True, capture_output=True))


def python_call(module: Path, driver: str, commands):
    return _with_payload(commands, lambda path: subprocess.run(
        [sys.executable, '-c', driver, str(module), path], text=True, capture_output=True))


def normalize(verdict: dict) -> dict:
    """CC spells the flag allowPush, CX allow_push; the decision is the same."""
    return {('allow_push' if key == 'allowPush' else key): value for key, value in verdict.items()}


def evidence_field(raw: str, key: str):
    """Read one field of the single evidence row; CC and CX quote scalars differently."""
    for line in raw.splitlines():
        stripped = line.strip().lstrip('- ')
        if stripped.startswith(f'{key}:'):
            value = stripped.split(':', 1)[1].strip()
            return json.loads(value) if value.startswith('"') else value
    return None


def baseline_copy(directory: Path, relative: str) -> Path:
    blob = subprocess.run(['git', 'show', f'{BASELINE}:{relative}'], cwd=REPO, capture_output=True)
    if blob.returncode:
        raise AssertionError(blob.stderr.decode('utf-8', 'replace'))
    target = directory / Path(relative).name
    target.write_bytes(blob.stdout)
    return target


class HeredocGuardCase(unittest.TestCase):
    def cc(self, commands):
        return node_call(CC / 'pre-bash-guard.cjs', CC_DRIVER, commands)

    def cx(self, commands):
        return python_call(CX / 'pre-bash-guard.py', CX_DRIVER, commands)

    def assert_both(self, command, expected, label=''):
        self.assertEqual(normalize(self.cc([command])[0]), expected, f'CC {label}')
        self.assertEqual(normalize(self.cx([command])[0]), expected, f'CX {label}')


class TestNarrowQuotedImmunity(HeredocGuardCase):
    """AC1 — the live mis-block forms go through; the positives keep going through."""

    def test_ac1_four_live_forms_are_no_longer_blocked(self):
        for label, command in LIVE_FORMS:
            with self.subTest(label):
                self.assert_both(command, {}, label)

    def test_ac1_positive_tee_samples_still_pass(self):
        for label, command in (('append', POSITIVE_TEE), ('truncate', POSITIVE_TEE_TRUNCATE)):
            with self.subTest(label):
                self.assert_both(command, {}, label)

    def test_ac1_consumer_matrix_five_in_one_out(self):
        for name in CONSUMERS:
            with self.subTest(name):
                self.assert_both(f"{name} - <<'EOF'\nrm -rf /\nEOF", {}, name)
        outside = "perl - <<'EOF'\nrm -rf /\nEOF"
        self.assert_both(outside, {'danger': 'recursive force removal of root/home'}, 'perl')

    def test_ac1_dash_variant_strips_tabs_only(self):
        self.assert_both("cat <<-'EOF'\n\trm -rf /\n\tEOF", {}, 'tab-indented terminator closes')
        self.assert_both("cat <<-'EOF'\n rm -rf /\n EOF",
                         {'danger': 'recursive force removal of root/home'},
                         'space-indented terminator does not close')

    def test_ac1_terminator_trailing_whitespace_rules(self):
        self.assert_both("cat <<'EOF'\nrm -rf /\nEOF ",
                         {'danger': 'recursive force removal of root/home'},
                         'trailing space does not close')
        # Deliberate deviation from bash (bash does not close on EOF\r): closing
        # early can only over-block, never under-block.
        self.assert_both("cat <<'EOF'\nrm -rf /\nEOF\r\necho done", {}, 'trailing CR closes')

    def test_ac1_lines_after_the_terminator_are_still_analyzed(self):
        self.assert_both("python3 - <<'PYEOF'\nprint(1)\nPYEOF\ngit push origin main",
                         {'push': True, 'allow_push': False}, 'push after terminator still gated')
        self.assert_both("python3 - <<'PYEOF'\ngit push origin main\nPYEOF",
                         {}, 'push text inside a masked body is not a command')


class TestUnquotedUnion(HeredocGuardCase):
    """AC2 — unquoted bodies keep the main stream and add the body-only scan."""

    def test_ac2_comment_shadowed_substitution_is_now_caught(self):
        self.assert_both("cat <<EOF\n# $(rm -rf /)\nEOF",
                         {'danger': 'recursive force removal of root/home'}, 'closed hole')

    def test_ac2_substitution_before_apostrophe_still_blocks(self):
        self.assert_both("cat <<EOF\n$(rm -rf /) don't\nEOF",
                         {'danger': 'recursive force removal of root/home'}, 'mainstream pin')

    def test_ac2_apostrophe_before_substitution_is_unchanged(self):
        # Pre-existing shadowing defect, out of scope for this slice: the union
        # structure must not change it in either direction.
        self.assert_both("cat <<EOF\ndon't $(rm -rf /)\nEOF", {}, 'existing defect unchanged')

    def test_ac2_benign_unquoted_body_still_passes(self):
        self.assert_both("cat <<EOF\nhello world\nEOF", {}, 'benign')


class TestNonNarrowByteEquivalence(unittest.TestCase):
    """AC3 — same input through the pre-change and post-change guards, both ends."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        directory = Path(cls._tmp.name)
        cls.old_cc = baseline_copy(directory, 'vibeCoding/claude/9.9.9/.claude/hooks/pre-bash-guard.cjs')
        cls.old_cx = baseline_copy(directory, 'vibeCoding/codex/9.9.9/.codex/hooks/pre-bash-guard.py')

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_ac3_every_review_counterexample_keeps_its_verdict(self):
        commands = [command for _, command in NON_NARROW]
        for label, old, new in (
            ('cc', node_call(self.old_cc, CC_DRIVER, commands), node_call(CC / 'pre-bash-guard.cjs', CC_DRIVER, commands)),
            ('cx', python_call(self.old_cx, CX_DRIVER, commands), python_call(CX / 'pre-bash-guard.py', CX_DRIVER, commands)),
        ):
            for (name, _), before, after in zip(NON_NARROW, old, new):
                with self.subTest(f'{label}:{name}'):
                    self.assertTrue(before, f'{name} must be a real finding, else equality is vacuous')
                    self.assertEqual(before, after, name)

    def test_ac3_interpreter_family_is_still_blocked(self):
        interpreters = [(name, command) for name, command in NON_NARROW
                        if name.startswith('interpreter_') or name == 'consumer_piped_to_shell']
        self.assertEqual(len(interpreters), 6)
        commands = [command for _, command in interpreters]
        for label, verdicts in (('cc', node_call(CC / 'pre-bash-guard.cjs', CC_DRIVER, commands)),
                                ('cx', python_call(CX / 'pre-bash-guard.py', CX_DRIVER, commands))):
            for (name, _), verdict in zip(interpreters, verdicts):
                with self.subTest(f'{label}:{name}'):
                    self.assertTrue(normalize(verdict).get('danger') or normalize(verdict).get('push'), name)


class TestSingleSourceAndFallback(unittest.TestCase):
    """AC4 — one whitelist implementation, lazily loaded, failing to today's behavior."""

    def test_ac4_whitelist_lives_only_in_the_lexer(self):
        for lexer, guard in ((CC / '_shell-lex.cjs', CC / 'pre-bash-guard.cjs'),
                             (CX / '_shell_lex.py', CX / 'pre-bash-guard.py')):
            lexer_text, guard_text = lexer.read_text(), guard.read_text()
            with self.subTest(lexer.name):
                for consumer in CONSUMERS:
                    self.assertIn(f"'{consumer}'", lexer_text, consumer)
                    self.assertNotIn(f"'{consumer}'", guard_text, f'{consumer} duplicated in guard')
                self.assertNotIn('<<', guard_text, 'heredoc grammar must not be restated in the guard')

    def test_ac4_guard_survives_a_missing_or_broken_lexer(self):
        payload = json.dumps({'tool_input': {'command': FORM_1}})
        with tempfile.TemporaryDirectory() as tmp:
            for end, runner, guard_name, lexer_name, stub in (
                ('cc', ['node'], 'pre-bash-guard.cjs', '_shell-lex.cjs',
                 "module.exports = { scan() { throw new Error('boom'); },"
                 " simpleHeredoc() { throw new Error('boom'); } };\n"),
                ('cx', [sys.executable], 'pre-bash-guard.py', '_shell_lex.py',
                 "def scan(command):\n    raise RuntimeError('boom')\n\n\n"
                 "def simple_heredoc(command):\n    raise RuntimeError('boom')\n"),
            ):
                source = CC if end == 'cc' else CX
                for mode in ('missing', 'broken'):
                    directory = Path(tmp) / f'{end}-{mode}'
                    shutil.copytree(source, directory, ignore=shutil.ignore_patterns('__pycache__'))
                    if mode == 'missing':
                        (directory / lexer_name).unlink()
                    else:
                        (directory / lexer_name).write_text(stub)
                    run = subprocess.run(runner + [str(directory / guard_name)], input=payload,
                                         text=True, capture_output=True)
                    with self.subTest(f'{end}:{mode}'):
                        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                        self.assertIn('BLOCKED', run.stderr)

    def test_ac4_guard_allows_the_live_form_when_the_lexer_is_present(self):
        payload = json.dumps({'tool_input': {'command': FORM_1}})
        for runner, guard in ((['node'], CC / 'pre-bash-guard.cjs'),
                              ([sys.executable], CX / 'pre-bash-guard.py')):
            run = subprocess.run(runner + [str(guard)], input=payload, text=True, capture_output=True)
            with self.subTest(guard.name):
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_ac4_evidence_scan_exempts_a_narrow_quoted_body(self):
        narrow = "python3 - <<'PY'\na | b; c\nPY"
        for label, segments in (('cc', node_call(CC / '_shell-lex.cjs', CC_SCAN_DRIVER, [narrow])[0]),
                                ('cx', python_call(CX / '_shell_lex.py', CX_SCAN_DRIVER, [narrow])[0])):
            with self.subTest(label):
                self.assertEqual([segment['text'] for segment in segments],
                                 ["python3 - <<'PY'", 'a | b; c\nPY'])

    def test_ac4_evidence_scan_is_unchanged_outside_the_narrow_form(self):
        wide = "bash <<'EOF'\na | b\nEOF"
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            old_cc = baseline_copy(directory, 'vibeCoding/claude/9.9.9/.claude/hooks/_shell-lex.cjs')
            old_cx = baseline_copy(directory, 'vibeCoding/codex/9.9.9/.codex/hooks/_shell_lex.py')
            self.assertEqual(node_call(CC / '_shell-lex.cjs', CC_SCAN_DRIVER, [wide]),
                             node_call(old_cc, CC_SCAN_DRIVER, [wide]))
            self.assertEqual(python_call(CX / '_shell_lex.py', CX_SCAN_DRIVER, [wide]),
                             python_call(old_cx, CX_SCAN_DRIVER, [wide]))


class TestCodexDecisionTruncation(unittest.TestCase):
    """AC5 — the Codex collector must classify and grade the *whole* command."""

    # `npm test` lands before 4000 chars, `| tail -8` after it: the pre-change
    # collector graded a masked pipeline as a provable pass.
    MASKED_PIPELINE = 'npm test ' + ('-v ' * 1400) + '| tail -8'

    def setUp(self):
        self.assertGreater(self.MASKED_PIPELINE.index('| tail -8'), 4000)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _collect(self, end: str) -> str:
        root = Path(self._tmp.name) / end
        root.mkdir()
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        sprint = root / '.ai_state/sprints/test'
        sprint.mkdir(parents=True)
        (root / '.ai_state/_index.md').write_text('---\nversion: "9.9.9"\ncurrent_sprint_slug: "test"\n---\n')
        (sprint / 'design.md').write_text('## Done Contract\n- AC1: grades the whole command\n')
        (root / 'app.py').write_text('print(1)\n')
        subprocess.run(['git', '-C', str(root), 'add', 'app.py'], check=True)
        subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base'], check=True)
        payload = {'cwd': str(root), 'tool_use_id': f'{end}-masked-pipeline', 'tool_name': 'Bash',
                   'hook_event_name': 'PreToolUse', 'tool_input': {'command': self.MASKED_PIPELINE}}
        hooks = CC if end == 'cc' else CX
        pre = ['node', str(hooks / 'pre-bash-guard.cjs')] if end == 'cc' else [sys.executable, str(hooks / 'pre-bash-guard.py')]
        post = ['node', str(hooks / 'evidence-collector.cjs')] if end == 'cc' else [sys.executable, str(hooks / 'evidence-collector.py')]
        run = subprocess.run(pre, input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        payload.update(hook_event_name='PostToolUse', tool_response={'exit_code': 0, 'stdout': 'ok'})
        run = subprocess.run(post, input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        return (sprint / 'evidence.yaml').read_text()

    def test_ac5_masked_pipeline_beyond_4000_chars_is_unknown_on_both_ends(self):
        for end in ('cc', 'cx'):
            raw = self._collect(end)
            with self.subTest(end):
                self.assertEqual(evidence_field(raw, 'result'), 'unknown')
                self.assertEqual(evidence_field(raw, 'result_reason'), 'pipeline_without_pipefail')

    def test_ac5_persisted_command_stays_bounded(self):
        raw = self._collect('cx')
        persisted = evidence_field(raw, 'command')
        self.assertLessEqual(len(persisted), 500)
        self.assertGreater(len(persisted), 120)


class TestTriEndConsistency(HeredocGuardCase):
    """AC7 — CC and Pi ship the same bytes; Codex reaches the same verdicts."""

    def test_ac7_cc_and_pi_hook_bytes_match(self):
        for name in ('_shell-lex.cjs', 'pre-bash-guard.cjs'):
            self.assertEqual((CC / name).read_bytes(), (PI / name).read_bytes(), name)

    def test_ac7_codex_agrees_with_claude_on_every_fixture(self):
        commands = ([command for _, command in LIVE_FORMS]
                    + [POSITIVE_TEE, POSITIVE_TEE_TRUNCATE]
                    + [f"{name} - <<'EOF'\nrm -rf /\nEOF" for name in CONSUMERS]
                    + ["cat <<EOF\n# $(rm -rf /)\nEOF", "cat <<EOF\ndon't $(rm -rf /)\nEOF"]
                    + [command for _, command in NON_NARROW])
        claude = [normalize(verdict) for verdict in self.cc(commands)]
        codex = [normalize(verdict) for verdict in self.cx(commands)]
        for command, left, right in zip(commands, claude, codex):
            with self.subTest(command.splitlines()[0]):
                self.assertEqual(left, right)


if __name__ == '__main__':
    unittest.main()
