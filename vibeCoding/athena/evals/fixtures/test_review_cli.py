"""athena review prepare/accept/show + reviewer contract + gate-pit regressions (athena-10-1 S3 AC1–AC5)."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from gate_harness import ATHENA, ENV, GATE, athena, call, check_file, git, tmpdir
from test_state_cli import ok, v2project

PASS_OUT = '- [P3] app.js:1 — naming nit\nVERDICT: PASS\n'
CONTRACT = re.compile(r'<!-- athena:reviewer-contract v1 -->.*?<!-- /athena:reviewer-contract -->', re.S)


def ready(testcase, root, slug='s-x'):
    ok(testcase, athena('sprint', 'start', 'r/x', '--slug', slug, cwd=root))
    design = root / f'.ai_state/sprints/{slug}/design.md'
    design.write_text(design.read_text(encoding='utf-8') + '\n- AC1: add returns 2\n', encoding='utf-8')
    ok(testcase, athena('sprint', 'stage', 'impl', cwd=root))
    (root / 'app.js').write_text('module.exports = 2;\n', encoding='utf-8')
    ok(testcase, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))


def accept(root, text, *extra):
    out = root.parent / 'review-out.md'
    out.write_text(text, encoding='utf-8')
    return athena('review', 'accept', '--run', 'latest', '--file', str(out), *extra, cwd=root)


class ReviewFlow(unittest.TestCase):
    def test_prepare_accept_show_and_ship(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        prep = ok(self, athena('review', 'prepare', cwd=root)).stdout
        run = re.search(r'^run (\S+)', prep, re.M).group(1)
        packet = (root / f'.ai_state/.runtime/review/{run}/packet.md').read_text(encoding='utf-8')
        for needle in ('AC1: add returns 2', 'app.js', 'review_ignore', 'VERDICT: PASS|CONCERNS|REWORK|FAIL'):
            self.assertIn(needle, packet)
        ok(self, accept(root, PASS_OUT, '--family', 'openai', '--platform', 'cx'))
        review = json.loads((root / '.ai_state/sprints/s-x/review.json').read_text())
        self.assertEqual((review['run'], review['verdict'], review['reviewer']['family']), (run, 'PASS', 'openai'))
        self.assertEqual(review['findings'], [{'sev': 'P3', 'loc': 'app.js:1', 'text': 'naming nit'}])
        self.assertIn('.ai_state/sprints/s-x/review.json', git(root, 'diff', '--cached', '--name-only').stdout)
        self.assertIn('current', ok(self, athena('review', 'show', cwd=root)).stdout)
        ok(self, athena('ship', cwd=root))

    def test_source_change_after_prepare_is_rejected_file_by_file(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        (root / 'app.js').write_text('module.exports = 3;\n', encoding='utf-8')
        (root / 'new.js').write_text('x\n', encoding='utf-8')
        run = accept(root, PASS_OUT)
        self.assertEqual(run.returncode, 4)
        self.assertRegex(run.stderr, r'app\.js: expected [0-9a-f]{12} actual [0-9a-f]{12}')
        self.assertIn('new.js: expected (absent) actual', run.stderr)
        self.assertIn('review prepare', run.stderr)
        self.assertFalse((root / '.ai_state/sprints/s-x/review.json').exists())

    def test_contract_parser(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        for text, code in (('no verdict here\n', 2), ('VERDICT: PASS\nVERDICT: FAIL\n', 2), ('VERDICT: MAYBE\n', 2),
                           ('- [P1] app.js:1 — broken\nVERDICT: PASS\n', 2), ('- [P1] app.js:1 — broken\nVERDICT: REWORK\n', 3),
                           ('**VERDICT: FAIL**\nsee:\n```\nVERDICT: PASS\n```\n', 2), ('VERDICT: FAIL — many issues\nVERDICT: PASS\n', 2),
                           ('- [P0] app.js:1: exploit\nVERDICT: PASS\n', 2), ('- **[P0]** app.js:1 — x\nVERDICT: PASS\n', 2),
                           ('* [P1] app.js:1 — x\nVERDICT: PASS\n', 2), ('1. [P0] app.js:1 — x\nVERDICT: PASS\n', 2),
                           ('- [p1] app.js:1 — x\nVERDICT: PASS\n', 2), ('- [P4] app.js:1 — x\nVERDICT: PASS\n', 2),
                           ('- [P2] review.cjs:1 — the verdict regex is loose\nOverall verdict prose is fine.\nVERDICT: CONCERNS\n', 3),
                           ('- [P3] src/my file.js:1 — spaced path ok\nVERDICT: PASS\n', 0)):
            with self.subTest(text=text):
                self.assertEqual(accept(root, text).returncode, code)
        self.assertEqual(json.loads((root / '.ai_state/sprints/s-x/review.json').read_text())['verdict'], 'PASS')

    def test_usage_errors(self):
        root = v2project(tmpdir(self))
        for args in (('review',), ('review', 'prepare'), ('review', 'accept', '--run', 'nope'), ('review', 'prepare', '--scope', 'x')):
            with self.subTest(args=args):
                self.assertEqual(athena(*args, cwd=root).returncode, 2)


class GatePits(unittest.TestCase):
    """Design §6 table: quantum gate pits #1–#11 as regressions."""

    def test_pit1_fix_findings_then_prepare_again(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        self.assertEqual(accept(root, '- [P1] app.js:1 — returns wrong value\nVERDICT: REWORK\n').returncode, 3)
        (root / 'app.js').write_text('module.exports = 2; // fixed\n', encoding='utf-8')
        ok(self, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, 'VERDICT: PASS\n'))
        ok(self, athena('ship', cwd=root))

    def test_pit5_same_reviewer_again_is_only_advisory(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        for i in range(2):
            ok(self, athena('review', 'prepare', cwd=root))
            ok(self, accept(root, f'- [P3] app.js:1 — note {i}\nVERDICT: PASS\n', '--family', 'anthropic', '--reviewer-agent', 'same-one'))
        ok(self, athena('sprint', 'stage', 'ship', cwd=root))
        self.assertFalse(call('cc', 'stop', root).blocked, 'same reviewer twice never blocks')
        self.assertIn('advisory A10', call('cc', 'prompt', root).context)

    def test_pit6_10_no_tracker_or_receipt_needed_and_pit8_latest(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, 'VERDICT: PASS\n'))  # --run latest, no SubagentStart, no dispatch receipt
        runs = sorted((p for p in (root / '.ai_state/.runtime/review').iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
        self.assertEqual(json.loads((root / '.ai_state/sprints/s-x/review.json').read_text())['run'], runs[-1].name)
        self.assertFalse((root / '.ai_state/.runtime/subagents.jsonl').exists())

    def test_pit11_missing_ac_lists_legal_forms_and_cat_heredoc_warns(self):
        root = v2project(tmpdir(self))
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=root))
        verdict = call('cc', 'write', root, file=root / 'app.js')
        self.assertTrue(verdict.blocked)
        self.assertIn('合法形态', verdict.reason)
        call('cc', 'bash', root, command="cat > notes.md <<'EOF'\nEOF")
        self.assertIn('0 bytes', call('cc', 'prompt', root).context)


