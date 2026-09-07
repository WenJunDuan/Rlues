"""One review request/receipt binding, persisted in the existing session log.

CLI receipts must be saved verbatim from native tool results. This is a local
workflow guardrail, not cryptographic attestation by the model provider.
"""
from __future__ import annotations
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
import uuid
from pathlib import Path
from _input_binding import canonical, context, digest, git, snapshot
from _index_io import acquire, release, update, write_atomic

NATIVE_BINDINGS = {
    'review_run_id':'review_run_id', 'mode':'mode', 'base_commit':'base_commit',
    'packet_sha256':'packet_sha256', 'reviewed_packet_sha256':'packet_sha256',
    'input_manifest_sha256':'input_manifest_sha256', 'reviewed_diff_sha256':'reviewed_diff_sha256',
}

def delivery_gate():
    spec = importlib.util.spec_from_file_location('athena_delivery_gate',Path(__file__).with_name('delivery-gate.py'))
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    return gate

def validate_native_metadata(output: str, prepared: dict, root: Path) -> None:
    """Absent metadata may be enveloped; contradictory native claims may not.

    Only the opening YAML frontmatter is authoritative, never quoted examples,
    fenced snippets or references in the review body.
    """
    lines = output.lstrip('\ufeff\r\n').splitlines()
    if not lines or lines[0].strip() != '---':
        return
    end = next((i for i in range(1,len(lines)) if lines[i].strip() == '---'),None)
    if end is None:
        raise ValueError('native review metadata frontmatter is not closed')
    seen = set()
    mappings = [m for line in lines[1:end] if (m := re.match(r'^([ \t]*)([A-Za-z0-9_.-]+)[ \t]*:[ \t]*(.*)$',line))]
    root_indent = min((len(m.group(1)) for m in mappings),default=0)
    for match in mappings:
        if len(match.group(1)) != root_indent or match.group(2) not in NATIVE_BINDINGS:
            continue
        key,raw = match.group(2),match.group(3).strip()
        if key in seen:
            raise ValueError('native review metadata duplicate field: '+key)
        seen.add(key)
        if raw.startswith('"'):
            value,used = json.JSONDecoder().raw_decode(raw)
            if raw[used:].strip() and not raw[used:].lstrip().startswith('#'):
                raise ValueError('native review metadata invalid scalar: '+key)
        elif raw.startswith("'"):
            quoted = re.fullmatch(r"'((?:''|[^'])*)'[ \t]*(?:#.*)?",raw)
            if not quoted:
                raise ValueError('native review metadata invalid scalar: '+key)
            value = quoted.group(1).replace("''", "'")
        else:
            value = raw.split(' #',1)[0].strip()
            if not value or value.startswith('#') or value.lower() == 'null' or value == '~':
                continue
        if value == '':
            continue
        expected = prepared.get(NATIVE_BINDINGS[key])
        if key == 'reviewed_diff_sha256':
            expected = delivery_gate().source_diff_sha256(root) if prepared['mode'] == 'implementation' else None
        if not isinstance(value,str) or not expected or value != expected:
            raise ValueError('native review metadata mismatch: '+key)

def events(sprint: Path) -> list[dict]:
    log = sprint/'session-log.md'
    if not log.exists():
        return []
    return [json.loads(m) for m in re.findall(r'^<!-- athena-review:(.*?) -->$', log.read_text(), re.M)]

def append(sprint: Path, row: dict) -> dict:
    log = sprint/'session-log.md'
    if not acquire(log):
        raise ValueError('session log lock unavailable; retry before native dispatch')
    try:
        prior = log.read_text() if log.exists() else '# Session log\n'
        write_atomic(log, prior + '\n<!-- athena-review:' + canonical({**row,'recorded_at':dt.datetime.now(dt.UTC).isoformat()}) + ' -->\n')
    finally:
        release(log)
    return row

def current(sprint: Path, run: str | None = None) -> dict:
    prepared = [r for r in events(sprint) if r.get('event') == 'prepared']
    if not prepared or (run is not None and prepared[-1]['review_run_id'] != run) or any(r.get('event') == 'superseded' and r.get('review_run_id') == prepared[-1]['review_run_id'] for r in events(sprint)):
        raise ValueError('unknown or superseded review run')
    return prepared[-1]

