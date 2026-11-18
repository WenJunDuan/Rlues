"""athena-10-1 S5 prompts-v2: constitution, rules, skills, agents (design §9)."""
import re
from pathlib import Path
import tempfile
import unittest

from test_build import ATHENA, RELEASE, build

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
        return self.dist / platform / RELEASE

    def constitutions(self):
        return {'claude': self.out('claude') / '.claude/CLAUDE.md', 'codex': self.out('codex') / '.codex/AGENTS.md',
                'pi': self.out('pi') / 'plugin/core/IRON.md'}

    def test_ac1_one_constitution_three_platforms(self):
        texts = {p: f.read_text(encoding='utf-8') for p, f in self.constitutions().items()}
        normal = {p: re.sub(r'\S*/(?:rules|standards)/', '<RULES>/', re.sub(r'\S*/pace/references/', '<SKILLS>/pace/references/', t))
                  for p, t in texts.items()}
        self.assertEqual(len(set(normal.values())), 1, 'three constitutions differ beyond SKILLS_DIR')
        for p, t in texts.items():
            with self.subTest(platform=p):
                self.assertLessEqual(len(t.encode()), 2500)
                self.assertNotIn('INTJ', t)
                self.assertNotIn('/goal', t)
                self.assertIsNone(re.search(r'\*\*[^*]*[A-Z]{4,}', t), 'no all-caps emphasis')
                self.assertIn('review 窗口内还有并行写者', t)   # NV-C2
                self.assertIn('转述别人的结论写出处', t)       # NV-C16
                self.assertIn('收尾前看最后一段', t)           # K3 (10.1.5): named early-stop shapes
                self.assertIn('不悄悄缩小、扩大或替换', t)     # K12 (10.1.5)
                self.assertIn('直接执行不用问', t)             # K13 (10.1.5)
                self.assertRegex(t, r'规范：.*(?:rules|standards)/.*_index\.md')  # pd-1 AC4: index pointer on every platform

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
                    self.assertLessEqual(len(skill.read_bytes()), 5000)
                    self.assertEqual(re.search(r'^name:\s*(.+)$', text, re.M).group(1), skill.parent.name)
                    m = re.search(r'^description:\s*(.+)$', text, re.M)
                    self.assertTrue(m)
                    if platform == 'claude':
                        total += len(m.group(1))
        self.assertLessEqual(total, 4500)
        stages = self.out('claude') / '.claude/skills/pace/references/stages.md'
        self.assertIn('由 `core/pace/stages.yaml` 生成', stages.read_text(encoding='utf-8'))

    def test_all_skill_entrypoints_budget(self):
        # Include adapters, project packs, Pi and plugin shells, not only CC/CX.
        roots = [ATHENA / 'core/package', ATHENA / 'adapters', *self.dist.glob('*/*')]
        for root in roots:
            total = 0
            for skill in sorted(root.rglob('SKILL.md')):
                text = skill.read_text(encoding='utf-8')
                with self.subTest(root=str(root), skill=str(skill)):
                    self.assertLessEqual(len(skill.read_bytes()), 5000)
                    self.assertLessEqual(len(text.splitlines()), 60)
                    name = re.search(r'^name:\s*(.+)$', text, re.M)
                    self.assertIsNotNone(name)
                    self.assertEqual(name.group(1), skill.parent.name)
                    description = re.search(r'^description:\s*(.+)$', text, re.M)
                    self.assertIsNotNone(description)
                    total += len(description.group(1))
            self.assertLessEqual(total, 4500, str(root))

    def test_product_pack_scope_and_links(self):
        products = {'ui-consistency', 'quantum-codegen', 'quantum-data', 'biz-delivery-loop'}
        for platform, root, global_dir in (
            ('claude', '.claude', '.claude/skills'), ('codex', '.codex', '.codex/skills'),
            ('pi', '', 'plugin/skills'), ('claude-plugin', '', 'skills'), ('codex-plugin', '', 'skills')):
            base = self.out(platform)
            global_skills = base / global_dir
            self.assertTrue(products.isdisjoint(p.name for p in global_skills.iterdir()))
            index = ''.join(p.parent.name + ': ' + re.search(r'^description: (.*)$', p.read_text(), re.M).group(1) + '\n'
                            for p in global_skills.glob('*/SKILL.md'))
            self.assertLessEqual(len(index.encode()), 3500)
            pack = base / root / 'project-packs/quantum/skills'
            self.assertEqual({p.name for p in pack.iterdir()}, products)
            for f in pack.rglob('*.md'):
                for link in re.findall(r'\]\((?!https?:)([^)#\s]+\.md)', f.read_text()):
                    self.assertTrue((f.parent / link).is_file(), f'{f}: {link}')
            self.assertIn('../quantum-codegen/SKILL.md', (pack / 'biz-delivery-loop/SKILL.md').read_text())

    def test_ac3_no_stale_references_in_dist(self):
        for platform in ('claude', 'codex', 'pi'):
            base = self.out(platform)
            for f in sorted(base.rglob('*')):
                rel = f.relative_to(base).as_posix()
                if not f.is_file() or f.suffix not in {'.md', '.toml', '.yaml'} or rel.startswith(('RELEASE', 'CHANGELOG', 'AI-MIGRATION', 'INSTALL', 'MIGRATION', 'README', 'GENERATED')) \
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
            'exclude matches nothing': ('cc', 'exclude', ['rules/nope.md'], 'exclude rules/nope.md matches no core file'),
            'exclude on core_map platform': ('pi', 'exclude', ['rules/_index.md'], 'exclude is for platforms'),
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
                if name == 'architect':
                    self.assertNotIn('skills:', head)
                if name == 'polish-worker':
                    self.assertIn('skills: [polish]', head)
                self.assertNotIn('architect-doc', head)
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

    def test_pd1_resident_rules_budget(self):
        """CC loads rules without a `paths` header every session: keep them ≤5200 B; no session-workflow, no _index."""
        rules = self.out('claude') / '.claude/rules'
        resident = [f for f in sorted(rules.glob('*.md')) if not f.read_text(encoding='utf-8').startswith('---\npaths:')]
        self.assertLessEqual(sum(f.stat().st_size for f in resident), 5200, [f.name for f in resident])
        self.assertFalse((rules / 'session-workflow.md').exists())
        self.assertFalse((rules / '_index.md').exists(), 'CC loads rules by paths; the index is for Codex / Pi')
        self.assertIn('严重度', (rules / 'coding.md').read_text(encoding='utf-8'))
        for index in (self.out('codex') / '.codex/standards/_index.md', self.out('pi') / 'config/rules/_index.md'):
            with self.subTest(index=index.parts[-3]):
                text = index.read_text(encoding='utf-8')
                self.assertNotIn('session-workflow', text)
                self.assertIn('athena-session', text)
        for p, f in self.constitutions().items():
            with self.subTest(platform=p):
                self.assertIn('athena-session', f.read_text(encoding='utf-8'))

    def test_pd1_session_skill_shape(self):
        refs = ('open', 'writers', 'verify', 'merge-review', 'close', 'collab')
        for platform, skills in (('claude', '.claude/skills'), ('codex', '.codex/skills'), ('pi', 'plugin/skills'),
                                 ('claude-plugin', 'skills'), ('codex-plugin', 'skills')):
            skill = self.out(platform) / skills / 'athena-session'
            with self.subTest(platform=platform):
                text = (skill / 'SKILL.md').read_text(encoding='utf-8')
                self.assertLessEqual(len(text.encode()), 5000)
                self.assertLessEqual(len(text.splitlines()), 60)
                self.assertRegex(text, r'(?m)^name: athena-session$')
                self.assertLessEqual(len(re.search(r'(?m)^description:\s*(.+)$', text).group(1)), 200)
                self.assertIn('开工', text)
                for name in refs:
                    self.assertIn(f'(references/{name}.md)', text)
                    self.assertTrue((skill / 'references' / f'{name}.md').is_file())
        refs_text = {n: (self.out('claude') / '.claude/skills/athena-session/references' / f'{n}.md').read_text(encoding='utf-8') for n in refs}
        # Hard constraints the gate reasons point at must survive the move verbatim.
        self.assertIn('packet 发出后到 accept 前，主树不提交任何东西', refs_text['merge-review'])
        self.assertIn('证据命令必须是单条 `athena run --covers ACn -- <cmd>`', refs_text['verify'])
        self.assertIn('同时 ≤3 个写者', refs_text['writers'])
        self.assertIn('先用表格和用户核对 5 类', refs_text['open'])

    def test_playbooks_match_state_v2(self):
        skills = ATHENA / 'core/package/project-packs/quantum/skills'
        module = (skills / 'quantum-codegen/references/module-playbook.md').read_text(encoding='utf-8')
        page = (skills / 'quantum-codegen/references/page-playbook.md').read_text(encoding='utf-8')
        for playbook in sorted(skills.rglob('*.md')):
            with self.subTest(playbook=playbook.relative_to(skills).as_posix()):
                self.assertNotIn('runtime-verify.md', playbook.read_text(encoding='utf-8'))
        self.assertNotIn('aether/pace', module)
        self.assertNotIn('由 一次独立 review', page)


