'use strict';
// One native review/receipt binding in session-log.md; no second task state store.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const input = require('./_input-binding.cjs'), io = require('./_index-io.cjs');
const NATIVE_BINDINGS = {review_run_id:'review_run_id',mode:'mode',base_commit:'base_commit',packet_sha256:'packet_sha256',
  reviewed_packet_sha256:'packet_sha256',input_manifest_sha256:'input_manifest_sha256',reviewed_diff_sha256:'reviewed_diff_sha256'};
function validateNativeMetadata(output,prepared,root) {
  // Inspect only opening frontmatter, never examples or references in the body.
  const lines=output.replace(/^[\ufeff\r\n]+/,'').split(/\r?\n/);
  if (!lines.length || lines[0].trim()!=='---') return;
  const end=lines.findIndex((line,i)=>i>0 && line.trim()==='---');
  if (end<0) throw new Error('native review metadata frontmatter is not closed');
  const seen=new Set();
  const mappings=lines.slice(1,end).map(line=>line.match(/^([ \t]*)([A-Za-z0-9_.-]+)[ \t]*:[ \t]*(.*)$/)).filter(Boolean);
  const rootIndent=Math.min(...mappings.map(match=>match[1].length));
  for (const match of mappings) {
    if (match[1].length!==rootIndent || !Object.hasOwn(NATIVE_BINDINGS,match[2])) continue;
    const key=match[2],raw=match[3].trim();
    if (seen.has(key)) throw new Error('native review metadata duplicate field: '+key);
    seen.add(key);
    let value;
    if (raw.startsWith('"')) {
      const quoted=raw.match(/^("(?:\\.|[^"\\])*")[ \t]*(?:#.*)?$/);
      if (!quoted) throw new Error('native review metadata invalid scalar: '+key);
      value=JSON.parse(quoted[1]);
    } else if (raw.startsWith("'")) {
      const quoted=raw.match(/^'((?:''|[^'])*)'[ \t]*(?:#.*)?$/);
      if (!quoted) throw new Error('native review metadata invalid scalar: '+key);
      value=quoted[1].replaceAll("''", "'");
    } else {
      value=raw.split(' #',1)[0].trim();
      if (!value || value.startsWith('#') || value.toLowerCase()==='null' || value==='~') continue;
    }
    if (value==='') continue;
    let expected=prepared[NATIVE_BINDINGS[key]];
    if (key==='reviewed_diff_sha256') expected=prepared.mode==='implementation' ? require('./delivery-gate.cjs').sourceDiffSha256(root) : null;
    if (typeof value!=='string' || !expected || value!==expected) throw new Error('native review metadata mismatch: '+key);
  }
}
function events(sprint) {
  const log = path.join(sprint,'session-log.md');
  return fs.existsSync(log) ? [...fs.readFileSync(log,'utf8').matchAll(/^<!-- athena-review:(.*?) -->$/gm)].map(m=>JSON.parse(m[1])) : [];
}
function append(sprint,row) {
  const log = path.join(sprint,'session-log.md');
  if (!io.acquire(log)) throw new Error('session log lock unavailable; retry before native dispatch');
  try {
    const prior = fs.existsSync(log) ? fs.readFileSync(log,'utf8') : '# Session log\n';
    io.writeAtomic(log,prior+'\n<!-- athena-review:'+input.canonical({...row,recorded_at:new Date().toISOString()})+' -->\n');
  } finally { io.release(log); }
  return row;
}
function current(sprint,run) {
  const rows = events(sprint), prepared = rows.filter(r=>r.event==='prepared'), latest = prepared.at(-1);
  if (!latest || (run && latest.review_run_id!==run) || rows.some(r=>r.event==='superseded' && r.review_run_id===latest.review_run_id)) throw new Error('unknown or superseded review run');
  return latest;
}
function fileRefs(root,names) {
  const result = {};
  for (const name of names) {
    const file = fs.realpathSync(path.resolve(root,name));
    if (!file.startsWith(fs.realpathSync(root)+path.sep) || !fs.statSync(file).isFile()) throw new Error('review input missing/outside worktree: '+name);
    result[name] = input.digest(fs.readFileSync(file));
  }
  return result;
}
function evidenceIds(sprint) {
  const file = path.join(sprint,'evidence.yaml');
  if (!fs.existsSync(file)) return [];
  return [...new Set([...fs.readFileSync(file,'utf8').matchAll(/^\s*-\s+tool_use_id\s*:\s*([^#\n]*)/gm)]
    .map(match => match[1].trim().replace(/^["']|["']$/g,''))
    .filter(id => id && !['[]','null','~'].includes(id)))].sort();
}
function liveInput(root,sprint,prepared) {
  const inputs = fileRefs(root,prepared.input_paths || []);
  if (prepared.mode==='implementation') Object.assign(inputs,input.snapshot(root,sprint));
  else inputs.design_sha256 = input.digest(fs.readFileSync(path.join(sprint,'design.md')));
  return {base_commit:input.git(root,'rev-parse','HEAD').toString().trim(),packet_sha256:input.digest(fs.readFileSync(path.join(sprint,'review-packet.md'))),
    input_manifest_sha256:input.digest(input.canonical(inputs)),evidence_ids:evidenceIds(sprint),
    evidence_docs:fileRefs(root,Object.keys(prepared.evidence_docs || {}))};
}
function assertLive(root,sprint,prepared) {
  const live = liveInput(root,sprint,prepared);
  // base_commit is recorded, not compared: ship bookkeeping commits must not void a review.
  if (live.packet_sha256!==prepared.packet_sha256) throw new Error('review input changed: packet_sha256');
  if (live.input_manifest_sha256!==prepared.input_manifest_sha256) throw new Error('review input changed: input_manifest_sha256');
  if (input.canonical(live.evidence_docs)!==input.canonical(prepared.evidence_docs || {})) throw new Error('review input changed: evidence_docs');
  const preparedIds = prepared.evidence_ids || [];
  if (!preparedIds.every(id => live.evidence_ids.includes(id))) throw new Error('review input changed: evidence_ids');
}
function explicitVerdict(output) {
  const lines=output.replace(/^[\ufeff\r\n]+/,'').split(/\r?\n/);
  if (lines[0] && lines[0].trim()==='---') {
    const end=lines.findIndex((line,i)=>i>0 && line.trim()==='---');
    if (end>0) {
      for (const line of lines.slice(1,end)) {
        const match=line.match(/^verdict\s*:\s*["']?(PASS|REWORK|FAIL|CONCERNS)\b/i);
        if (match) return match[1].toUpperCase();
      }
    }
  }
  const verdicts=[...new Set([...output.matchAll(/(?:^|[\s>])(?:VERDICT|verdict)\s*:\s*["']?(PASS|REWORK|FAIL|CONCERNS)\b/gm)].map(match=>match[1].toUpperCase()))];
  if (!verdicts.length) throw new Error('native result has no explicit verdict');
  if (verdicts.length!==1) throw new Error('native result has conflicting verdicts');
  return verdicts[0];
}
function prepare(cwd,mode,inputs) {
  const [root,sprint] = input.context(cwd);
  if (!['design','implementation'].includes(mode)) throw new Error('mode must be design or implementation');
  const rows = events(sprint), latest = rows.filter(r=>r.event==='prepared').at(-1);
  if (latest && !rows.some(r=>r.review_run_id===latest.review_run_id && ['accepted','received','superseded'].includes(r.event))) throw new Error('review already pending; recover its receipt or explicitly supersede');
  require('./delivery-gate.cjs').validateReviewPacket(sprint);
  let docs = [];
  if (mode==='implementation') {
    if (!fs.existsSync(path.join(sprint,'evidence.yaml'))) throw new Error('implementation review requires evidence.yaml');
    docs = ['runtime-verify.md','cleanup-pass.md','review-manifest.yaml'].filter(n=>fs.existsSync(path.join(sprint,n))).map(n=>path.relative(root,path.join(sprint,n)).split(path.sep).join('/'));
  }
  const row = {event:'prepared',schema_version:1,review_run_id:crypto.randomUUID(),mode,author_target:process.env.CODEX_THREAD_ID || process.env.CLAUDE_SESSION_ID || '',
    input_paths:[...new Set(inputs)].sort(),evidence_docs:Object.fromEntries(docs.map(n=>[n,'']))};
  Object.assign(row,liveInput(root,sprint,row));
  return append(sprint,row);
}
function nativeReceipt(file,expectedTarget='') {
  let obj = JSON.parse(fs.readFileSync(file,'utf8'));
  if (!obj || typeof obj!=='object' || Array.isArray(obj)) throw new Error('native receipt must be an object');
  if (obj.structuredContent && typeof obj.structuredContent==='object') obj = obj.structuredContent;
  if (Array.isArray(obj.agents)) {
    const matches=obj.agents.filter(a=>a.agent_name===expectedTarget);
    if (matches.length!==1) throw new Error('native agent listing lacks exactly one bound target');
    const item=matches[0];
    return item.agent_status && typeof item.agent_status.completed==='string' ? [item.agent_name,'completed',item.agent_status.completed] : [item.agent_name,'unknown',''];
  }
  let target = ['agent_id','agentId','threadId','thread_id','task_name'].map(k=>obj[k]).find(v=>typeof v==='string' && v) || '';
  let status = obj.status || '', output = obj.output || obj.result || '';
  if (status && typeof status==='object' && Object.keys(status).length===1) {
    const [id,item] = Object.entries(status)[0]; target=id;
    if (item && typeof item.completed==='string') { output=item.completed; status='completed'; }
  }
  if (!output && Array.isArray(obj.content)) output=obj.content.filter(c=>c.type==='text').map(c=>c.text || '').join('\n');
  if (!target) throw new Error('native receipt has no actual target ID');
  return [target,status,typeof output==='string' ? output : ''];
}
function persistReceipt(sprint,run,kind,receipt) {
  const target = path.join(sprint,'reviews/_native',run+'-'+kind+'.json'), raw = fs.readFileSync(receipt,'utf8');
  fs.mkdirSync(path.dirname(target),{recursive:true}); io.writeAtomic(target,raw);
  return [path.relative(sprint,target).split(path.sep).join('/'),input.digest(raw)];
}
function bind(cwd,run,receipt) {
  const [root,sprint] = input.context(cwd), prepared=current(sprint,run);
  assertLive(root,sprint,prepared);
  const [target] = nativeReceipt(receipt);
  if (target===prepared.author_target) throw new Error('reviewer target is the author session');
  if (events(sprint).some(r=>r.event==='bound' && (r.reviewer_target===target || r.review_run_id===run))) throw new Error('target/run already bound; a fresh independent request is required');
  const [ref,sha] = persistReceipt(sprint,run,'dispatch',receipt);
  const row = append(sprint,{event:'bound',review_run_id:run,reviewer_target:target,dispatch_receipt_ref:ref,dispatch_receipt_sha256:sha});
  io.update(path.join(root,'.ai_state/_index.md'),text=>text.replace(/^next_action:.*$/m,'next_action: "await-review-result"'));
  return row;
}
function accepted(sprint,run) { return events(sprint).filter(r=>r.event==='accepted' && r.review_run_id===run); }
function accept(cwd,run,receipt) {
  const [root,sprint] = input.context(cwd), prepared = current(sprint,run);
  if (events(sprint).some(r=>r.review_run_id===run && ['accepted','received'].includes(r.event))) throw new Error('review result already accepted');
  const bound = events(sprint).filter(r=>r.event==='bound' && r.review_run_id===run);
  if (bound.length!==1) throw new Error('review requires exactly one persisted native dispatch binding');
  const [target,status,output] = nativeReceipt(receipt,bound[0].reviewer_target);
  if (target!==bound[0].reviewer_target || !['completed','complete','succeeded'].includes(status) || !output.trim()) throw new Error('wrong target, unknown/incomplete native result, or missing output');
  assertLive(root,sprint,prepared);
  validateNativeMetadata(output,prepared,root);
  const verdict=explicitVerdict(output);
  const [ref,sha] = persistReceipt(sprint,run,'result',receipt), doc=path.join(sprint,'reviews',prepared.mode+'-review.md');
  const fm = {schema_version:1,mode:prepared.mode,review_run_id:run,reviewer_target:target,packet_sha256:prepared.packet_sha256,
    input_manifest_sha256:prepared.input_manifest_sha256,native_output_ref:ref,verdict};
  let header = '---\n'+Object.entries(fm).map(([k,v])=>k+': '+JSON.stringify(v)+'\n').join('')+'---\n\n';
  const manifest = path.join(sprint,'review-manifest.yaml');
  if (prepared.mode==='implementation' && fs.existsSync(manifest)) header+='Reviewed design sha256: '+input.digest(fs.readFileSync(path.join(sprint,'design.md')))+'\nReviewed implementation commit: '+prepared.base_commit+'\nReviewed state manifest sha256: '+input.digest(fs.readFileSync(manifest))+'\n\n';
  io.writeAtomic(doc,header+'## Native review output\n\n'+output);
  const row = append(sprint,{event:verdict==='PASS' ? 'accepted':'received',verdict,review_run_id:run,reviewer_target:target,native_output_ref:ref,native_output_sha256:sha,
    output_ref:path.relative(sprint,doc).split(path.sep).join('/'),output_sha256:input.digest(fs.readFileSync(doc))});
  io.update(path.join(root,'.ai_state/_index.md'),text=>{
    text=text.replace(/^next_action:.*$/m,'next_action: "'+(verdict==='PASS' ? '':'rework_impl')+'"');
    if (verdict==='PASS') text=text.replace(/^design_changed_after_impl:.*$/m,'design_changed_after_impl: false');
    return text;
  });
  return row;
}
function validateCurrent(root,sprint,review) {
  const prepared = current(sprint);
  if (prepared.mode!=='implementation') throw new Error('latest request did not review implementation');
  assertLive(root,sprint,prepared);
  const rows = accepted(sprint,prepared.review_run_id);
  if (rows.length!==1) throw new Error('missing or duplicate accepted native review');
  const row = rows[0];
  if (path.resolve(sprint,row.output_ref)!==path.resolve(review) || input.digest(fs.readFileSync(review))!==row.output_sha256) throw new Error('accepted review output changed/missing');
  const bound = events(sprint).filter(r=>r.event==='bound' && r.review_run_id===prepared.review_run_id);
  if (bound.length!==1) throw new Error('missing native dispatch binding');
  for (const [ref,sha] of [[bound[0].dispatch_receipt_ref,bound[0].dispatch_receipt_sha256],[row.native_output_ref,row.native_output_sha256]]) {
    if (input.digest(fs.readFileSync(path.join(sprint,ref)))!==sha) throw new Error('native receipt changed/missing');
  }
  const [target,status,output] = nativeReceipt(path.join(sprint,row.native_output_ref),bound[0].reviewer_target);
  if (target!==bound[0].reviewer_target || target!==row.reviewer_target || !['completed','complete','succeeded'].includes(status)) throw new Error('native result identity/status mismatch');
  validateNativeMetadata(output,prepared,root);
}
function main(argv=process.argv.slice(2)) {
  if (argv.includes('--help') || !argv.length) {
    process.stdout.write('Usage: review-binding.cjs prepare|bind|accept|supersede [--cwd ABS_WORKTREE] [--mode design|implementation] [--input REL_DOC ...] [--run PREPARED_ID] [--receipt NATIVE_TOOL_RESULT.json]\nPrepare generates run/base/packet/input/evidence hashes from actual files. Bind and accept read saved native tool results, never a guessed target. Accept requires completed status and an explicit verdict; negative results are retained for rework, only PASS is deliverable. Supersede only after the old request ended or was invalidated.\n'); return 0;
  }
  const action=argv[0], args={cwd:process.cwd(),mode:'implementation',input:[]};
  try {
    for (let i=1;i<argv.length;i+=2) {
      const key=argv[i].replace(/^--/,'');
      if (!['cwd','mode','input','run','receipt'].includes(key) || !argv[i+1]) throw new Error('unknown or missing option: '+argv[i]);
      if (key==='input') args.input.push(argv[i+1]); else args[key]=argv[i+1];
    }
    let result;
    if (action==='prepare') result=prepare(args.cwd,args.mode,args.input);
    else if (!args.run) throw new Error('--run required');
    else if (action==='supersede') { const [,sprint]=input.context(args.cwd); current(sprint,args.run); result=append(sprint,{event:'superseded',review_run_id:args.run}); }
    else if (!args.receipt) throw new Error('--receipt required');
    else if (action==='bind' || action==='accept') result=(action==='bind' ? bind:accept)(args.cwd,args.run,args.receipt);
    else throw new Error('unknown action');
    process.stdout.write(input.canonical(result)+'\n'); return 0;
  } catch (e) { process.stderr.write('[review-binding] '+e.message+'\n'); return 2; }
}
module.exports={events,append,current,prepare,bind,accept,validateCurrent,main};
