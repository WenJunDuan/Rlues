"""athena status: AC coverage matrix + ship pre-check (athena-10-5 S2 AC4)."""
import json
import unittest

from gate_harness import athena, check_file, tmpdir
from test_state_cli import ok, snapshot, v2project


def sprint(testcase, root, slug='s-x', acs=('AC1: add returns 2', 'AC2: sub returns 0')):
    ok(testcase, athena('sprint', 'start', 'r/x', '--slug', slug, cwd=root))
    design = root / f'.ai_state/sprints/{slug}/design.md'
    design.write_text(design.read_text(encoding='utf-8') + ''.join(f'\n- {ac}\n' for ac in acs), encoding='utf-8')
    ok(testcase, athena('sprint', 'stage', 'impl', cwd=root))


def view(testcase, root):
    return json.loads(ok(testcase, athena('status', '--json', cwd=root)).stdout)


def states(data):
    return {ac['id']: ac['state'] for ac in data['acs']}


class StatusMatrix(unittest.TestCase):
    def test_idle_output_has_no_matrix(self):
        root = v2project(tmpdir(self))
        data = view(self, root)
        self.assertNotIn('acs', data)
        self.assertNotIn('ship_precheck', data)
        text = ok(self, athena('status', cwd=root)).stdout
        self.assertNotIn('acceptance', text)
        self.assertNotIn('ship pre-check', text)

    def test_missing_then_covered_then_stale(self):
        root = v2project(tmpdir(self))
        sprint(self, root)
        data = view(self, root)
        self.assertEqual(states(data), {'AC1': 'missing', 'AC2': 'missing'})
        self.assertEqual(data['acs'][0]['fix'], 'athena run --covers AC1 -- <test/typecheck/build command>')
        text = ok(self, athena('status', cwd=root)).stdout
        self.assertIn('AC1 [missing] add returns 2', text)
        self.assertIn('athena run --covers AC1 -- ', text)
        self.assertIn('acceptance (0/2 covered', text)

        ok(self, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
        data = view(self, root)
        self.assertEqual(states(data), {'AC1': 'covered', 'AC2': 'missing'})
        self.assertEqual(len(data['acs'][0]['evidence']), 1)
        self.assertEqual(data['acs'][0]['fix'], '')
        self.assertEqual(data['ship_precheck']['uncovered'], ['AC2'])
        self.assertIn('AC1 [covered]', ok(self, athena('status', cwd=root)).stdout)

        (root / 'app.js').write_text('module.exports = 2;\n', encoding='utf-8')  # source edit → new tree
        data = view(self, root)
        self.assertEqual(states(data), {'AC1': 'stale', 'AC2': 'missing'})
        self.assertIn('source changed since', data['acs'][0]['detail'])
        text = ok(self, athena('status', cwd=root)).stdout
        self.assertIn('AC1 [stale]', text)
        self.assertIn('athena run --covers AC1 -- ', text)

    def test_failing_run_is_missing_with_its_exit_code(self):
        root = v2project(tmpdir(self))
        sprint(self, root)
        athena('run', '--covers', 'AC2', '--', 'node', '--test', check_file(root, passing=False), cwd=root)
        ac2 = view(self, root)['acs'][1]
        self.assertEqual(ac2['state'], 'missing')
        self.assertRegex(ac2['detail'], r'record [0-9a-f]+ exited [1-9]')

    def test_ship_precheck_lists_h2_and_h3_with_fixes(self):
        root = v2project(tmpdir(self))
        sprint(self, root)
        pre = view(self, root)['ship_precheck']
        self.assertFalse(pre['ok'])
        rules = {b['rule']: b for b in pre['blockers']}
        self.assertIn('H2 evidence: no evidence recorded for this sprint', rules['H2']['reason'])
        self.assertIn('athena run', rules['H2']['fix'])
        self.assertIn('H3 review:', rules['H3']['reason'])
        self.assertEqual(rules['H3']['fix'], 'athena review prepare')
        text = ok(self, athena('status', cwd=root)).stdout
        self.assertIn('ship pre-check: athena ship would refuse (2)', text)
        self.assertIn('H2 evidence: no evidence recorded', text)
        self.assertIn('→ athena review prepare', text)
        # the same first reason `athena ship` refuses on
        ship = athena('ship', '--dry-run', cwd=root)
        self.assertEqual(ship.returncode, 1)
        self.assertIn(rules['H2']['reason'], ship.stderr)

        ok(self, athena('run', '--covers', 'AC1,AC2', '--', 'node', '--test', check_file(root), cwd=root))
        pre = view(self, root)['ship_precheck']
        self.assertEqual([b['rule'] for b in pre['blockers']], ['H3'])
        self.assertEqual(pre['uncovered'], [])
        (root / 'app.js').write_text('module.exports = 3;\n', encoding='utf-8')
        pre = view(self, root)['ship_precheck']
        self.assertIn('source changed since', {b['rule']: b for b in pre['blockers']}['H2']['reason'])

    def test_status_is_read_only_even_at_ship_stage(self):
        root = v2project(tmpdir(self))
        sprint(self, root)
        ok(self, athena('run', '--covers', 'AC1', '--', 'node', '--test', check_file(root), cwd=root))
        ok(self, athena('sprint', 'stage', 'ship', cwd=root))
        before = snapshot(root)
        for _ in range(4):  # more than the Stop breaker's repeat threshold
            ok(self, athena('status', cwd=root))
            ok(self, athena('status', '--json', cwd=root))
        self.assertEqual(snapshot(root), before)
        self.assertFalse((root / '.ai_state/issues.md').exists() and 'gate' in (root / '.ai_state/issues.md').read_text())

    def test_existing_json_keys_are_kept(self):
        root = v2project(tmpdir(self))
        sprint(self, root)
        data = view(self, root)
        for key in ('route', 'hot', 'waiting', 'queue', 'roadmaps', 'questions', 'issues_open', 'exemptions', 'advisories'):
            self.assertIn(key, data)
        self.assertEqual(data['route']['sprint'], 's-x')


if __name__ == '__main__':
    unittest.main()