def file_refs(root: Path, names: list[str]) -> dict:
    result = {}
    for name in names:
        file = (root/name).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():
            raise ValueError('review input missing/outside worktree: '+name)
        result[name] = digest(file.read_bytes())
    return result

def evidence_ids(sprint: Path) -> list[str]:
    file = sprint/'evidence.yaml'
    if not file.is_file():
        return []
    found = re.findall(r'(?m)^\s*-\s+tool_use_id\s*:\s*([^#\n]*)', file.read_text())
    ids = []
    for raw in found:
        ident = raw.strip().strip('"\'')
        if ident and ident not in {'[]', 'null', '~'}:
            ids.append(ident)
    return sorted(set(ids))

def live_input(root: Path, sprint: Path, prepared: dict) -> dict:
    mode = prepared['mode']
    inputs = file_refs(root, prepared.get('input_paths', []))
    if mode == 'implementation':
        inputs.update(snapshot(root,sprint))
    else:
        inputs['design_sha256'] = digest((sprint/'design.md').read_bytes())
    return {'base_commit':git(root,'rev-parse','HEAD').decode().strip(),
            'packet_sha256':digest((sprint/'review-packet.md').read_bytes()),
            'input_manifest_sha256':digest(canonical(inputs)),
            'evidence_ids':evidence_ids(sprint),
            'evidence_docs':file_refs(root,list(prepared.get('evidence_docs',{})))}

def assert_live(root: Path, sprint: Path, prepared: dict) -> None:
    live = live_input(root,sprint,prepared)
    # base_commit is recorded, not compared: ship bookkeeping commits must not void a review.
    for field in ('packet_sha256','input_manifest_sha256'):
        if live[field] != prepared[field]:
            raise ValueError('review input changed: '+field)
    if live['evidence_docs'] != prepared.get('evidence_docs', {}):
        raise ValueError('review input changed: evidence_docs')
    prepared_ids = prepared.get('evidence_ids') or []
    live_ids = set(live['evidence_ids'])
    if any(ident not in live_ids for ident in prepared_ids):
        raise ValueError('review input changed: evidence_ids')

def explicit_verdict(output: str) -> str:
    lines = output.lstrip('\ufeff\r\n').splitlines()
    if lines and lines[0].strip() == '---':
        end = next((i for i in range(1,len(lines)) if lines[i].strip() == '---'), None)
        if end:
            for line in lines[1:end]:
                match = re.match(r'^verdict\s*:\s*["\']?(PASS|REWORK|FAIL|CONCERNS)\b', line, re.I)
                if match:
                    return match.group(1).upper()
    verdicts = list(dict.fromkeys(re.findall(r'(?:^|[\s>])(?:VERDICT|verdict)\s*:\s*["\']?(PASS|REWORK|FAIL|CONCERNS)\b', output, re.M)))
    if not verdicts:
        raise ValueError('native result has no explicit verdict')
    if len(verdicts) != 1:
        raise ValueError('native result has conflicting verdicts')
    return verdicts[0]

def prepare(cwd: Path, mode: str, inputs: list[str]) -> dict:
    root,sprint = context(cwd)
    if mode not in {'design','implementation'}:
        raise ValueError('mode must be design or implementation')
    rows = events(sprint)
    if rows:
        latest = [r for r in rows if r.get('event') == 'prepared']
        if latest and not any(r.get('review_run_id') == latest[-1]['review_run_id'] and r.get('event') in {'accepted','received','superseded'} for r in rows):
            raise ValueError('review already pending; recover its receipt or explicitly supersede')
    delivery_gate().validate_review_packet(sprint)
    docs = []
    if mode == 'implementation':
        if not (sprint/'evidence.yaml').is_file():
            raise ValueError('implementation review requires evidence.yaml')
        docs = [(sprint/name).relative_to(root).as_posix() for name in ('runtime-verify.md','cleanup-pass.md','review-manifest.yaml') if (sprint/name).is_file()]
    row = {'event':'prepared','schema_version':1,'review_run_id':str(uuid.uuid4()),'mode':mode,
           'author_target':os.environ.get('CODEX_THREAD_ID') or os.environ.get('CLAUDE_SESSION_ID') or '',
           'input_paths':sorted(set(inputs)), 'evidence_docs':dict.fromkeys(docs,'')}
    row.update(live_input(root,sprint,row))
    return append(sprint,row)

