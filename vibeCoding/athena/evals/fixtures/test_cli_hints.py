"""Refusals carry the fix (athena-10-1-5 S1 AC2): `athena run` unprovable records print a provable
form, a malformed --covers prints a corrected sample, every `review accept` refusal ends with
`next: <command>`. Exit codes and what is accepted stay as they were."""
import json
import os
import time
import unittest

from gate_harness import ENV, GOOD_DESIGN, athena, check_file, project, tmpdir
from test_review_cli import PASS_OUT, accept, ready
from test_state_cli import ok, v2project

FORM = '[athena run] provable form: '


def form(run):
    lines = [line[len(FORM):] for line in run.stderr.splitlines() if line.startswith(FORM)]
    return lines[0] if lines else ''


class RunProvableForms(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir(self)
        self.root = project(self.tmp, design=GOOD_DESIGN)
        self.green = check_file(self.root)

    def run_(self, *args, env=None):
        return athena('run', *args, cwd=self.root, env=env)

    def test_each_unprovable_reason_prints_its_form(self):
        g = self.green
        cases = [
            ('wrapped_command', ('--', 'bash', '-c', f'node --test {g}'), 'athena run -- npm test'),
            ('validation_status_not_reported', ('--', f'node --test {g}; echo done'), 'follow it with `&&` only'),
            ('validation_may_not_run', ('--', f'false || node --test {g}'), 'chain with `&&` only'),
            ('validation_backgrounded', ('--', f'node --test {g} &'), 'drop the trailing `&`'),
            ('pipeline_without_pipefail', ('--', f'set +o pipefail; node --test {g} | tail -1'), 'pipe hides'),
            ('validation_shadowable', ('--env', 'NODE_OPTIONS=--no-warnings', '--', 'node', '--test', g), 'athena run --env FOO=1 -- npm test'),
            ('validation_shadowable', ('--', f'PATH=/usr/bin:/bin node --test {g}'), 'project config'),
            ('zero_tests', ('--', 'node', '--test', str(self.tmp / 'unmatched/*.test.cjs')), 'npm test --workspace <pkg>'),
            ('tree_changed_during_run', ('--', f'node --test {g} && echo x > generated.txt'), '.gitignore'),
        ]
        for reason, args, needle in cases:
            with self.subTest(reason=reason, args=args):
                run = self.run_(*args)
                self.assertIn(f'provable=false ({reason}', run.stderr)
                self.assertIn(needle, form(run), run.stderr)
                self.assertEqual(run.stderr.strip().splitlines()[-1][:len(FORM)], FORM, 'the form follows the reason line')

    def test_unrecognized_kind_lists_recognized_commands(self):
        run = self.run_('--', 'echo', 'hi')
        self.assertIn('kind=other provable=false', run.stderr)
        for needle in ('test / typecheck / build / docs', 'athena run -- npm test', 'npx tsc --noEmit', 'grep -F -q'):
            self.assertIn(needle, form(run))

    def test_ssh_forms(self):
        bin_dir = self.tmp / 'bin'
        bin_dir.mkdir()
        (bin_dir / 'ssh').write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        (bin_dir / 'ssh').chmod(0o755)
        home = self.tmp / 'home'
        (home / '.athena').mkdir(parents=True)
        (home / '.athena/vm.json').write_text(json.dumps({'vms': [{'name': 'dev', 'host': '10.0.0.5', 'user': 'root'}]}), encoding='utf-8')
        env = {'HOME': str(home), 'PATH': f"{bin_dir}{os.pathsep}{ENV['PATH']}"}
        for args in (('--', 'ssh', 'root@10.0.0.6', 'npm test'), ('--', "ssh root@10.0.0.5 'npm test'")):  # unregistered; shell form
            with self.subTest(args=args):
                text = form(self.run_(*args, env=env))
                self.assertIn('~/.athena/vm.json', text)
                self.assertIn("athena run -- ssh user@host '", text)
        run = self.run_('--', 'ssh', 'root@10.0.0.5', 'npm test | tail -3', env=env)
        self.assertIn('pipeline_without_pipefail', run.stderr)
        self.assertIn("ssh user@host 'set -o pipefail; npm test | tail -20'", form(run))
        self.assertEqual(form(self.run_('--', 'ssh', 'root@10.0.0.5', 'cd /opt/w && npm test', env=env)), '')

    def test_provable_and_plain_failures_print_no_form(self):
        self.assertEqual(form(ok(self, self.run_('--', 'node', '--test', self.green))), '')
        self.assertEqual(form(ok(self, self.run_('--', f'node --test {self.green} | tail -1'))), '')  # pipefail is on
        red = self.run_('--', 'node', '--test', check_file(self.root, passing=False))
        self.assertNotEqual(red.returncode, 0)
        self.assertEqual(form(red), '')

    def test_malformed_covers_shows_corrected_sample(self):
        for raw, fixed in (('ac1,AC-2', 'AC1,AC2'), ('AC1 AC3', 'AC1,AC3'), ('1', 'AC1'), ('first', 'AC1,AC2')):
            with self.subTest(raw=raw):
                run = self.run_('--covers', raw, '--', 'node', '--test', self.green)
                self.assertEqual(run.returncode, 2)
                self.assertIn(f'sample: athena run --covers {fixed} -- <cmd…>', run.stderr)
                self.assertIn(f'got "{raw}"', run.stderr)
        self.assertFalse((self.root / '.ai_state/.runtime/evidence').exists(), 'nothing ran')
        ok(self, self.run_('--covers', 'AC1,AC2', '--', 'node', '--test', self.green))
        self.assertIn('sample: athena run --env FOO=1', self.run_('--env', 'FOO', '--', 'true').stderr)


class ReviewAcceptRefusals(unittest.TestCase):
    def setUp(self):
        self.root = v2project(tmpdir(self))

    def prepared(self):
        ready(self, self.root)
        return ok(self, athena('review', 'prepare', cwd=self.root)).stdout.split()[1]

    def last(self, run):
        return run.stderr.strip().splitlines()[-1]

    def test_contract_errors_show_sample_lines_and_next(self):
        run_id = self.prepared()
        for text in ('no verdict here\n', 'VERDICT: PASS\nVERDICT: FAIL\n', '**VERDICT: FAIL**\n', '- [P1] app.js:1: broken\nVERDICT: REWORK\n',
                     '* [P1] app.js:1 — x\nVERDICT: REWORK\n', '- [P2] evidence: — missing id\nVERDICT: CONCERNS\n',
                     '- [P1] app.js:1 — broken\nVERDICT: PASS\n', '```\nVERDICT: PASS\n'):
            with self.subTest(text=text):
                run = accept(self.root, text)
                self.assertEqual(run.returncode, 2)
                self.assertIn('- [P2] src/app.js:42 — <what is wrong>', run.stderr)
                self.assertIn('- [P3] evidence:<id> — <text>', run.stderr)
                self.assertIn('VERDICT: CONCERNS', run.stderr)
                self.assertTrue(self.last(run).startswith(f'next: athena review accept --run {run_id} --file <reviewer output>'), run.stderr)
        self.assertFalse((self.root / '.ai_state/sprints/s-x/review.json').exists())

    def test_stale_tree_and_changed_acceptance_point_at_prepare(self):
        self.prepared()
        (self.root / 'app.js').write_text('module.exports = 3;\n', encoding='utf-8')
        run = accept(self.root, PASS_OUT)
        self.assertEqual((run.returncode, self.last(run)), (4, 'next: athena review prepare'))
        (self.root / 'app.js').write_text('module.exports = 2;\n', encoding='utf-8')
        design = self.root / '.ai_state/sprints/s-x/design.md'
        design.write_text(design.read_text(encoding='utf-8') + '- AC2: sub returns 0\n', encoding='utf-8')
        run = accept(self.root, PASS_OUT)
        self.assertEqual((run.returncode, self.last(run)), (4, 'next: athena review prepare'))

    def test_non_pass_verdict_names_the_follow_up(self):
        self.prepared()
        run = accept(self.root, '- [P1] app.js:1 — returns wrong value\nVERDICT: REWORK\n')
        self.assertEqual(run.returncode, 3)
        self.assertTrue(self.last(run).startswith('next: athena review show'))
        self.assertIn('athena review prepare', self.last(run))
        self.assertEqual(json.loads((self.root / '.ai_state/sprints/s-x/review.json').read_text())['verdict'], 'REWORK')

    def test_usage_refusals_end_with_next(self):
        self.assertEqual(self.last(athena('review', 'accept', cwd=tmpdir(self))), 'next: athena init')
        ready(self, self.root)
        out = self.root.parent / 'review-out.md'
        out.write_text(PASS_OUT, encoding='utf-8')
        run = athena('review', 'accept', '--file', str(out), cwd=self.root)
        self.assertEqual((run.returncode, self.last(run)), (2, 'next: athena review prepare'))  # nothing prepared
        time.sleep(0.05)
        run_id = ok(self, athena('review', 'prepare', cwd=self.root)).stdout.split()[1]
        again = f'next: athena review accept --run {run_id} --file <reviewer output>'
        for args, start in ((('--run', 'latest', '--file', str(out)), again),               # output older than the packet
                            (('--run', 'latest', '--file', 'missing.md'), again),
                            (('--run', 'nope', '--file', str(out)), 'next: athena review accept --run latest'),
                            (('--bogus',), 'next: athena review accept --run latest')):
            with self.subTest(args=args):
                run = athena('review', 'accept', *args, cwd=self.root)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertTrue(self.last(run).startswith(start), run.stderr)

    def test_reused_output_and_pass_path(self):
        self.prepared()
        run = accept(self.root, PASS_OUT)
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        time.sleep(0.05)
        run_id = ok(self, athena('review', 'prepare', cwd=self.root)).stdout.split()[1]
        time.sleep(0.05)
        run = accept(self.root, PASS_OUT)  # same bytes, new run
        self.assertEqual(run.returncode, 2)
        self.assertTrue(self.last(run).startswith(f'next: athena review accept --run {run_id} --file <reviewer output>'), run.stderr)


if __name__ == '__main__':
    unittest.main()
