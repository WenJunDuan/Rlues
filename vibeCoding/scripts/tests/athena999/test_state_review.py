"""Behavioral 9.9.9 state/review regressions; run with unittest discovery."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
REPO = Path(__file__).resolve().parents[4]
CX = ROOT / 'codex/9.9.9/.codex/hooks'
CC = ROOT / 'claude/9.9.9/.claude/hooks'
PI = ROOT / 'pi-agent/plugin/extensions/cc-core'
GUARD_PATHS = (
    'vibeCoding/claude/9.9.9/.claude/hooks/pre-bash-guard.cjs',
    'vibeCoding/codex/9.9.9/.codex/hooks/pre-bash-guard.py',
    'vibeCoding/pi-agent/plugin/extensions/cc-core/pre-bash-guard.cjs',
)
POLICY_MATRIX = (
    ('npm test', True, None),
    ('npm run lint && npm test', True, None),
    ('npm test && echo ok', True, None),
    ('set -o pipefail; npm test 2>&1 | tail -8', True, None),
    ('set -o pipefail; set -e; npm test | tail -8', True, None),
    ('set -euo pipefail; npm test | tee test.log', True, None),
    ("go test -run 'A|B' ./...", True, None),
    ('pytest -k "a|b"', True, None),
    ('npm test | tail -8', False, 'pipeline_without_pipefail'),
    ('set -o pipefail; set +o pipefail; npm test | tail -8', False, 'pipeline_without_pipefail'),
    ('npm test || true', False, 'validation_status_not_reported'),
    ('npm test; echo done', False, 'validation_status_not_reported'),
    ('npm test | tail -8 || echo done', False, 'validation_status_not_reported'),
    ('npm test &', False, 'validation_backgrounded'),
)
POLICY_EXTRAS = (
    ('npm test &> out.log', True, None),
    ('npm test &>> out.log', True, None),
    ('set -o pipefail; npm test |& tee test.log', True, None),
    ('npm test |& tee test.log', False, 'pipeline_without_pipefail'),
    ('npm test\necho done', False, 'validation_status_not_reported'),
)


def py_module(name):
    sys.path.insert(0, str(CX))
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), CX / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def invoke(platform, operation, index):
    if platform == 'cx':
        code = ('import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                'import _index_io as io; from _index_bounds import enforce_index_bounds; '
                'p=Path(sys.argv[2]); ' + operation[0])
        args = [sys.executable, '-c', code, str(CX), str(index)]
    else:
        code = ('const p=process.argv[2],io=require(process.argv[1]+"/_index-io.cjs"),'
                'bounds=require(process.argv[1]+"/_index-bounds.cjs");' + operation[1])
        args = ['node', '-e', code, str(CC), str(index)]
    return subprocess.run(args, text=True, capture_output=True)


def invoke_bounds_with_payload(platform, index, payload, sync_dir):
    if platform == 'cx':
        code = ('import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                'import _index_io as io; from _index_bounds import enforce_index_bounds; '
                'p=Path(sys.argv[2]); sync=Path(sys.argv[3]); payload=sys.stdin.read(); '
                'deadline=time.monotonic()+2; held=sync/"cc-held"; '
                'exec("while not held.exists():\\n if time.monotonic() >= deadline: raise RuntimeError(\'CC did not acquire lock\')\\n time.sleep(0.01)"); '
                'result=io.update(p,lambda _: enforce_index_bounds(payload,p.parent)); '
                'print(result or "",end="")')
        args = [sys.executable, '-c', code, str(CX), str(index), str(sync_dir)]
    else:
        code = ('const fs=require("fs"),path=require("path"),p=process.argv[2],'
                'sync=process.argv[3],held=path.join(sync,"cc-held"),'
                'observed=path.join(sync,"contention-observed"),'
                'io=require(process.argv[1]+"/_index-io.cjs"),'
                'bounds=require(process.argv[1]+"/_index-bounds.cjs"),'
                'payload=fs.readFileSync(0,"utf8"),'
                'wait=new Int32Array(new SharedArrayBuffer(4)),'
                'prefix=path.basename(p)+".lock.",'
                'result=io.update(p,()=>{fs.writeFileSync(held,"");const deadline=Date.now()+2000;'
                'while(fs.readdirSync(path.dirname(p)).filter(name=>name.startsWith(prefix)&&name.endsWith(".json")).length<2){'
                'if(Date.now()>=deadline)throw new Error("CX lock contender did not appear");'
                'Atomics.wait(wait,0,0,10);}fs.writeFileSync(observed,"");'
                'return bounds.enforceIndexBounds(payload,path.dirname(p));});'
                'process.stdout.write(result||"");')
        args = ['node', '-e', code, str(CC), str(index), str(sync_dir)]
    return subprocess.run(args, input=payload, text=True, capture_output=True)


class StateBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ai = self.root / '.ai_state'
        self.ai.mkdir()
        self.idx = self.ai / '_index.md'
        self.base = '---\ncurrent_sprint_slug: "example"\nroute_history: []\n---\n## 当前状态\n- ready\n'
        self.idx.write_text(self.base)

    @property
    def spill(self):
        return self.ai / 'index-overflow.md'

    @property
    def sprint_spill(self):
        return self.ai / 'sprints/example/index-overflow.md'

    def assert_pointers_resolve(self, content, expected_prefix):
        pointers = re.findall(r'(\.ai_state/index-overflow\.md)#([a-z]+-\d+)', content)
        matching = [(relative, ident) for relative, ident in pointers
                    if ident.startswith(expected_prefix + '-')]
        self.assertTrue(matching, content)
        overflow = self.spill.read_text()
        for relative, ident in matching:
            self.assertIn(f'## {ident}\n', overflow)
            self.assertEqual((self.root / relative).resolve(), self.spill.resolve())
        return [ident for _, ident in matching]

    def test_lock_timeout_never_mutates(self):
        for platform in ('cx', 'cc'):
            with self.subTest(platform=platform):
                self.idx.write_text('original')
                lock = self.idx.with_name('_index.md.lock')
                lock.write_text(json.dumps({'pid': os.getpid(), 'token': 'other'}))
                result = invoke(platform, ('io.update(p,lambda _: "lost")', 'io.update(p,()=>"lost")'), self.idx)
                self.assertEqual(self.idx.read_text(), 'original', result.stderr)
                self.assertTrue(lock.exists(), 'contender must not release owner lock')
                lock.unlink()

    def test_live_old_lock_is_not_stolen(self):
        for platform in ('cx', 'cc'):
            self.idx.write_text('original')
            lock = self.idx.with_name('_index.md.lock')
            lock.write_text(json.dumps({'pid': os.getpid(), 'token': 'alive'}))
            os.utime(lock, (time.time()-30, time.time()-30))
            invoke(platform, ('io.update(p,lambda _: "lost")', 'io.update(p,()=>"lost")'), self.idx)
            self.assertEqual(self.idx.read_text(), 'original', platform)
            lock.unlink()

    def bound(self, platform):
        return invoke(platform, ('io.update(p,lambda c: enforce_index_bounds(c,p.parent))',
                                 'io.update(p,c=>bounds.enforceIndexBounds(c,require("path").dirname(p)))'), self.idx)

    def test_noop_has_no_overflow_write(self):
        for platform in ('cx', 'cc'):
            self.idx.write_text(self.base.replace('- ready', '- ' + '原文' * 100))
            first = self.bound(platform)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = self.idx.stat().st_mtime_ns
            spill_before = self.spill.stat().st_mtime_ns
            second = self.bound(platform)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(self.idx.stat().st_mtime_ns, before, platform)
            self.assertEqual(self.spill.stat().st_mtime_ns, spill_before, platform)
            self.assertFalse(self.sprint_spill.exists(), platform)

    def test_end_of_file_long_pointer_original_preserved(self):
        original = 'prefix-' + '长' * 200 + ' →index-overflow.md#prior-1'
        for platform in ('cx', 'cc'):
            self.idx.write_text(self.base.replace('- ready', '- ' + original))
            run = self.bound(platform)
            self.assertEqual(run.returncode, 0, run.stderr)
            item = self.idx.read_text().split('## 当前状态\n')[1].strip()[2:]
            self.assertLessEqual(len(item.encode()), 160, platform)
            self.assertIn(original, self.spill.read_text(), platform)
            self.assertFalse(self.sprint_spill.exists(), platform)

    def test_oversized_index_preserves_raw_body(self):
        body = '\n## Narrative\n' + '记录' * 7000
        for platform in ('cx', 'cc'):
            self.idx.write_text(self.base + body)
            run = self.bound(platform)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertLessEqual(self.idx.stat().st_size, 12*1024, platform)
            self.assertIn(body, self.spill.read_text(), platform)
            self.assertFalse(self.sprint_spill.exists(), platform)

    def test_all_spill_branches_emit_project_relative_resolvable_pointers(self):
        long_item = '原文' * 100
        cases = {
            'rh': '---\ncurrent_sprint_slug: "example"\nroute_history: [' + json.dumps(long_item) + ']\n---\n## 当前状态\n- ready\n',
            'st': self.base.replace('- ready', '- ' + long_item),
            'hi': self.base + '\n## 历史\n- ' + long_item + '\n',
            'body': self.base + '\n## Narrative\n' + '整文件' * 5000,
        }
        for platform in ('cx', 'cc'):
            for prefix, original in cases.items():
                with self.subTest(platform=platform, branch=prefix):
                    self.spill.unlink(missing_ok=True)
                    self.idx.write_text(original)
                    run = self.bound(platform)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assert_pointers_resolve(self.idx.read_text(), prefix)
                    self.assertFalse(self.sprint_spill.exists())

    def test_mixed_platform_concurrent_bounds_preserve_both_payloads(self):
        sync_dir = self.root / 'bounds-sync'
        sync_dir.mkdir()
        originals = {
            'cx': 'cx-concurrent-original-' + '甲' * 200,
            'cc': 'cc-concurrent-original-' + '乙' * 200,
        }
        payloads = {
            platform: self.base.replace('- ready', '- ' + original)
            for platform, original in originals.items()
        }
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                platform: pool.submit(
                    invoke_bounds_with_payload, platform, self.idx, payload, sync_dir
                )
                for platform, payload in payloads.items()
            }
        results = {platform: future.result() for platform, future in futures.items()}
        self.assertTrue(all(result.returncode == 0 for result in results.values()),
                        {platform: result.stderr for platform, result in results.items()})
        self.assertTrue((sync_dir / 'contention-observed').exists(),
                        'CC must observe the CX lock contender before releasing its lock')
        overflow = self.spill.read_text()
        for original in originals.values():
            self.assertIn(original, overflow)
        headings = re.findall(r'^## (st-\d+)$', overflow, re.M)
        self.assertEqual(len(headings), 2)
        self.assertEqual(len(set(headings)), 2)
        emitted = []
        for platform, result in results.items():
            emitted.extend(self.assert_pointers_resolve(result.stdout, 'st'))
        self.assertEqual(len(set(emitted)), 2)
        self.assertFalse(self.sprint_spill.exists())

    def test_mixed_platform_concurrent_updates_do_not_lose_increments(self):
        self.idx.write_text('0')
        def one(number):
            platform = 'cx' if number % 2 else 'cc'
            return invoke(platform,('io.update(p,lambda c: str(int(c)+1))','io.update(p,c=>String(Number(c)+1))'),self.idx)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(one,range(24)))
        self.assertTrue(all(r.returncode==0 for r in results),[r.stderr for r in results])
        self.assertEqual(self.idx.read_text(),'24')

    def test_crash_between_overflow_and_index_commit_recovers(self):
        original=self.base.replace('- ready','- '+'崩溃原文'*200)
        self.idx.write_text(original)
        run=invoke('cx',('io.update(p,lambda c: (enforce_index_bounds(c,p.parent),__import__("os")._exit(77))[0])',''),self.idx)
        self.assertEqual(run.returncode,77)
        self.assertEqual(self.idx.read_text(),original)
        self.assertIn('崩溃原文'*200,self.spill.read_text())
        self.assertFalse(self.sprint_spill.exists())
        run=self.bound('cc')  # Recovery can happen on the other native implementation.
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertNotEqual(self.idx.read_text(),original)

    def test_unreadable_existing_overflow_is_never_replaced(self):
        self.spill.write_text('original overflow survives')
        self.idx.write_text(self.base.replace('- ready','- '+'long'*80))
        code='const fs=require("fs"),read=fs.readFileSync;fs.readFileSync=function(p,...args){if(String(p).endsWith("index-overflow.md")){const e=new Error("injected read failure");e.code="EACCES";throw e;}return read.call(this,p,...args)};require(process.argv[1]).enforceIndexBounds(read(process.argv[2],"utf8"),process.argv[3]);'
        run=subprocess.run(['node','-e',code,str(CC/'_index-bounds.cjs'),str(self.idx),str(self.ai)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(self.spill.read_text(),'original overflow survives')

    def test_route_history_keeps_newest_head_and_spills_oldest_tail(self):
        # route_history 新在前 (主 agent 头插): 11 条 → 保前 10, 最旧的第 11 条进 spill。
        items=[f'2026-09-18 route note {i}' for i in range(11)]
        rendered=', '.join(json.dumps(i) for i in items)
        spill_path=self.spill
        for platform in ('cx','cc'):
            with self.subTest(platform=platform):
                self.idx.write_text('---\ncurrent_sprint_slug: "example"\nroute_history: ['+rendered+']\n---\n## 当前状态\n- ready\n')
                if spill_path.exists():
                    spill_path.unlink()
                run=self.bound(platform)
                self.assertEqual(run.returncode,0,run.stderr)
                match=re.search(r'^route_history:\s*\[(.*)\]\s*(?:#.*)?$',self.idx.read_text(),re.M)
                kept=json.loads('['+match.group(1)+']')
                self.assertEqual(kept,items[:10],platform)
                spill=spill_path.read_text()
                self.assertIn(items[10],spill,platform)
                self.assertNotIn(items[0],spill,platform)
                self.assertFalse(self.sprint_spill.exists(),platform)

    def test_templates_and_gitignore_use_root_overflow_contract(self):
        templates = (
            ROOT/'claude/9.9.9/.claude/skills/pace/templates/_index.md',
            ROOT/'codex/9.9.9/.codex/skills/pace/templates/_index.md',
            ROOT/'pi-agent/plugin/skills/pace/templates/_index.md',
        )
        for template in templates:
            text = template.read_text()
            self.assertIn('.ai_state/index-overflow.md', text, template)
            self.assertNotIn('sprints/{slug}/index-overflow.md', text, template)
        implementations = (
            ROOT/'claude/9.9.9/.claude/hooks/_index-bounds.cjs',
            ROOT/'codex/9.9.9/.codex/hooks/_index_bounds.py',
        )
        for implementation in implementations:
            text = implementation.read_text()
            self.assertNotRegex(text, r'readSlug|read_slug|spillPath|spill_path')
        ignored = subprocess.run(
            ['git', '-C', str(ROOT.parent), 'check-ignore', '--no-index',
             '.ai_state/index-overflow.md'],
            text=True,
            capture_output=True,
        )
        self.assertEqual(ignored.returncode, 1, ignored.stdout + ignored.stderr)
        tracked = subprocess.run(
            ['git', '-C', str(ROOT.parent), 'ls-files', '--error-unmatch',
             '.ai_state/index-overflow.md'],
            text=True,
            capture_output=True,
        )
        self.assertEqual(tracked.returncode, 0, tracked.stdout + tracked.stderr)


class IndexUpdaterNextActionBehavior(unittest.TestCase):
    """next_action 允许散文; 机器枚举仍识别; re-route 地板不覆盖散文。"""

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'.ai_state/sprints/test').mkdir(parents=True)
        self.idx=self.root/'.ai_state/_index.md'
        for i in range(5):   # Quick 上限 3, 5 个未跟踪实现文件 → 触发地板
            (self.root/f'f{i}.py').write_text('x = 1\n')

    def write_index(self,next_action):
        self.idx.write_text('---\nversion: "9.9.9"\ncurrent_sprint_slug: "test"\npath: "Quick"\n'
                            f'stage: "impl"\nnext_action: "{next_action}"\n---\n## 当前状态\n- ready\n')

    def updater(self):
        payload={'cwd':str(self.root),'tool_name':'Edit','hook_event_name':'PostToolUse',
                 'tool_input':{'file_path':str(self.root/'f0.py')}}
        run=subprocess.run(['node',str(CC/'index-updater.cjs')],input=json.dumps(payload),text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        return run

    def test_prose_next_action_is_not_warned_and_never_overwritten(self):
        prose='继续修 hook 缺陷 2, 再跑回归'
        self.write_index(prose)
        run=self.updater()
        self.assertNotIn('非枚举',run.stderr)
        self.assertIn('re-route',run.stderr)
        self.assertIn('散文',run.stderr)
        self.assertIn(f'next_action: "{prose}"',self.idx.read_text())

    def test_empty_next_action_still_gets_the_re_route_floor(self):
        self.write_index('')
        self.updater()
        self.assertIn('next_action: "re-route"',self.idx.read_text())

    def test_machine_signal_keeps_the_floor_closed(self):
        self.write_index('review')
        run=self.updater()
        self.assertNotIn('re-route',run.stderr)
        self.assertIn('next_action: "review"',self.idx.read_text())


class GateBehavior(unittest.TestCase):
    def test_done_contract_tables_are_acceptance(self):
        gate = py_module('delivery-gate')
        doc = '## Done Contract\n| ID | Observable result |\n|---|---|\n| AC1 | lock contention preserves data |\n| AC2 | stale result is rejected |\n'
        self.assertEqual(len(gate.acceptance_criteria(doc)), 2)

    def test_git_failure_is_not_empty_tree_success(self):
        gate = py_module('delivery-gate')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gate.source_diff_sha256(Path(tmp)), '')

    def test_packet_requires_design_binding_and_only_contract_ids(self):
        gate = py_module('delivery-gate')
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            design = 'Background: AC99 is retired.\n## Done Contract\n- AC1: lock contention preserves bytes\n'
            (sprint/'design.md').write_text(design)
            (sprint/'review-packet.md').write_text('## Done Contract\n- AC1: lock contention preserves bytes\n')
            with self.assertRaises(gate.GateError):
                gate.validate_review_packet(sprint)
            digest = hashlib.sha256(design.encode()).hexdigest()
            (sprint/'review-packet.md').write_text(f'---\nsource_design_sha256: "{digest}"\n---\n## Done Contract\n- AC1: lock contention preserves bytes\n')
            gate.validate_review_packet(sprint)

    def test_evidence_covers_accepts_inline_and_block_lists(self):
        document=('collected_evidence:\n'
                  '  - tool_use_id: block\n    covers:\n      - ac1\n      - "AC2"\n    result: pass\n'
                  '  - tool_use_id: inline\n    covers: [ac3, "AC4"]\n    result: pass\n'
                  '  - tool_use_id: indentless\n    covers: # valid YAML indentless sequence\n'
                  '    - ac5 # first\n    - "AC6"\n    result: pass\n')
        invalid='collected_evidence:\n  - tool_use_id: bad\n    covers: AC1\n    result: pass\n'
        gate=py_module('delivery-gate')
        with tempfile.TemporaryDirectory() as tmp:
            evidence=Path(tmp)/'evidence.yaml'
            evidence.write_text(document)
            expected=[['AC1','AC2'],['AC3','AC4'],['AC5','AC6']]
            self.assertEqual([r['covers'] for r in gate.parse_evidence_records(evidence)],expected)
            code='const m=require(process.argv[1]);process.stdout.write(JSON.stringify(m.validateEvidence(process.argv[2])));'
            run=subprocess.run(['node','-e',code,str(CC/'delivery-gate.cjs'),str(evidence)],text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual([r['covers'] for r in json.loads(run.stdout)],expected)
            evidence.write_text(invalid)
            for platform,action in (
                ('cx',lambda: gate.parse_evidence_records(evidence)),
                ('cc',lambda: subprocess.run(['node','-e',code,str(CC/'delivery-gate.cjs'),str(evidence)],text=True,capture_output=True,check=True)),
            ):
                with self.subTest(platform=platform), self.assertRaises(Exception) as caught:
                    action()
                message=str(caught.exception)
                if platform == 'cc':
                    message=caught.exception.stderr
                self.assertIn('covers: [AC1, AC2]',message)
                self.assertIn('covers:\n  - AC1\n  - AC2',message)

    def test_post_review_drift_allows_ship_bookkeeping_only(self):
        gate=py_module('delivery-gate')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            subprocess.run(['git','init','-q',str(root)],check=True)
            sprint=root/'.ai_state/sprints/test'
            sprint.mkdir(parents=True)
            design=sprint/'design.md'
            design.write_text('## Done Contract\n- AC1: ships\n')
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','reviewed'],check=True)
            commit=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,text=True,capture_output=True).stdout.strip()
            fm={key:'' for key in gate.INDEX_GOVERNANCE_FIELDS}
            fm.update(version='9.9.9',path='Feature',current_sprint_slug='test')
            manifest=sprint/'review-manifest.yaml'
            manifest.write_text('schema_version: 1\nimplementation_commit: '+commit+'\nindex_governance_sha256: '+gate.index_governance_sha256(fm)+'\nfiles:\n  design.md: "'+hashlib.sha256(design.read_bytes()).hexdigest()+'"\n')
            review=('Reviewed design sha256: '+hashlib.sha256(design.read_bytes()).hexdigest()+'\n'
                    'Reviewed implementation commit: '+commit+'\n'
                    'Reviewed state manifest sha256: '+hashlib.sha256(manifest.read_bytes()).hexdigest()+'\n')
            allowed=(sprint/'tdd-evidence.yaml',sprint/'evidence.yaml',root/'.ai_state/vm-pending.md',
                     sprint/'runs/result.log',root/'.ai_state/docs/note.md',root/'.ai_state/compound/learning.md')
            for path in allowed:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('bookkeeping\n')
            gate.validate_review_binding(review,sprint/'reviews/implementation-review.md',sprint,root/'.ai_state',root,fm)
            code='const m=require(process.argv[1]);m.validateReviewBinding(process.argv[2],"review",process.argv[3],process.argv[4],process.argv[5],JSON.parse(process.argv[6]));'
            args=['node','-e',code,str(CC/'delivery-gate.cjs'),review,str(sprint),str(root/'.ai_state'),str(root),json.dumps(fm)]
            run=subprocess.run(args,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            unexpected=root/'.ai_state/unreviewed.md'
            unexpected.write_text('must block\n')
            with self.assertRaisesRegex(gate.GateError,'unreviewed .ai_state drift'):
                gate.validate_review_binding(review,sprint/'reviews/implementation-review.md',sprint,root/'.ai_state',root,fm)
            run=subprocess.run(args,text=True,capture_output=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('unreviewed .ai_state drift',run.stderr)

    def test_ship_closes_vm_pending_promises_in_current_sprint(self):
        gate=py_module('delivery-gate')
        promises={
            'design.md':'后续记 vm-pending',
            'runtime-verify.md':'后续记 `vm-pending`',
            'cleanup-pass.md':'失败 → vm-pending',
            'fix-note.md':'需要登 vm-pending',
            'session-log.md':'稍后转 vm-pending',
        }
        for filename,promise in promises.items():
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                ai=Path(tmp)/'.ai_state'
                sprint=ai/'sprints/q12-test'
                sprint.mkdir(parents=True)
                (sprint/filename).write_text(promise+'\n')
                docs=ai/'docs'
                docs.mkdir()
                (docs/'ignored.md').write_text('记 vm-pending\n')
                with self.assertRaisesRegex(gate.GateError,rf'found in {re.escape(filename)}.*q12-test'):
                    gate.validate_vm_pending_promises(ai,sprint,'q12-test')
                code='const m=require(process.argv[1]);m.validateVmPendingPromises(process.argv[2],process.argv[3],process.argv[4]);'
                args=['node','-e',code,str(CC/'delivery-gate.cjs'),str(ai),str(sprint),'q12-test']
                run=subprocess.run(args,text=True,capture_output=True)
                self.assertNotEqual(run.returncode,0)
                self.assertIn('unlock: add a .ai_state/vm-pending.md row',run.stderr)
                (ai/'vm-pending.md').write_text('| q12-test | pending |\n')
                gate.validate_vm_pending_promises(ai,sprint,'q12-test')
                run=subprocess.run(args,text=True,capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)


class InputBindingBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.sprint = self.root / '.ai_state/sprints/test'
        self.sprint.mkdir(parents=True)
        (self.root/'.ai_state/_index.md').write_text('---\nversion: "9.9.9"\ncurrent_sprint_slug: "test"\n---\n')
        (self.sprint/'design.md').write_text('## Done Contract\n- AC1: returns exact bytes\n')
        (self.root/'app.py').write_text('print(1)\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'app.py'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base'], check=True)

    def review_command(self, platform, action, *args):
        directory, suffix, runner = (CX,'.py',sys.executable) if platform == 'cx' else (CC,'.cjs','node')
        cli=directory.parent/'skills/pace/scripts'/('review-binding'+suffix)
        return subprocess.run([runner,str(cli),action,'--cwd',str(self.root),*args],text=True,capture_output=True)

    def seed_review_packet(self):
        design=(self.sprint/'design.md').read_bytes()
        (self.sprint/'review-packet.md').write_text('---\nsource_design_sha256: "'+hashlib.sha256(design).hexdigest()+'"\n---\n## Done Contract\n- AC1: returns exact bytes\n')
        (self.sprint/'evidence.yaml').write_text('collected_evidence: []\n')

    def prepare_review(self, platform, target):
        self.seed_review_packet()
        run=self.review_command(platform,'prepare')
        self.assertEqual(run.returncode,0,run.stderr)
        prepared=json.loads(run.stdout)
        dispatch=self.sprint/'dispatch.json'
        dispatch.write_text(json.dumps({'task_name':target}))
        run=self.review_command(platform,'bind','--run',prepared['review_run_id'],'--receipt',str(dispatch))
        self.assertEqual(run.returncode,0,run.stderr)
        return prepared

    def accept_pass(self, platform, run_id, target):
        receipt=self.sprint/'result.json'
        receipt.write_text(json.dumps({'task_name':target,'status':'completed','output':'VERDICT: PASS\n'}))
        run=self.review_command(platform,'accept','--run',run_id,'--receipt',str(receipt))
        self.assertEqual(run.returncode,0,run.stderr)
        return json.loads(run.stdout)

    def validate_current_review(self, platform):
        review=self.sprint/'reviews/implementation-review.md'
        if platform=='cx':
            py_module('_review_binding').validate_current(self.root,self.sprint,review)
            return
        code='require(process.argv[1]).validateCurrent(process.argv[2],process.argv[3],process.argv[4]);'
        run=subprocess.run(['node','-e',code,str(CC/'_review-binding.cjs'),str(self.root),str(self.sprint),str(review)],text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)

    def test_review_rejects_conflicting_native_frontmatter_without_scanning_body(self):
        for platform in ('cx','cc'):
            receipt=self.sprint/'result.json'
            for key in ('mode','review_run_id','packet_sha256','input_manifest_sha256','reviewed_packet_sha256','reviewed_diff_sha256'):
                target='/root/metadata-'+platform+'-'+key
                prepared=self.prepare_review(platform,target)
                with self.subTest(platform=platform,key=key):
                    bad='design' if key=='mode' else 'wrong-run' if key=='review_run_id' else '0'*64
                    output='---\n'+key+': '+json.dumps(bad)+'\nverdict: PASS\n---\nVERDICT: PASS\n'
                    receipt.write_text(json.dumps({'agents':[{'agent_name':target,'agent_status':{'completed':output}}]}))
                    run=self.review_command(platform,'accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
                    self.assertEqual(run.returncode,2,run.stdout)
                    self.assertIn('native review metadata',run.stderr)
                run=self.review_command(platform,'supersede','--run',prepared['review_run_id'])
                self.assertEqual(run.returncode,0,run.stderr)
            # A quoted example in the body is not a declaration by this review.
            target='/root/metadata-'+platform+'-valid'
            prepared=self.prepare_review(platform,target)
            expected={key:prepared[key] for key in ('mode','review_run_id','packet_sha256','input_manifest_sha256')}
            expected.update(reviewed_packet_sha256=prepared['packet_sha256'],reviewed_diff_sha256=py_module('delivery-gate').source_diff_sha256(self.root))
            output='---\n'+''.join(k+': '+json.dumps(v)+'\n' for k,v in expected.items())+'verdict: PASS\n---\n## Rejected example\n\n```yaml\nmode: design\nreview_run_id: wrong-run\nreviewed_packet_sha256: wrong-packet\n```\n\nVERDICT: PASS\n'
            receipt.write_text(json.dumps({'agents':[{'agent_name':target,'agent_status':{'completed':output}}]}))
            run=self.review_command(platform,'accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
            self.assertEqual(run.returncode,0,run.stderr)
            py_module('delivery-gate').validate_review(self.sprint/'reviews/implementation-review.md',self.root,self.sprint)

    def test_final_validation_rechecks_legacy_native_metadata(self):
        target='/root/legacy-accepted'
        prepared=self.prepare_review('cx',target)
        receipt=self.sprint/'result.json'
        receipt.write_text(json.dumps({'task_name':target,'status':'completed','output':'VERDICT: PASS\n'}))
        run=self.review_command('cx','accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
        self.assertEqual(run.returncode,0,run.stderr)
        accepted=json.loads(run.stdout)
        # Model an old accepted artifact whose hashes are internally consistent,
        # but whose original native declaration contradicts its dispatch.
        native=self.sprint/accepted['native_output_ref']
        raw=json.loads(native.read_text())
        raw['output']='---\nmode: design\nverdict: PASS\n---\nVERDICT: PASS\n'
        native.write_text(json.dumps(raw))
        log=self.sprint/'session-log.md'
        log.write_text(log.read_text().replace(accepted['native_output_sha256'],hashlib.sha256(native.read_bytes()).hexdigest()))
        gate=py_module('delivery-gate')
        with self.assertRaisesRegex(gate.GateError,'native review metadata'):
            gate.validate_review(self.sprint/'reviews/implementation-review.md',self.root,self.sprint)
        code='require(process.argv[1]).validateReview(process.argv[2],process.argv[3],process.argv[4]);'
        run=subprocess.run(['node','-e',code,str(CC/'delivery-gate.cjs'),str(self.sprint/'reviews/implementation-review.md'),str(self.root),str(self.sprint)],text=True,capture_output=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('native review metadata',run.stderr)

    def test_accept_deduplicates_reviewed_binding_lines(self):
        labels=('Reviewed design sha256:','Reviewed implementation commit:','Reviewed state manifest sha256:')
        for platform in ('cx','cc'):
            (self.sprint/'review-manifest.yaml').write_text('schema_version: 1\n')
            target='/root/deduplicate-'+platform
            prepared=self.prepare_review(platform,target)
            output='VERDICT: PASS\n\n'+''.join(label+' stale-value\n' for label in labels)
            receipt=self.sprint/'result.json'
            receipt.write_text(json.dumps({'task_name':target,'status':'completed','output':output}))
            run=self.review_command(platform,'accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
            self.assertEqual(run.returncode,0,run.stderr)
            formal=(self.sprint/'reviews/implementation-review.md').read_text()
            for label in labels:
                self.assertEqual(formal.count(label),1,platform+': '+label)
            self.assertNotIn('stale-value',formal,platform)

    def test_native_metadata_distinguishes_indented_root_from_nested_fields(self):
        for platform in ('cx','cc'):
            target='/root/indented-'+platform
            prepared=self.prepare_review(platform,target)
            receipt=self.sprint/'result.json'
            receipt.write_text(json.dumps({'task_name':target,'status':'completed','output':'---\n  mode: design\n  verdict: PASS\n---\nVERDICT: PASS\n'}))
            with self.subTest(platform=platform):
                run=self.review_command(platform,'accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
                self.assertEqual(run.returncode,2,run.stdout)
                self.assertIn('native review metadata',run.stderr)
            self.review_command(platform,'supersede','--run',prepared['review_run_id'])
            target='/root/nested-'+platform
            prepared=self.prepare_review(platform,target)
            output='---\nmode: implementation\ndimensions:\n  mode: design\nverdict: CONCERNS\n---\nVERDICT: CONCERNS\n'
            receipt.write_text(json.dumps({'task_name':target,'status':'completed','output':output}))
            run=self.review_command(platform,'accept','--run',prepared['review_run_id'],'--receipt',str(receipt))
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['event'],'received')

    def test_gradle_maven_and_supported_validation_commands_pair_pre_post(self):
        commands=('./gradlew test','./gradlew build','mvn compile','mvn verify','prettier --check .','cmake --build build','npm run lint','python3 -m unittest','go vet ./...','cargo clippy')
        for platform,directory,suffix,runner in [('cx',CX,'.py',sys.executable),('cc',CC,'.cjs','node')]:
            for number,command in enumerate(commands):
                with self.subTest(platform=platform,command=command):
                    ident=platform+'-paired-'+str(number)
                    payload={'cwd':str(self.root),'tool_use_id':ident,'tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':command}}
                    run=subprocess.run([runner,str(directory/('pre-bash-guard'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
                    self.assertEqual(run.returncode,0,run.stderr)
                    payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0,'stdout':'validated'})
                    run=subprocess.run([runner,str(directory/('evidence-collector'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
                    self.assertEqual(run.returncode,0,run.stderr)
                    evidence=self.sprint/'evidence.yaml'
                    records=py_module('delivery-gate').parse_evidence_records(evidence) if evidence.exists() else []
                    matching=[r for r in records if r['tool_use_id']==ident]
                    self.assertEqual(len(matching),1,platform+': '+command)
                    self.assertEqual(matching[0]['binding_status'],'current',platform+': '+command)

    def test_evidence_output_keeps_test_summary_tail_after_redaction(self):
        for platform,directory,suffix,runner in [('cx',CX,'.py',sys.executable),('cc',CC,'.cjs','node')]:
            ident=platform+'-long-output'
            payload={'cwd':str(self.root),'tool_use_id':ident,'tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':'npm test'}}
            run=subprocess.run([runner,str(directory/('pre-bash-guard'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            summary='\nTests: 42 passed, 42 total\n'
            payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0,'stdout':'token=fixture-secret '+('x'*1700)+summary})
            run=subprocess.run([runner,str(directory/('evidence-collector'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            record=[r for r in py_module('delivery-gate').parse_evidence_records(self.sprint/'evidence.yaml') if r['tool_use_id']==ident][0]
            artifact=(self.sprint/record['output_artifact']).read_text()
            self.assertIn('Tests: 42 passed, 42 total',artifact,platform)
            self.assertIn('…[truncated ',artifact,platform)
            self.assertIn('token=[REDACTED]',artifact,platform)
            self.assertNotIn('fixture-secret',artifact,platform)
            unicode_id=platform+'-unicode-output'
            payload={'cwd':str(self.root),'tool_use_id':unicode_id,'tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':'npm test'}}
            run=subprocess.run([runner,str(directory/('pre-bash-guard'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0,'stdout':'😀'*1000})
            run=subprocess.run([runner,str(directory/('evidence-collector'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            record=[r for r in py_module('delivery-gate').parse_evidence_records(self.sprint/'evidence.yaml') if r['tool_use_id']==unicode_id][0]
            artifact=(self.sprint/record['output_artifact']).read_text()
            self.assertEqual(artifact.count('😀'),1000,platform)
            self.assertNotIn('…[truncated ',artifact,platform)

    def test_binding_ignores_log_writes_but_rejects_code_contract_environment_drift(self):
        binding = py_module('_input_binding')
        original = binding.snapshot(self.root, self.sprint)
        (self.sprint/'evidence.yaml').write_text('log appended')
        (self.sprint/'session-log.md').write_text('review dispatched')
        self.assertEqual(binding.snapshot(self.root, self.sprint), original)
        (self.root/'app.py').write_text('print(2)\n')
        self.assertNotEqual(binding.snapshot(self.root, self.sprint)['source_sha256'], original['source_sha256'])
        (self.sprint/'design.md').write_text('## Done Contract\n- AC2: changed contract\n')
        self.assertNotEqual(binding.snapshot(self.root, self.sprint)['design_sha256'], original['design_sha256'])
        (self.root/'.ai_state/runtime-env.yaml').write_text('image: app:2\npassword: private-value\n')
        changed = binding.snapshot(self.root, self.sprint)
        self.assertNotEqual(changed['environment_sha256'], original['environment_sha256'])
        (self.root/'.ai_state/runtime-env.yaml').write_text('image: app:2\npassword: changed-secret\n')
        self.assertEqual(binding.snapshot(self.root, self.sprint), changed)

    def test_post_without_pre_is_unverifiable(self):
        binding = py_module('_input_binding')
        payload = {'cwd': str(self.root), 'tool_use_id': 'run-one', 'tool_input': {'command': 'pytest'}}
        self.assertEqual(binding.finish(payload, 'passed')['binding_status'], 'unverifiable')
        binding.capture_before(payload)
        self.assertEqual(binding.finish(payload, 'passed')['binding_status'], 'current')
        binding.capture_before(payload)
        (self.root/'app.py').write_text('print(3)\n')
        self.assertEqual(binding.finish(payload, 'passed')['binding_status'], 'unverifiable')

    def test_native_implementations_have_same_binding(self):
        original = py_module('_input_binding').snapshot(self.root,self.sprint)
        code = 'const m=require(process.argv[1]);process.stdout.write(JSON.stringify(m.snapshot(process.argv[2],process.argv[3])));'
        run = subprocess.run(['node','-e',code,str(CC/'_input-binding.cjs'),str(self.root),str(self.sprint)],text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout),original)

    def test_review_late_wrong_unknown_and_changed_inputs_rejected(self):
        binding = py_module('_review_binding')
        design = (self.sprint/'design.md').read_bytes()
        (self.sprint/'review-packet.md').write_text('---\nsource_design_sha256: "'+hashlib.sha256(design).hexdigest()+'"\n---\n## Done Contract\n- AC1: returns exact bytes\n')
        (self.sprint/'evidence.yaml').write_text('collected_evidence: []\n')
        prepared = binding.prepare(self.root,'implementation',[])
        run = prepared['review_run_id']
        dispatch = self.sprint/'dispatch.json'
        dispatch.write_text(json.dumps({'agent_id':'native-one'}))
        binding.bind(self.root,run,dispatch)
        result = self.sprint/'result.json'
        result.write_text(json.dumps({'agent_id':'native-two','status':'completed','output':'VERDICT: PASS\n'}))
        with self.assertRaises(ValueError): binding.accept(self.root,run,result)
        result.write_text(json.dumps({'agent_id':'native-one','status':'running','output':'VERDICT: PASS\n'}))
        with self.assertRaises(ValueError): binding.accept(self.root,run,result)
        result.write_text(json.dumps({'agent_id':'native-one','status':'completed','output':'VERDICT: PASS\n'}))
        with self.assertRaises(ValueError): binding.accept(self.root,'old-run',result)
        (self.root/'app.py').write_text('print(3)\n')
        with self.assertRaises(ValueError): binding.accept(self.root,run,result)
        (self.root/'app.py').write_text('print(1)\n')
        binding.accept(self.root,run,result)
        binding.validate_current(self.root,self.sprint,self.sprint/'reviews/implementation-review.md')
        with self.assertRaises(ValueError): binding.accept(self.root,run,result)
        (self.sprint/'review-packet.md').write_text('changed packet')
        with self.assertRaises(ValueError): binding.validate_current(self.root,self.sprint,self.sprint/'reviews/implementation-review.md')

    def test_both_real_hook_chains_collect_current_evidence_and_gate_rejects_drift(self):
        for platform,directory,suffix,runner in [('cx',CX,'.py',sys.executable),('cc',CC,'.cjs','node')]:
            payload={'cwd':str(self.root),'tool_use_id':platform+'-validation','tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':'pytest'}}
            run=subprocess.run([runner,str(directory/('pre-bash-guard'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0,'stdout':'one passing assertion'})
            run=subprocess.run([runner,str(directory/('evidence-collector'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
        records=py_module('delivery-gate').validate_evidence(self.sprint/'evidence.yaml')
        self.assertEqual(len(records),2)
        code='const m=require(process.argv[1]);m.validateEvidence(process.argv[2]);'
        run=subprocess.run(['node','-e',code,str(CC/'delivery-gate.cjs'),str(self.sprint/'evidence.yaml')],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        (self.root/'app.py').write_text('print("changed")\n')
        gate=py_module('delivery-gate')
        with self.assertRaises(gate.GateError):
            gate.validate_evidence(self.sprint/'evidence.yaml')
        run=subprocess.run(['node','-e',code,str(CC/'delivery-gate.cjs'),str(self.sprint/'evidence.yaml')],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)

    def test_desktop_receipts_negative_results_and_both_native_clis(self):
        design=(self.sprint/'design.md').read_bytes()
        (self.sprint/'review-packet.md').write_text('---\nsource_design_sha256: "'+hashlib.sha256(design).hexdigest()+'"\n---\n## Done Contract\n- AC1: returns exact bytes\n')
        (self.sprint/'evidence.yaml').write_text('collected_evidence: []\n')
        for platform,directory,suffix,runner in [('cx',CX,'.py',sys.executable),('cc',CC,'.cjs','node')]:
            cli=directory.parent/'skills/pace/scripts'/('review-binding'+suffix)
            def command(action,*args,ok=True):
                run=subprocess.run([runner,str(cli),action,'--cwd',str(self.root),*args],text=True,capture_output=True)
                self.assertEqual(run.returncode,0 if ok else 2,run.stderr)
                return json.loads(run.stdout) if ok else None
            for verdict in ('CONCERNS','PASS'):
                prepared=command('prepare'); ident=prepared['review_run_id']
                target='/root/actual-'+platform+'-'+verdict.lower()
                dispatch=self.sprint/'dispatch.json';dispatch.write_text(json.dumps({'task_name':target,'nickname':'Not an identity'}))
                command('bind','--run',ident,'--receipt',str(dispatch))
                result=self.sprint/'result.json';result.write_text(json.dumps({'agents':[{'agent_name':'/root/unrelated','agent_status':{'completed':'VERDICT: PASS\n'}},{'agent_name':target,'agent_status':{'completed':'VERDICT: '+verdict+'\n'}}]}))
                row=command('accept','--run',ident,'--receipt',str(result))
                self.assertEqual(row['event'],'accepted' if verdict=='PASS' else 'received')
                gate=py_module('delivery-gate')
                if verdict=='PASS': gate.validate_review(self.sprint/'reviews/implementation-review.md',self.root,self.sprint)
                else:
                    with self.assertRaises(gate.GateError): gate.validate_review(self.sprint/'reviews/implementation-review.md',self.root,self.sprint)
                command('accept','--run',ident,'--receipt',str(result),ok=False)

    def test_prepare_excludes_cli_written_paths_from_stored_inputs(self):
        self.seed_review_packet()
        (self.root/'notes.md').write_text('bound note\n')
        written=(
            '.ai_state/sprints/test/session-log.md',
            './.ai_state/sprints/test/session-log.md',
            '.ai_state/sprints/test/reviews/implementation-review.md',
            './.ai_state/_index.md',
            '.ai_state/_index.md',
        )
        for platform in ('cx','cc'):
            with self.subTest(platform=platform):
                args=['--input','notes.md']
                for path in written:
                    args+=['--input',path]
                run=self.review_command(platform,'prepare',*args)
                self.assertEqual(run.returncode,0,run.stderr)
                prepared=json.loads(run.stdout)
                self.assertEqual(prepared['input_paths'],['notes.md'])
                for path in written:
                    self.assertIn(path,prepared['excluded_inputs'])
                self.assertNotIn('notes.md',prepared['excluded_inputs'])
                self.assertEqual(prepared['input_hashes']['notes.md'],hashlib.sha256(b'bound note\n').hexdigest())
                for axis in ('source_sha256','design_sha256','environment_sha256'):
                    self.assertIn(axis,prepared['input_hashes'])
                target='/root/exclude-'+platform
                dispatch=self.sprint/'dispatch.json'
                dispatch.write_text(json.dumps({'task_name':target}))
                run=self.review_command(platform,'bind','--run',prepared['review_run_id'],'--receipt',str(dispatch))
                self.assertEqual(run.returncode,0,run.stderr)
                self.accept_pass(platform,prepared['review_run_id'],target)
                self.validate_current_review(platform)

    def test_prepare_fails_when_exclusion_empties_declared_inputs(self):
        self.seed_review_packet()
        for platform in ('cx','cc'):
            with self.subTest(platform=platform):
                run=self.review_command(platform,'prepare','--input','.ai_state/_index.md',
                    '--input','.ai_state/sprints/test/session-log.md',
                    '--input','.ai_state/sprints/test/reviews/implementation-review.md')
                self.assertEqual(run.returncode,2,run.stdout)
                self.assertIn('empty after excluding',run.stderr)
                run=self.review_command(platform,'prepare')
                self.assertEqual(run.returncode,0,run.stderr)
                prepared=json.loads(run.stdout)
                self.assertEqual(prepared['input_paths'],[])
                self.assertEqual(self.review_command(platform,'supersede','--run',prepared['review_run_id']).returncode,0)

    def run_hook_chain(self, platform, ident, command, *, success=True, stdout='validated'):
        directory, suffix, runner = (CX,'.py',sys.executable) if platform == 'cx' else (CC,'.cjs','node')
        payload={'cwd':str(self.root),'tool_use_id':ident,'tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':command}}
        run=subprocess.run([runner,str(directory/('pre-bash-guard'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        if platform == 'cc':
            if success:
                payload.update(hook_event_name='PostToolUse',tool_response={'stdout':stdout,'stderr':'','interrupted':False})
            else:
                payload.update(hook_event_name='PostToolUseFailure',tool_response={'stdout':stdout,'stderr':'failed','interrupted':False})
        else:
            payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0 if success else 1,'stdout':stdout})
        run=subprocess.run([runner,str(directory/('evidence-collector'+suffix))],input=json.dumps(payload),text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        return payload

    def evidence_record(self, ident):
        evidence=self.sprint/'evidence.yaml'
        records=py_module('delivery-gate').parse_evidence_records(evidence)
        matching=[r for r in records if r['tool_use_id']==ident]
        self.assertEqual(len(matching),1,ident)
        return matching[0], evidence.read_text()

    def test_ac1_pipefail_pipelines_record_pass_and_fail_through_real_chain(self):
        commands=(
            'set -o pipefail; npm test 2>&1 | tail -8',
            'set -euo pipefail; npm test | tee test.log',
        )
        for platform in ('cx','cc'):
            for index,command in enumerate(commands):
                with self.subTest(platform=platform,command=command,outcome='pass'):
                    ident=f'{platform}-ac1-pass-{index}'
                    self.run_hook_chain(platform,ident,command,success=True,stdout='Tests: 1 passed')
                    record, raw=self.evidence_record(ident)
                    self.assertEqual(record['result'],'pass',raw)
                    self.assertEqual(record['binding_status'],'current',raw)
                    self.assertNotIn('result_reason:', raw.split(ident,1)[-1].split('\n  - ',1)[0])
                    if platform=='cx':
                        self.assertIn('\n    kind: "test"\n', raw.split(ident,1)[-1].split('\n  - ',1)[0])
                with self.subTest(platform=platform,command=command,outcome='fail'):
                    ident=f'{platform}-ac1-fail-{index}'
                    self.run_hook_chain(platform,ident,command,success=False,stdout='Tests: 1 failed')
                    record, raw=self.evidence_record(ident)
                    self.assertEqual(record['result'],'fail',raw)
                    self.assertNotIn('result_reason:', raw.split(ident,1)[-1].split('\n  - ',1)[0])

    def test_ac2_masked_validation_records_unknown_reason_and_keeps_fail(self):
        masked=(
            ('npm test | tail -8','pipeline_without_pipefail'),
            ('npm test || true','validation_status_not_reported'),
            ('npm test; echo done','validation_status_not_reported'),
            ('npm test &','validation_backgrounded'),
            ('npm test | tail -8 || echo done','validation_status_not_reported'),
        )
        for platform in ('cx','cc'):
            for index,(command,reason) in enumerate(masked):
                with self.subTest(platform=platform,command=command,outcome='success'):
                    ident=f'{platform}-ac2-unknown-{index}'
                    self.run_hook_chain(platform,ident,command,success=True)
                    record, raw=self.evidence_record(ident)
                    block=raw.split(ident,1)[-1].split('\n  - ',1)[0]
                    self.assertEqual(record['result'],'unknown',block)
                    self.assertIn(f'result_reason: "{reason}"', block)
                    self.assertEqual(record['binding_status'],'current',block)
                with self.subTest(platform=platform,command=command,outcome='fail'):
                    ident=f'{platform}-ac2-fail-{index}'
                    self.run_hook_chain(platform,ident,command,success=False)
                    record, raw=self.evidence_record(ident)
                    block=raw.split(ident,1)[-1].split('\n  - ',1)[0]
                    self.assertEqual(record['result'],'fail',block)
                    self.assertNotIn('result_reason:', block)

    def test_ac2_masking_survives_the_persisted_command_bound(self):
        """A masked pipeline past the 500-char persisted bound must still downgrade.

        CC used to truncate to 500 before classifying, which cut a trailing
        `| tail -8` off long commands and recorded them as `pass` while CX (which
        decides on 4000 chars) recorded `unknown` — fail-open plus CC/CX divergence
        on the exact axis this slice closes.
        """
        command='npm test '+'-x '*180+'| tail -8'
        self.assertGreater(len(command),500,'fixture must cross the persisted bound')
        for platform in ('cx','cc'):
            with self.subTest(platform=platform):
                ident=f'{platform}-ac2-longbound'
                self.run_hook_chain(platform,ident,command,success=True)
                record, raw=self.evidence_record(ident)
                block=raw.split(ident,1)[-1].split('\n  - ',1)[0]
                self.assertEqual(record['result'],'unknown',block)
                self.assertIn('result_reason: "pipeline_without_pipefail"',block)
                # the persisted copy stays bounded on both platforms
                self.assertLessEqual(len(record['command']),500,block)

    def test_ac4_cc_shaped_response_and_redaction_tail(self):
        ident='cc-ac4-long'
        summary='\nTests: 42 passed, 42 total\n'
        self.run_hook_chain('cc',ident,'npm test',success=True,stdout='token=fixture-secret '+('x'*1700)+summary)
        record, raw=self.evidence_record(ident)
        self.assertEqual(record['result'],'pass',raw)
        artifact=(self.sprint/record['output_artifact']).read_text()
        self.assertIn('Tests: 42 passed, 42 total',artifact)
        self.assertIn('…[truncated ',artifact)
        self.assertIn('token=[REDACTED]',artifact)
        self.assertNotIn('fixture-secret',artifact)
        fail_id='cc-ac4-fail'
        self.run_hook_chain('cc',fail_id,'npm test',success=False,stdout='boom')
        fail_record, fail_raw=self.evidence_record(fail_id)
        self.assertEqual(fail_record['result'],'fail',fail_raw)
        collector=(CC/'evidence-collector.cjs').read_text()
        self.assertEqual(collector.count('function redact('),1)
        self.assertEqual(len(list(CC.glob('evidence-collector*'))),1)
        self.assertEqual(len(list(CX.glob('evidence-collector*'))),1)


class EvidencePipelineIntegrity(unittest.TestCase):
    def cc_policy(self, command):
        code=('const m=require(process.argv[1]);'
              'process.stdout.write(JSON.stringify(m.validationStatusPolicy(process.argv[2])));')
        return subprocess.run(['node','-e',code,str(CC/'_input-binding.cjs'),command],text=True,capture_output=True)

    def cx_policy(self, command):
        return py_module('_input_binding').validation_status_policy(command)

    def assert_policy(self, command, provable, reason):
        cx=self.cx_policy(command)
        self.assertEqual(bool(cx['provable']),provable,command)
        self.assertEqual(cx.get('reason'),reason,command)
        run=self.cc_policy(command)
        self.assertEqual(run.returncode,0,run.stderr)
        cc=json.loads(run.stdout)
        self.assertEqual(bool(cc['provable']),provable,command)
        self.assertEqual(cc.get('reason'),reason,command)
        self.assertEqual(cc.get('reason'),cx.get('reason'),command)

    def test_ac3_policy_matrix_identical_on_cc_and_cx(self):
        for command,provable,reason in POLICY_MATRIX + POLICY_EXTRAS:
            with self.subTest(command=command):
                self.assert_policy(command,provable,reason)
        long_command='set -o pipefail; '+('true && '*20)+'npm test 2>&1 | tail -8'
        self.assertGreater(len(long_command),120)
        self.assertLess(len(long_command),500)
        self.assert_policy(long_command,True,None)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            subprocess.run(['git','init','-q',str(root)],check=True)
            sprint=root/'.ai_state/sprints/test'
            sprint.mkdir(parents=True)
            (root/'.ai_state/_index.md').write_text('---\nversion: "9.9.9"\ncurrent_sprint_slug: "test"\n---\n')
            (sprint/'design.md').write_text('## Done Contract\n- AC1: returns exact bytes\n')
            (root/'app.py').write_text('print(1)\n')
            subprocess.run(['git','-C',str(root),'add','app.py'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','base'],check=True)
            ident='cx-ac3-bound'
            payload={'cwd':str(root),'tool_use_id':ident,'tool_name':'Bash','hook_event_name':'PreToolUse','tool_input':{'command':long_command}}
            run=subprocess.run([sys.executable,str(CX/'pre-bash-guard.py')],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            payload.update(hook_event_name='PostToolUse',tool_response={'exit_code':0,'stdout':'ok'})
            run=subprocess.run([sys.executable,str(CX/'evidence-collector.py')],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            raw=(sprint/'evidence.yaml').read_text()
            self.assertIn('| tail -8',raw)
            match=re.search(r'command: ("(?:\\.|[^"\\])*")', raw)
            self.assertIsNotNone(match,raw)
            persisted=json.loads(match.group(1))
            self.assertLessEqual(len(persisted),500)
            self.assertGreater(len(persisted),120)

    def test_ac5_guards_unchanged_pi_parity_and_gate_blocks_without_shell_lex(self):
        diff=subprocess.run(['git','diff','--exit-code','52ff57eb','--',*GUARD_PATHS],cwd=REPO,text=True,capture_output=True)
        self.assertEqual(diff.returncode,0,diff.stdout+diff.stderr)
        for name in ('_shell-lex.cjs','_input-binding.cjs','pre-bash-guard.cjs'):
            self.assertEqual((CC/name).read_bytes(),(PI/name).read_bytes(),name)
        evidence_body='collected_evidence:\n  - tool_use_id: x\n    result: unknown\n'
        with tempfile.TemporaryDirectory() as tmp:
            evidence=Path(tmp)/'evidence.yaml'
            evidence.write_text(evidence_body)
            # Drop the lexer from a copy of each hook tree, never from the package itself:
            # an interrupted run must not leave the shipped hooks without _shell-lex.
            cc_dir,cx_dir=Path(tmp)/'cc',Path(tmp)/'cx'
            shutil.copytree(CC,cc_dir,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(CX,cx_dir,ignore=shutil.ignore_patterns('__pycache__'))
            (cc_dir/'_shell-lex.cjs').unlink()
            (cx_dir/'_shell_lex.py').unlink()
            cx_code=('import sys,importlib.util\nfrom pathlib import Path\n'
                     'sys.path.insert(0, str(Path(sys.argv[1]).parent))\n'
                     'spec=importlib.util.spec_from_file_location("delivery_gate", sys.argv[1])\n'
                     'mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n'
                     'try:\n'
                     '    mod.validate_evidence(Path(sys.argv[2]))\n'
                     '    sys.exit(0)\n'
                     'except mod.GateError as exc:\n'
                     '    sys.stderr.write(str(exc))\n'
                     '    sys.exit(2)\n')
            cx=subprocess.run([sys.executable,'-c',cx_code,str(cx_dir/'delivery-gate.py'),str(evidence)],text=True,capture_output=True)
            self.assertEqual(cx.returncode,2,cx.stdout+cx.stderr)
            self.assertIn('insufficient',cx.stderr)
            self.assertIn('unknown',cx.stderr.lower())
            cc_code=('try{require(process.argv[1]).validateEvidence(process.argv[2]);process.exit(0)}'
                     'catch(e){process.stderr.write(String(e.message||e));process.exit(2)}')
            cc=subprocess.run(['node','-e',cc_code,str(cc_dir/'delivery-gate.cjs'),str(evidence)],text=True,capture_output=True)
            self.assertEqual(cc.returncode,2,cc.stdout+cc.stderr)
            self.assertIn('insufficient',cc.stderr)
            self.assertIn('unknown',cc.stderr.lower())

    def test_ac6_gate_contracts_document_admissible_evidence(self):
        paths=(
            CC.parent/'skills/pace/references/gate-contracts.md',
            CX.parent/'skills/pace/references/gate-contracts.md',
            ROOT/'pi-agent/plugin/skills/pace/references/gate-contracts.md',
        )
        required=(
            'set -o pipefail; npm test 2>&1 | tail -8',
            'unprotected pipeline',
            'not admissible evidence',
        )
        for path in paths:
            text=path.read_text()
            for needle in required:
                with self.subTest(path=str(path),needle=needle):
                    self.assertIn(needle,text)
            self.assertTrue(re.search(r'masked validation|backgrounded', text), path)


if __name__ == '__main__':
    unittest.main()
