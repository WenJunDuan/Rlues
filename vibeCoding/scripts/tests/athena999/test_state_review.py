"""Behavioral 9.9.9 state/review regressions; run with unittest discovery."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
import concurrent.futures
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CX = ROOT / 'codex/9.9.9/.codex/hooks'
CC = ROOT / 'claude/9.9.9/.claude/hooks'


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


class StateBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ai = Path(self.tmp.name) / '.ai_state'
        self.ai.mkdir()
        self.idx = self.ai / '_index.md'
        self.base = '---\ncurrent_sprint_slug: "example"\nroute_history: []\n---\n## 当前状态\n- ready\n'
        self.idx.write_text(self.base)

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
            self.idx.write_text(self.base)
            self.bound(platform)  # first normalization is allowed
            before = self.idx.stat().st_mtime_ns
            spill = self.ai / 'sprints/example/index-overflow.md'
            spill_before = spill.stat().st_mtime_ns if spill.exists() else None
            self.bound(platform)
            self.assertEqual(self.idx.stat().st_mtime_ns, before, platform)
            self.assertEqual(spill.stat().st_mtime_ns if spill.exists() else None, spill_before, platform)

    def test_end_of_file_long_pointer_original_preserved(self):
        original = 'prefix-' + '长' * 200 + ' →index-overflow.md#prior-1'
        for platform in ('cx', 'cc'):
            self.idx.write_text(self.base.replace('- ready', '- ' + original))
            run = self.bound(platform)
            self.assertEqual(run.returncode, 0, run.stderr)
            item = self.idx.read_text().split('## 当前状态\n')[1].strip()[2:]
            self.assertLessEqual(len(item.encode()), 160, platform)
            spill = self.ai / 'sprints/example/index-overflow.md'
            self.assertIn(original, spill.read_text(), platform)

    def test_oversized_index_preserves_raw_body(self):
        body = '\n## Narrative\n' + '记录' * 7000
        for platform in ('cx', 'cc'):
            self.idx.write_text(self.base + body)
            run = self.bound(platform)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertLessEqual(self.idx.stat().st_size, 12*1024, platform)
            self.assertIn(body, (self.ai / 'sprints/example/index-overflow.md').read_text(), platform)

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
        spill=self.ai/'sprints/example/index-overflow.md'
        self.assertIn('崩溃原文'*200,spill.read_text())
        run=self.bound('cc')  # Recovery can happen on the other native implementation.
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertNotEqual(self.idx.read_text(),original)

    def test_unreadable_existing_overflow_is_never_replaced(self):
        spill=self.ai/'sprints/example/index-overflow.md'
        spill.parent.mkdir(parents=True)
        spill.write_text('original overflow survives')
        self.idx.write_text(self.base.replace('- ready','- '+'long'*80))
        code='const fs=require("fs"),read=fs.readFileSync;fs.readFileSync=function(p,...args){if(String(p).endsWith("index-overflow.md")){const e=new Error("injected read failure");e.code="EACCES";throw e;}return read.call(this,p,...args)};require(process.argv[1]).enforceIndexBounds(read(process.argv[2],"utf8"),process.argv[3]);'
        run=subprocess.run(['node','-e',code,str(CC/'_index-bounds.cjs'),str(self.idx),str(self.ai)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(spill.read_text(),'original overflow survives')

    def test_route_history_keeps_newest_head_and_spills_oldest_tail(self):
        # route_history 新在前 (主 agent 头插): 11 条 → 保前 10, 最旧的第 11 条进 spill。
        items=[f'2026-09-18 route note {i}' for i in range(11)]
        rendered=', '.join(json.dumps(i) for i in items)
        spill_path=self.ai/'sprints/example/index-overflow.md'
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

    def prepare_review(self, platform, target):
        design=(self.sprint/'design.md').read_bytes()
        (self.sprint/'review-packet.md').write_text('---\nsource_design_sha256: "'+hashlib.sha256(design).hexdigest()+'"\n---\n## Done Contract\n- AC1: returns exact bytes\n')
        (self.sprint/'evidence.yaml').write_text('collected_evidence: []\n')
        run=self.review_command(platform,'prepare')
        self.assertEqual(run.returncode,0,run.stderr)
        prepared=json.loads(run.stdout)
        dispatch=self.sprint/'dispatch.json'
        dispatch.write_text(json.dumps({'task_name':target}))
        run=self.review_command(platform,'bind','--run',prepared['review_run_id'],'--receipt',str(dispatch))
        self.assertEqual(run.returncode,0,run.stderr)
        return prepared

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


if __name__ == '__main__':
    unittest.main()