def native_receipt(file: Path, expected_target: str = '') -> tuple[str, str, str]:
    obj = json.loads(file.read_text())
    if not isinstance(obj,dict):
        raise ValueError('native receipt must be an object')
    if isinstance(obj.get('structuredContent'),dict):
        obj = obj['structuredContent']
    if isinstance(obj.get('agents'),list):
        matches = [a for a in obj['agents'] if a.get('agent_name') == expected_target]
        if len(matches) != 1:
            raise ValueError('native agent listing lacks exactly one bound target')
        item = matches[0]
        status = item.get('agent_status')
        if isinstance(status,dict) and isinstance(status.get('completed'),str):
            return item['agent_name'],'completed',status['completed']
        return item['agent_name'],'unknown',''
    target = next((obj.get(k) for k in ('agent_id','agentId','threadId','thread_id','task_name') if isinstance(obj.get(k),str) and obj[k]),'')
    status = obj.get('status','')
    output = obj.get('output') or obj.get('result') or ''
    if isinstance(status,dict) and len(status) == 1:
        target, item = next(iter(status.items()))
        if isinstance(item,dict) and isinstance(item.get('completed'),str):
            output, status = item['completed'],'completed'
    if not output and isinstance(obj.get('content'),list):
        output = '\n'.join(c.get('text','') for c in obj['content'] if c.get('type') == 'text')
    if not target:
        raise ValueError('native receipt has no actual target ID')
    return target, status, output if isinstance(output,str) else ''

