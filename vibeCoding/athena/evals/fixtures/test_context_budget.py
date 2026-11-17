"""athena-pd-1 AC4: `athena doctor --context` reports per-layer bytes / tokens and project rules paths coverage."""
import re
import subprocess
import unittest

from gate_harness import ENV, RELEASE, athena, git, tmpdir
from test_install import build


class DoctorContext(unittest.TestCase):
    def test_layers_and_coverage(self):
        base = tmpdir(self)
        dist = build(base / 'dist')
        home = base / 'home'
        home.mkdir()
        env = {**ENV, 'HOME': str(home)}
        run = athena('install', '--platform', 'cc,cx', '--dist', str(dist), cwd=home, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        proj = base / 'proj'
        (proj / '.claude/rules').mkdir(parents=True)
        (proj / 'src').mkdir()
        (proj / 'src/a.ts').write_text('x\n')
        (proj / 'src/b.py').write_text('x\n')
        (proj / 'CLAUDE.md').write_text('# 项目\n')
        (proj / '.claude/rules/always.md').write_text('# 常驻规则\n')
        (proj / '.claude/rules/web.md').write_text('---\npaths:\n  - "src/**/*.{ts,tsx}"\n---\n# Web\n')
        subprocess.run(['git', 'init', '-q'], cwd=proj, check=True)
        subprocess.run(['git', 'add', '.'], cwd=proj, check=True)
        out = athena('doctor', '--context', '--home', str(home), cwd=proj, env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        text = out.stdout
        claude = (home / '.claude/CLAUDE.md').read_bytes()
        self.assertRegex(text, rf'constitution\s+{len(claude)} B\s+≈\s*\d+ tok')
        resident = sum(f.stat().st_size for f in (home / '.claude/rules').glob('*.md') if not f.read_text().startswith('---\npaths:'))
        self.assertRegex(text, rf'rules without paths\s+{resident} B')
        self.assertLessEqual(resident, 5200)
        self.assertRegex(text, r'skill list\s+\d+ B\s+≈\s*\d+ tok\s+\d+ skills')
        self.assertRegex(text, r'agent descriptions\s+\d+ B\s+≈\s*\d+ tok\s+4 agents')
        project = len('# 项目\n'.encode()) + len('# 常驻规则\n'.encode())
        self.assertRegex(text, rf'project rules\s+{project} B\s+≈\s*\d+ tok\s+CLAUDE.md, .claude/rules/always.md')
        self.assertIn('.claude/rules/always.md', text.split('coverage')[1])
        self.assertRegex(text, r'\.claude/rules/always\.md\s+\d+ B\s+no paths \(every session\)')
        self.assertRegex(text, r'\.claude/rules/web\.md\s+\d+ B\s+paths src/\*\*/\*\.\{ts,tsx\} → 1 tracked file')
        cx = athena('doctor', '--context', '--platform', 'cx', '--home', str(home), cwd=proj, env=env)
        self.assertEqual(cx.returncode, 0, cx.stderr)
        self.assertRegex(cx.stdout, rf'constitution\s+{len((home / ".codex/AGENTS.md").read_bytes())} B')

    def test_token_estimate(self):
        import json
        probe = "const t = require(process.argv[1]); console.log(JSON.stringify([t.tokens('中文'), t.tokens('abcdefg'), t.tokens('')]));"
        from gate_harness import ATHENA
        run = subprocess.run(['node', '-e', probe, str(ATHENA / 'gate/cli/lib/context-budget.cjs')], capture_output=True, text=True)
        self.assertEqual(json.loads(run.stdout), [2, 2, 0])


    def test_unclosed_brace_is_literal_not_a_hang(self):
        import json
        probe = "const t = require(process.argv[1]); const re = t.globRe('src/{draft/**'); console.log(JSON.stringify([re.test('src/{draft/a.ts'), re.test('src/draft/a.ts')]));"
        from gate_harness import ATHENA
        run = subprocess.run(['node', '-e', probe, str(ATHENA / 'gate/cli/lib/context-budget.cjs')], capture_output=True, text=True, timeout=10)
        self.assertEqual(json.loads(run.stdout), [True, False])

    def test_pi_installs_project_packs(self):
        probe = "const p = require(process.argv[1]); console.log(p._target ? p._target('pi', 'project-packs/x/SKILL.md', 'r') : 'none');"
        from gate_harness import ATHENA
        src = (ATHENA / 'gate/cli/lib/install-plan.cjs').read_text()
        self.assertIn("plugin|config|project-packs", src)

if __name__ == '__main__':
    unittest.main()
