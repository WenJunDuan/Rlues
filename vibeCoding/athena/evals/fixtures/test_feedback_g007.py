import json
import unittest
from gate_harness import GATE, ENV
import subprocess

class ReviewLocations(unittest.TestCase):
    def parse(self, text):
        code = "try { console.log(JSON.stringify(require(process.argv[1]).parseOutput(process.argv[2]))); } catch(e) { console.error(e.message); process.exit(2); }"
        return subprocess.run(['node', '-e', code, str(GATE / 'cli/review.cjs'), text], capture_output=True, text=True, env=ENV)

    def test_evidence_packet_design_locations_and_empty_id(self):
        for loc in ('evidence:abc123', 'packet:—', 'design:AC1'):
            with self.subTest(loc=loc):
                run = self.parse(f'- [P2] {loc} — explain\nVERDICT: CONCERNS\n')
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(json.loads(run.stdout)['findings'][0]['loc'], loc)
        self.assertEqual(self.parse('- [P2] evidence: — missing id\nVERDICT: CONCERNS\n').returncode, 2)

    def test_packet_contract_advertises_nonfile_locations(self):
        self.assertIn('<evidence|packet|design>:<id|—>', (GATE / 'cli/review.cjs').read_text())
