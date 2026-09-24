"""athena-10-1 S5 prompts-v2: constitution, rules, skills, agents (design §9)."""
import re
from pathlib import Path
import tempfile
import unittest

from test_build import ATHENA, build

STALE = re.compile(r'9\.9\.[0-9]|delivery-gate|spec-gate|review-binding|tdd-evidence|review-packet|cleanup-pass\.md|route-note|route_history|'
                   r'checklist\.yaml|\bcritic\b|evaluator|spec-compliance|docs_researcher|pr_explorer|compound/|current_sprint_slug|'
                   r'evidence\.yaml|implementation-review|session-log|subagent-tracker|athena-checkpoint|athena-issue|athena-preferences|'
                   r'antigravity|gate-contracts|execution-contracts|platform-contracts|state-contract|setup-athena\.py|铁律\[|INTJ')
REMOVED_SKILLS = ('antigravity', 'athena-preferences', 'athena-checkpoint', 'athena-issue', 'compound', 'athena-migrate')
ROOTS = {'claude': '.claude', 'codex': '.codex'}


class Prompts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.tmp.name) / 'dist'
        run = build(cls.dist)
        assert run.returncode == 0, run.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def out(self, platform):
        return self.dist / platform / '10.1'

    def constitutions(self):
        return {'claude': self.out('claude') / '.claude/CLAUDE.md', 'codex': self.out('codex') / '.codex/AGENTS.md',
                'pi': self.out('pi') / 'plugin/core/IRON.md'}

    def test_ac1_one_constitution_three_platforms(self):
        texts = {p: f.read_text(encoding='utf-8') for p, f in self.constitutions().items()}
        normal = {p: re.sub(r'\S*/pace/references/', '<SKILLS>/pace/references/', t) for p, t in texts.items()}
        self.assertEqual(len(set(normal.values())), 1, 'three constitutions differ beyond SKILLS_DIR')
        for p, t in texts.items():
            with self.subTest(platform=p):
                self.assertLessEqual(len(t.encode()), 2500)
                self.assertNotIn('INTJ', t)
                self.assertNotIn('/goal', t)
                self.assertIsNone(re.search(r'\*\*[^*]*[A-Z]{4,}', t), 'no all-caps emphasis')
                self.assertIn('review 窗口内还有并行写者', t)   # NV-C2
                self.assertIn('转述别人的结论写出处', t)       # NV-C16

    def test_ac2_rules_budget_and_provenance(self):
        rules = sorted((ATHENA / 'core/package/rules').glob('*.md'))
        self.assertLessEqual(sum(len(f.read_text(encoding='utf-8').splitlines()) for f in rules), 300)
        prov = (ATHENA / 'core/rules.md').read_text(encoding='utf-8')
        rows = [l for l in prov.splitlines() if re.match(r'^\| [KR]\d+ \|', l)]
        self.assertGreaterEqual(len(rows), 20)
        for row in rows:
            with self.subTest(row=row[:20]):
                self.assertEqual(row.count('|'), 6, 'id | rule | failure | delete-when | where')
        self.assertTrue((self.out('codex') / '.codex/standards/coding.md').is_file())
        self.assertTrue((self.out('claude') / '.claude/rules/coding.md').is_file())
        self.assertTrue((self.out('pi') / 'config/rules/coding.md').is_file())
        self.assertFalse((self.out('claude') / '.claude/rules.md').exists(), 'provenance is not installed')

    def test_ac3_skills_shape(self):
        total = 0
        for platform, root in ROOTS.items():
            skills = self.out(platform) / root / 'skills'
            for name in REMOVED_SKILLS:
                self.assertFalse((skills / name).exists(), f'{platform} ships removed skill {name}')
            for skill in sorted(skills.glob('*/SKILL.md')):
                text = skill.read_text(encoding='utf-8')
                with self.subTest(skill=f'{platform}/{skill.parent.name}'):
                    self.assertLessEqual(len(text.splitlines()), 60)
                    m = re.search(r'^description:\s*(.+)$', text, re.M)
                    self.assertTrue(m)
                    if platform == 'claude':
                        total += len(m.group(1))
        self.assertLessEqual(total, 6500)
        stages = self.out('claude') / '.claude/skills/pace/references/stages.md'
        self.assertIn('由 `core/pace/stages.yaml` 生成', stages.read_text(encoding='utf-8'))

    def test_ac3_no_stale_references_in_dist(self):
        for platform in ('claude', 'codex', 'pi'):
            base = self.out(platform)
            for f in sorted(base.rglob('*')):
                rel = f.relative_to(base).as_posix()
                if not f.is_file() or f.suffix not in {'.md', '.toml', '.yaml'} or rel.startswith(('RELEASE', 'CHANGELOG', 'AI-MIGRATION', 'README', 'GENERATED')) \
                        or '/core/gate/' in f'/{rel}' or rel.startswith(('templates/', 'plugin/core/gate/')):
                    continue
                with self.subTest(file=f'{platform}/{rel}'):
                    hit = STALE.search(f.read_text(encoding='utf-8'))
                    self.assertIsNone(hit, hit and hit.group(0))

    def test_ac3_skill_links_resolve(self):
        """Markdown links and bare references/…md / ../skill/…md paths resolve in every dist."""
        for platform, skills in (('claude', '.claude/skills'), ('codex', '.codex/skills'), ('pi', 'plugin/skills')):
            base = self.out(platform) / skills
            for f in sorted(base.rglob('*.md')):
                text = f.read_text(encoding='utf-8')
                links = set(re.findall(r'\]\((?!https?:)([^)#\s]+\.md)', text))
                if f.name == 'SKILL.md':
                    links |= set(re.findall(r'(?<![\w/~.])((?:references|\.\./[\w-]+(?:/references)?)/[\w.-]+\.md)', text))
                for link in sorted(links):
                    with self.subTest(platform=platform, file=f.relative_to(base).as_posix(), link=link):
                        self.assertTrue((f.parent / link).resolve().is_file())

    def test_build_rejects_bad_maps(self):
        import json, shutil
        cases = {
            'dir key to file target': ('cx', 'rename', {'rules/': 'standards'}, 'both end with'),
            'key matches nothing': ('cc', 'rename', {'nope/': 'x/'}, 'matches no core file'),
            'core_map with core true': ('cc', 'core_map', {'rules/': 'r/'}, 'core_map is for platforms'),
            'escaping target': ('pi', 'core_map', {'rules/': '../x/'}, 'invalid core_map entry'),
        }
        for label, (platform, key, table, message) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / 'athena'
                shutil.copytree(ATHENA, src, ignore=shutil.ignore_patterns('evals', '__pycache__'))
                cfg = src / 'adapters' / platform / 'platform.json'
                data = json.loads(cfg.read_text(encoding='utf-8'))
                data[key] = table
                cfg.write_text(json.dumps(data), encoding='utf-8')
                run = build(Path(tmp) / 'dist', src)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn(message, run.stderr)

    def test_rename_collision_with_adapter_file_fails(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'athena'
            shutil.copytree(ATHENA, src, ignore=shutil.ignore_patterns('evals', '__pycache__'))
            (src / 'adapters/cc/package/CLAUDE.md').write_text('clash\n', encoding='utf-8')
            run = build(Path(tmp) / 'dist', src)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('CLAUDE.md', run.stderr)

    def test_ac4_agents(self):
        cc = sorted(p.stem for p in (self.out('claude') / '.claude/agents').glob('*.md'))
        cx = sorted(p.stem for p in (self.out('codex') / '.codex/agents').glob('*.toml'))
        pi = sorted(p.stem for p in (self.out('pi') / 'plugin/prompts').glob('*.md'))
        self.assertEqual(cc, ['architect', 'generator', 'polish-worker', 'reviewer'])
        self.assertEqual(cx, ['architect', 'generator', 'polish_worker', 'reviewer'])
        self.assertEqual(pi, ['architect', 'generator', 'polish-worker', 'reviewer'])
        for name in cc:
            head = (self.out('claude') / '.claude/agents' / f'{name}.md').read_text(encoding='utf-8').split('---')[1]
            with self.subTest(agent=name):
                self.assertIn('omitClaudeMd: true', head)
                self.assertNotRegex(head, r'(?m)^model:(?![ \t]*inherit\b)')
        execution = (self.out('claude') / '.claude/skills/pace/references/execution.md').read_text(encoding='utf-8')
        self.assertIn('不带 `model:`', execution)
        self.assertIn('commit 署名按你会话的 attribution 规则', execution)

    def test_ac5_consolidation_lines(self):
        skills = self.out('claude') / '.claude/skills'
        read = lambda rel: (skills / rel).read_text(encoding='utf-8')
        grok = read('grok-exec/SKILL.md')
        for needle in ('grok models', '402', '最后一个顶层 JSON 对象', 'cherry-pick', 'tdd-evidence' if False else '不在仓库任何位置写证据'):
            self.assertIn(needle, grok)
        deps = read('deps-check/SKILL.md')
        for needle in ('全组件清单', '标来源', '私有或未文档化契约', '一个主版本'):
            self.assertIn(needle, deps)
        vm = read('athena-vm/SKILL.md')
        self.assertIn('apt 源优先级', vm)
        self.assertIn('镜像变量', vm)
        shell = (self.out('claude') / '.claude/rules/shell.md').read_text(encoding='utf-8')
        for needle in ('bat', 'timeout', '`!` 前缀'):
            self.assertIn(needle, shell)
        self.assertIn('order_note', (ATHENA / 'core/pace/stages.yaml').read_text(encoding='utf-8'))
        self.assertIn('- AC1:', read('pace/SKILL.md') + (ATHENA / 'core/package/skills/pace/references').joinpath('gates.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
