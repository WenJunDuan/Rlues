"""Pi adapter: hard Stop through agent_before_settle, single-boundary counting, codemode (athena-10-5 S4 AC7).

The Pi extension (.ts) cannot be loaded here; it only forwards what `gate/platform/pi.cjs` renders, so
these fixtures send the raw Pi payloads through `run('pi', …)` exactly as the extension does.
"""
import json
import subprocess
import unittest

from gate_harness import ENV, GATE, GOOD_DESIGN, HOOK, PI_DRIVER, green, project, set_index, tmpdir

SUPPORT = ("const a=require(process.argv[1]);"
           "process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(v=>a.supportsHardStop(v))));")


def pi(root, event, **body):
    proc = subprocess.run(['node', '-e', PI_DRIVER, str(HOOK)], input=json.dumps({'type': event, 'cwd': str(root), **body}),
                          text=True, capture_output=True, cwd=str(root), env=ENV)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout or '{}')


def ledger(root):
    file = root / '.ai_state/.runtime/gate-ledger.jsonl'
    return [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []


def gate_issues(root):
    file = root / '.ai_state/issues.md'
    return [line for line in file.read_text(encoding='utf-8').splitlines() if '熔断放行' in line] if file.exists() else []


class HardStop(unittest.TestCase):
    def ship(self):
        return project(tmpdir(self), path='Feature', stage='ship', design=GOOD_DESIGN)

    def test_ship_without_evidence_renders_continue_form(self):
        root = self.ship()
        out = pi(root, 'agent_before_settle', outcome='completed')
        self.assertIs(out.get('continue'), True, out)
        self.assertTrue(out['reason'].startswith('[athena H2]'), out)
        self.assertEqual(len(out['entries']), 1)
        entry = out['entries'][0]
        # CustomMessageEntryDraft (Pi src/core/extensions/types.ts): exactly these keys, content carries the reason.
        self.assertEqual(set(entry), {'type', 'customType', 'content', 'display'})
        self.assertEqual((entry['type'], entry['customType'], entry['display']), ('custom_message', 'athena-stop', True))
        self.assertIn(out['reason'], entry['content'])
        self.assertEqual([row['event'] for row in ledger(root)], ['block'])

    def test_outcome_absent_is_treated_as_completed(self):
        self.assertIs(pi(self.ship(), 'agent_before_settle').get('continue'), True)

    def test_non_ship_and_idle_render_nothing(self):
        impl = project(tmpdir(self), path='Feature', stage='impl', design=GOOD_DESIGN)
        idle = project(tmpdir(self), name='idle', path='', stage='')
        for root in (impl, idle):
            with self.subTest(root=root.name):
                out = pi(root, 'agent_before_settle', outcome='completed')
                self.assertEqual(out, {'warnings': []})
                self.assertEqual(ledger(root), [])

    def test_aborted_or_failed_run_is_not_forced_and_not_counted(self):
        root = self.ship()
        for outcome in ('aborted', 'error'):
            with self.subTest(outcome=outcome):
                self.assertEqual(pi(root, 'agent_before_settle', outcome=outcome), {'warnings': []})
        self.assertEqual(ledger(root), [])

    def test_breaker_releases_after_repeats_then_no_continue(self):
        root = self.ship()
        first, second = (pi(root, 'agent_before_settle', outcome='completed') for _ in range(2))
        self.assertTrue(first.get('continue') and second.get('continue'))
        third = pi(root, 'agent_before_settle', outcome='completed')
        self.assertNotIn('continue', third)
        self.assertNotIn('entries', third)
        self.assertNotIn('stop', third)
        self.assertTrue(any('circuit breaker' in w for w in third['warnings']), third)
        self.assertEqual([(row['event'], row['consecutive']) for row in ledger(root)], [('block', 1), ('block', 2), ('release', 3)])
        self.assertEqual(len(gate_issues(root)), 1)

    def test_agent_end_does_not_double_count_when_hard_stop_is_on(self):
        root = self.ship()
        # The real order per settlement: agent_end, then agent_before_settle. Two settlements must not trip the breaker.
        for n in (1, 2):
            with self.subTest(settlement=n):
                self.assertEqual(pi(root, 'agent_end', hardStop=True), {'warnings': []})
                self.assertIs(pi(root, 'agent_before_settle', outcome='completed').get('continue'), True)
        self.assertEqual([(row['event'], row['consecutive']) for row in ledger(root)], [('block', 1), ('block', 2)])
        self.assertEqual(gate_issues(root), [])

    def test_agent_end_is_the_soft_fallback_without_hard_stop(self):
        root = self.ship()
        for body in ({}, {'hardStop': False}):
            with self.subTest(body=body):
                out = pi(root, 'agent_end', **body)
                self.assertIs(out.get('stop'), True, out)
                self.assertIn('H2', out['reason'])
                self.assertNotIn('continue', out)
                self.assertNotIn('entries', out)

    def test_passing_ship_renders_no_continue(self):
        root = project(tmpdir(self), path='Quick', stage='ship', design=GOOD_DESIGN)
        self.assertEqual(green(root).returncode, 0)
        out = pi(root, 'agent_before_settle', outcome='completed')
        self.assertNotIn('continue', out)
        self.assertNotIn('stop', out)

    def test_hard_stop_feature_detection_by_host_version(self):
        versions = ['1.0.2', '0.87.0', '0.87.1', '0.99.2', '2.1.0-beta.1', '0.86.1', '0.9.0', '', None, 'next']
        proc = subprocess.run(['node', '-e', SUPPORT, str(GATE / 'platform/pi.cjs'), json.dumps(versions)],
                              capture_output=True, text=True, env=ENV, check=True)
        self.assertEqual(json.loads(proc.stdout), [True, True, True, True, True, False, False, False, False, False])


class Codemode(unittest.TestCase):
    def setUp(self):
        self.root = project(tmpdir(self), path='Feature', stage='impl')  # sprint in flight, no design.md → no AC

    def test_outer_codemode_call_is_allowed(self):
        code = "await tools.write({path: 'app.js', content: 'x'}); await tools.bash({command: 'git push --force'});"
        out = pi(self.root, 'tool_call', toolName='codemode', input={'code': code})
        self.assertEqual(out, {'warnings': []})

    def test_nested_write_without_ac_is_blocked(self):
        for tool, extra in (('write', {'content': 'x'}), ('edit', {'edits': [{'oldText': '1', 'newText': '2'}]})):
            with self.subTest(tool=tool):
                out = pi(self.root, 'tool_call', toolName=tool, parentToolCallId='call_1', toolCallId='call_1/1',
                         input={'path': 'app.js', **extra})
                self.assertIs(out.get('block'), True, out)
                self.assertIn('H1', out['reason'])

    def test_nested_calls_judged_like_direct_ones(self):
        nested = {'parentToolCallId': 'call_1', 'toolCallId': 'call_1/2'}
        self.assertEqual(pi(self.root, 'tool_call', toolName='read', input={'path': 'app.js'}, **nested), {'warnings': []})
        self.assertEqual(pi(self.root, 'tool_call', toolName='bash', input={'command': 'ls'}, **nested), {'warnings': []})
        direct = pi(self.root, 'tool_call', toolName='write', input={'path': 'app.js', 'content': 'x'})
        self.assertIs(direct.get('block'), True)
        with_ac = project(tmpdir(self), name='ac', path='Feature', stage='impl', design=GOOD_DESIGN)
        allowed = pi(with_ac, 'tool_call', toolName='write', input={'path': 'app.js', 'content': 'x'}, **nested)
        self.assertNotIn('block', allowed)


if __name__ == '__main__':
    unittest.main()
