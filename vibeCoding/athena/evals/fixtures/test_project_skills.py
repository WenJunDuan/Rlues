"""Project-pack upgrade planning stays read-only and removes owned global entries."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_build import ATHENA, RELEASE, build


class ProjectSkills(unittest.TestCase):
    def test_upgrade_retires_only_recorded_product_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / 'dist'
            self.assertEqual(build(dist).returncode, 0)
            home = root / 'home'
            owned = '.claude/skills/ui-consistency/SKILL.md'
            user = '.claude/skills/ui-consistency/custom.md'
            for rel in (owned, user):
                p = home / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('local content')
            (home / '.athena').mkdir()
            (home / '.athena/installed.json').write_text(json.dumps({'files': [{'path': owned, 'kind': 'cc'}]}))
            driver = '''const p=require(process.argv[1]);
const result=p.plan(process.argv[2],['cc'],{root:process.argv[3],release:process.argv[4]});
process.stdout.write(JSON.stringify(result.actions.filter(a=>a.action==='retire').map(a=>a.dest)));'''
            run = subprocess.run(['node', '-e', driver, str(ATHENA / 'gate/cli/lib/install-plan.cjs'),
                                  str(home), str(dist), RELEASE], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            retired = json.loads(run.stdout)
            self.assertIn(owned, retired)
            self.assertNotIn(user, retired)
            self.assertTrue((home / owned).is_file(), 'planning must not mutate HOME')