class Binding(unittest.TestCase):
    def test_replayed_output_stale_ac_and_old_file_are_refused(self):
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, PASS_OUT))
        (root / 'app.js').write_text('module.exports = 2; // evil\n', encoding='utf-8')
        ok(self, athena('review', 'prepare', cwd=root))
        replay = accept(root, PASS_OUT)
        self.assertEqual(replay.returncode, 2)
        self.assertIn('already accepted', replay.stderr)
        design = root / '.ai_state/sprints/s-x/design.md'
        ok(self, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
        ok(self, accept(root, '- [P3] app.js:1 — fresh look\nVERDICT: PASS\n'))
        design.write_text(design.read_text() + '- AC2: new unreviewed AC\n')
        self.assertIn('acceptance lines changed', ok(self, athena('review', 'show', cwd=root)).stdout)
        ok(self, athena('sprint', 'stage', 'ship', cwd=root))
        self.assertIn('acceptance lines changed', call('cc', 'stop', root).reason)
        ok(self, athena('review', 'prepare', cwd=root))
        old = root.parent / 'stale-output.md'
        old.write_text('VERDICT: PASS\n')
        import os
        os.utime(old, (1, 1))
        run = athena('review', 'accept', '--run', 'latest', '--file', str(old), cwd=root)
        self.assertEqual(run.returncode, 2)
        self.assertIn('older than the packet', run.stderr)

    def test_unknown_family_fails_cross_family_review(self):
        from test_gate_hard import set_index
        root = v2project(tmpdir(self))
        ready(self, root)
        ok(self, athena('review', 'prepare', cwd=root))
        ok(self, accept(root, PASS_OUT))
        set_index(root, stage='ship', flags='{cross_family_review: true}')
        self.assertIn('family is unknown', call('cc', 'stop', root).reason)


class Contract(unittest.TestCase):
    def test_one_contract_three_platforms(self):
        files = [ATHENA / 'adapters/cc/package/agents/reviewer.md', ATHENA / 'adapters/cx/package/agents/reviewer.toml',
                 ATHENA / 'adapters/pi/top/plugin/prompts/reviewer.md']
        blocks = [CONTRACT.search(f.read_text(encoding='utf-8')).group(0) for f in files]
        self.assertEqual(len(set(blocks)), 1)
        for word in ('review_run_id', 'frontmatter:', 'packet_sha256', 'native_output_ref'):
            self.assertNotIn(word, blocks[0])
        self.assertIn('VERDICT: PASS|CONCERNS|REWORK|FAIL', blocks[0])

    def test_workflow_ships_to_cc_and_only_drives_the_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run(['node', str(ATHENA / 'build.mjs'), '--out', tmp], capture_output=True, text=True, env=ENV)
            self.assertEqual(run.returncode, 0, run.stderr)
            wf = Path(tmp) / 'claude/10.1/.claude/workflows/athena-review.js'
            src = wf.read_text(encoding='utf-8')
            self.assertIn("name: 'athena-review'", src)
            self.assertIn('review prepare', src)
            self.assertIn('review accept', src)
            self.assertNotRegex(src, r'writeFile|\bfs\.|require\(', 'the workflow never writes files itself')
            body = src.replace('export const meta', 'const meta')
            check = subprocess.run(['node', '-e', "new (Object.getPrototypeOf(async function(){}).constructor)('agent','parallel',require('fs').readFileSync(0,'utf8'))"],
                                   input=body, text=True, capture_output=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertFalse((Path(tmp) / 'codex/10.1/.codex/workflows').exists())


if __name__ == '__main__':
    unittest.main()
