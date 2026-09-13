'use strict';
// Native CC counterpart of _input_binding.py. No other platform runtime needed.
const fs = require('fs'), path = require('path'), os = require('os'), crypto = require('crypto');
const {execFileSync} = require('child_process');
const {writeAtomic} = require('./_index-io.cjs');
const FIELDS = ['source_sha256', 'design_sha256', 'environment_sha256'];
const PUBLIC_ENV = new Set(['system','release','machine','os','arch','image','runtime','version','scenario','seed','recipe','required']);
const COMMAND_PREFIX = String.raw`(?:^|[;&|]\s*)\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*(?:npx\s+)?`;
const VALIDATION_PATTERNS = [
  ['test',String.raw`(?:python3?\s+-m\s+(?:pytest|unittest)|pytest|unittest|(?:npm|pnpm|yarn|bun)\s+(?:test|run\s+test)|cargo\s+test|go\s+test|mvn\s+(?:test|verify)|\./gradlew\s+test)`],
  ['lint',String.raw`(?:eslint|prettier\s+--check|ruff|(?:npm|pnpm|yarn|bun)\s+run\s+lint|cargo\s+clippy|go\s+vet|node\s+--check|git\s+diff\s+--check)`],
  ['typecheck',String.raw`(?:tsc|(?:npm|pnpm|yarn|bun)\s+run\s+(?:typecheck|check)|cargo\s+check)`],
  ['build',String.raw`(?:(?:npm|pnpm|yarn|bun)\s+run\s+build|cargo\s+build|go\s+build|mvn\s+compile|\./gradlew\s+build|cmake\s+--build)`],
].map(([kind,pattern])=>[kind,new RegExp(COMMAND_PREFIX+pattern+'\\b','im')]);
// One native classifier for both pre and post; no collector-side pattern copy.
function classifyValidation(command) { return VALIDATION_PATTERNS.find(([,pattern])=>pattern.test(command))?.[0] || null; }
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
function required(sprint) {
  // 9.9.9 hooks enable binding for the current sprint. Never read project version:
  // that field is agent-writable and would silently disable AC6/AC7 after migrate.
  const index = path.join(sprint,'../../_index.md');
  if (!fs.existsSync(index)) return false;
  const text = fs.readFileSync(index,'utf8');
  const slug=text.match(/^current_sprint_slug:\s*["']?([A-Za-z0-9][A-Za-z0-9._-]*)/m);
  return Boolean(slug && slug[1]===path.basename(sprint));
}
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
function git(root, ...args) { return execFileSync('git', args, {cwd:root, timeout:15000, stdio:['ignore','pipe','pipe']}); }
function context(cwd) {
  const root = git(cwd, 'rev-parse','--show-toplevel').toString().trim();
  const text = fs.readFileSync(path.join(root,'.ai_state/_index.md'),'utf8');
  const m = text.match(/^current_sprint_slug:\s*["']?([A-Za-z0-9][A-Za-z0-9._-]*)/m);
  if (!m) throw new Error('current sprint unavailable');
  return [root,path.join(root,'.ai_state/sprints',m[1])];
}
function sourceSha256(root) {
  const names = [...new Set(git(root,'ls-files','-z','-c','-o','--exclude-standard').toString('utf8').split('\0').filter(Boolean))].sort();
  const h = crypto.createHash('sha256');
  for (const name of names) {
    const parts = name.split('/');
    if (['.ai_state','.runtime'].includes(parts[0])) continue;
    if (parts.some(p=>p.startsWith('.env') || /\.(pem|key|p12)$/.test(p) || ['credentials','secrets'].includes(p.toLowerCase()))) continue;
    const target = path.join(root,name);
    h.update(name+'\0');
    let stat; try { stat = fs.lstatSync(target); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    if (!stat) h.update('deleted');
    else if (stat.isSymbolicLink()) h.update('link\0'+fs.readlinkSync(target));
    else if (stat.isFile()) { h.update(stat.mode & 0o111 ? 'executable\0':'file\0'); h.update(fs.readFileSync(target)); }
    else if (stat.isDirectory()) { process.stderr.write('[input-binding] skip gitlink/submodule: '+name+'\n'); h.update('gitlink\0'); }
    else throw new Error('unsupported source directory/submodule: '+name);
    h.update('\n');
  }
  return h.digest('hex');
}
function environment(root) {
  const result = {system:os.type().toLowerCase(),release:os.release(),machine:os.machine(),recipe:[]};
  for (const name of ['.ai_state/runtime-env.yaml','.ai_state/conventions/runtime-env.yaml','.ai_state/conventions/runtime-env.md']) {
    const file = path.join(root,name); if (!fs.existsSync(file)) continue;
    const publicFields = [];
    for (const line of fs.readFileSync(file,'utf8').split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_]+):\s*(.*?)\s*$/);
      if (m && PUBLIC_ENV.has(m[1])) {
        if (/:\/\/[^/\s]*@|(?:token|password|secret|api.key)\s*[=:]/i.test(m[2])) throw new Error('public environment field contains credential syntax');
        publicFields.push([m[1],m[2]]);
      }
    }
    result.recipe.push([name,publicFields]);
  }
  return result;
}
function snapshot(root,sprint) {
  return {source_sha256:sourceSha256(root),design_sha256:digest(fs.readFileSync(path.join(sprint,'design.md'))),environment_sha256:digest(canonical(environment(root)))};
}
function commandOf(payload) { return String(payload.tool_input?.command || payload.tool_input?.cmd || ''); }
function executionCwd(payload) { return payload.tool_input?.workdir || payload.cwd || process.cwd(); }
function prePath(root,payload) {
  if (typeof payload.tool_use_id !== 'string' || !payload.tool_use_id) throw new Error('native tool_use_id unavailable');
  return path.join(root,'.ai_state/.runtime/evidence-inputs',digest(payload.tool_use_id)+'.json');
}
function captureBefore(payload) {
  if (!classifyValidation(commandOf(payload))) return;
  if (/(?:^|[;&|]\s*)cd\s/.test(commandOf(payload))) throw new Error('use the tool workdir for validation; shell directory changes are not bound');
  const [root,sprint] = context(executionCwd(payload)), file = prePath(root,payload);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  writeAtomic(file,canonical(snapshot(root,sprint)));
}
function finish(payload,redactedOutput) {
  try {
    const [root,sprint] = context(executionCwd(payload)), file = prePath(root,payload);
    const before = JSON.parse(fs.readFileSync(file,'utf8')); fs.unlinkSync(file);
    const current = snapshot(root,sprint);
    if (canonical(before) !== canonical(current)) return {binding_status:'unverifiable'};
    const output = path.join(sprint,'evidence',digest(payload.tool_use_id)+'.txt');
    fs.mkdirSync(path.dirname(output),{recursive:true}); writeAtomic(output,redactedOutput);
    return {...current,binding_status:'current',output_artifact:path.relative(sprint,output).split(path.sep).join('/'),artifact_sha256:digest(fs.readFileSync(output))};
  } catch (_) { return {binding_status:'unverifiable'}; }
}
function currentRecord(record,root,sprint,live) {
  if (record.binding_status !== 'current') return false;
  try {
    const current = live || snapshot(root,sprint), output = fs.realpathSync(path.resolve(sprint,record.output_artifact));
    if (!output.startsWith(fs.realpathSync(sprint)+path.sep)) return false;
    return FIELDS.every(k=>record[k]===current[k]) && digest(fs.readFileSync(output))===record.artifact_sha256;
  } catch (_) { return false; }
}
module.exports = {FIELDS,classifyValidation,required,canonical,digest,git,context,sourceSha256,environment,snapshot,captureBefore,finish,currentRecord};