if __name__ == '__main__':
    unittest.main()

class PromptsV3(unittest.TestCase):
    """athena-10-1-5 S5: wording the 2026-09 model guides advise against stays out of every prompt."""

    BANNED = re.compile(r'think carefully|think step by step|仔细思考|逐步思考|深呼吸|写出(你的)?(完整)?推理|展示(你的)?思考过程', re.I)

    def test_no_reasoning_extraction_or_think_harder(self):
        roots = [ATHENA / 'core/package', ATHENA / 'adapters']
        for root in roots:
            for f in sorted(root.rglob('*')):
                if f.is_file() and f.suffix in ('.md', '.toml'):
                    with self.subTest(file=str(f.relative_to(ATHENA))):
                        self.assertIsNone(self.BANNED.search(f.read_text(encoding='utf-8')))

    def test_codex_default_model_and_no_effort_pin_in_packages(self):
        cx = (ATHENA / 'adapters/cx/package/config.toml').read_text(encoding='utf-8')
        self.assertRegex(cx, r'(?m)^model = "gpt-6\.2-sol"$')
        self.assertIsNone(re.search(r'^model_reasoning_effort\s*=|^plan_mode_reasoning_effort\s*=', cx, re.M))
        cc = (ATHENA / 'adapters/cc/package/settings.json').read_text(encoding='utf-8')
        self.assertNotIn('effortLevel', cc)

    def test_yellow_zone_defaults_to_direct(self):
        self.assertIn('主 agent 直做', (ATHENA / 'core/pace/stages.yaml').read_text(encoding='utf-8'))
        self.assertIn('主 agent 直做', (ATHENA / 'core/package/skills/pace/references/execution.md').read_text(encoding='utf-8'))