def persist_receipt(sprint: Path, run: str, kind: str, receipt: Path) -> tuple[str,str]:
    target = sprint/'reviews/_native'/(run+'-'+kind+'.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    raw = receipt.read_text()
    write_atomic(target,raw)
    return target.relative_to(sprint).as_posix(),digest(raw)

def bind(cwd: Path, run: str, receipt: Path) -> dict:
    root,sprint = context(cwd); prepared = current(sprint,run)
    assert_live(root,sprint,prepared)
    target,_,_ = native_receipt(receipt)
    if target == prepared.get('author_target'):
        raise ValueError('reviewer target is the author session')
    if any(r.get('event') == 'bound' and (r.get('reviewer_target') == target or r.get('review_run_id') == run) for r in events(sprint)):
        raise ValueError('target/run already bound; a fresh independent request is required')
    ref,sha = persist_receipt(sprint,run,'dispatch',receipt)
    row = append(sprint,{'event':'bound','review_run_id':run,'reviewer_target':target,'dispatch_receipt_ref':ref,'dispatch_receipt_sha256':sha})
    update(root/'.ai_state/_index.md',lambda text: re.sub(r'^next_action:.*$','next_action: "await-review-result"',text,flags=re.M))
    return row

def accepted(sprint: Path, run: str) -> list[dict]:
    return [r for r in events(sprint) if r.get('review_run_id') == run and r.get('event') == 'accepted']

def accept(cwd: Path, run: str, receipt: Path) -> dict:
    root,sprint = context(cwd); prepared = current(sprint,run)
    if any(r.get('review_run_id') == run and r.get('event') in {'accepted','received'} for r in events(sprint)):
        raise ValueError('review result already accepted')
    bound = [r for r in events(sprint) if r.get('event') == 'bound' and r.get('review_run_id') == run]
    if len(bound) != 1:
        raise ValueError('review requires exactly one persisted native dispatch binding')
    target,status,output = native_receipt(receipt,bound[0]['reviewer_target'])
    if target != bound[0]['reviewer_target'] or status not in {'completed','complete','succeeded'} or not output.strip():
        raise ValueError('wrong target, unknown/incomplete native result, or missing output')
    assert_live(root,sprint,prepared)
    validate_native_metadata(output,prepared,root)
    verdict = explicit_verdict(output)
    ref,sha = persist_receipt(sprint,run,'result',receipt)
    doc = sprint/'reviews'/(prepared['mode']+'-review.md')
    fm = {'schema_version':1,'mode':prepared['mode'],'review_run_id':run,'reviewer_target':target,'packet_sha256':prepared['packet_sha256'],
          'input_manifest_sha256':prepared['input_manifest_sha256'],'native_output_ref':ref,'verdict':verdict}
    header = '---\n' + ''.join(k+': '+json.dumps(v)+'\n' for k,v in fm.items()) + '---\n\n'
    if prepared['mode'] == 'implementation' and (sprint/'review-manifest.yaml').is_file():
        header += 'Reviewed design sha256: '+digest((sprint/'design.md').read_bytes())+'\nReviewed implementation commit: '+prepared['base_commit']+'\nReviewed state manifest sha256: '+digest((sprint/'review-manifest.yaml').read_bytes())+'\n\n'
    write_atomic(doc,header+'## Native review output\n\n'+output)
    row = append(sprint,{'event':'accepted' if verdict == 'PASS' else 'received','verdict':verdict,'review_run_id':run,'reviewer_target':target,'native_output_ref':ref,'native_output_sha256':sha,
                        'output_ref':doc.relative_to(sprint).as_posix(),'output_sha256':digest(doc.read_bytes())})
    def _after_accept(text: str) -> str:
        text = re.sub(r'^next_action:.*$','next_action: "'+('' if verdict == 'PASS' else 'rework_impl')+'"',text,flags=re.M)
        if verdict == 'PASS':
            text = re.sub(r'^design_changed_after_impl:.*$','design_changed_after_impl: false',text,count=1,flags=re.M)
        return text
    update(root/'.ai_state/_index.md', _after_accept)
    return row

def validate_current(root: Path, sprint: Path, review: Path) -> None:
    prepared = current(sprint)
    if prepared['mode'] != 'implementation':
        raise ValueError('latest request did not review implementation')
    assert_live(root,sprint,prepared)
    rows = accepted(sprint,prepared['review_run_id'])
    if len(rows) != 1:
        raise ValueError('missing or duplicate accepted native review')
    row = rows[0]
    if (sprint/row['output_ref']).resolve() != review.resolve() or digest(review.read_bytes()) != row['output_sha256']:
        raise ValueError('accepted review output changed/missing')
    bound = [r for r in events(sprint) if r.get('event') == 'bound' and r.get('review_run_id') == prepared['review_run_id']]
    if len(bound) != 1:
        raise ValueError('missing native dispatch binding')
    for ref,sha in ((bound[0]['dispatch_receipt_ref'],bound[0]['dispatch_receipt_sha256']),(row['native_output_ref'],row['native_output_sha256'])):
        if digest((sprint/ref).read_bytes()) != sha:
            raise ValueError('native receipt changed/missing')
    target,status,output = native_receipt(sprint/row['native_output_ref'],bound[0]['reviewer_target'])
    if target != bound[0]['reviewer_target'] or target != row['reviewer_target'] or status not in {'completed','complete','succeeded'}:
        raise ValueError('native result identity/status mismatch')
    validate_native_metadata(output,prepared,root)

def main() -> int:
    parser = argparse.ArgumentParser(description='Prepare, bind and accept one native review using real saved tool-result JSON. Completed negative verdicts are retained for rework; only PASS is deliverable. No model or platform dispatch is invented.')
    parser.add_argument('action',choices=['prepare','bind','accept','supersede'])
    parser.add_argument('--cwd',type=Path,default=Path.cwd(),help='Actual Git worktree; current sprint comes from _index.md')
    parser.add_argument('--mode',choices=['design','implementation'],default='implementation')
    parser.add_argument('--input',action='append',default=[],help='Additional reviewed document relative to worktree; repeat as needed')
    parser.add_argument('--run',help='Actual prepare output review_run_id')
    parser.add_argument('--receipt',type=Path,help='Verbatim native tool result JSON with actual target and, for accept, completed output')
    args = parser.parse_args()
    try:
        if args.action == 'prepare': result = prepare(args.cwd,args.mode,args.input)
        elif not args.run: raise ValueError('--run required')
        elif args.action == 'supersede':
            _,sprint = context(args.cwd); current(sprint,args.run)
            result = append(sprint,{'event':'superseded','review_run_id':args.run})
        elif not args.receipt: raise ValueError('--receipt required')
        else: result = (bind if args.action == 'bind' else accept)(args.cwd,args.run,args.receipt)
        print(canonical(result)); return 0
    except (ValueError,OSError,RuntimeError) as exc:
        print('[review-binding] '+str(exc),file=sys.stderr); return 2
