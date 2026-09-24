'use strict';
// athena migrate --to 10.1 [--dry-run] [--report <file>]  (design §11.3).
// Dry-run changes nothing (a --report file is written only where asked). A real run needs a
// clean tracked tree, tags pre-athena-10.1-state, moves files, stages them — never commits.
const fs = require('fs');
const path = require('path');
const { requireCtx, flags, today, UsageError, VERSION } = require('./lib/common.cjs');
const { plan } = require('./lib/migrate-plan.cjs');
const state = require('./lib/state.cjs');
const archive = require('./lib/archive.cjs');
const { git } = require('../lib/context.cjs');

/** Everything that would make a real run lose data or stop half-way (review S4 P0/P2). */
function blockers(ctx, p, allowReads) {
  const out = [];
  const targets = new Map();
  for (const a of p.actions) {
    if (a.kind !== 'move') continue;
    if (fs.existsSync(path.join(ctx.aiState, a.to))) out.push(`${a.to} already exists`);
    if (targets.has(a.to)) out.push(`${targets.get(a.to)} and ${a.from} both move to ${a.to}`);
    targets.set(a.to, a.from);
    if (allowReads) continue;
    try { for (const hit of archive.runtimeReads(ctx, a.from)) out.push(`${a.from} is read by ${hit}`); }
    catch (error) { out.push(error.message); }
  }
  return out;
}

function report(ctx, p, dry, blocked = [], tag = 'pre-athena-10.1-state') {
  const L = [`# Athena 10.1 state migration ${dry ? '(dry-run)' : ''}`.trim(), '', `- project: ${path.basename(ctx.mainRoot)}`, `- date: ${today()}`, ''];
  L.push('## _index', '');
  if (p.index.already) L.push('already athena-state/2');
  else {
    L.push(`- v1 size ${p.index.bytes} B → v2 fields: ${Object.keys(p.index.v2).join(', ')}`);
    L.push(`- to .runtime/probe.json: ${Object.keys(p.index.probe).join(', ') || '—'}`);
    L.push(`- dropped: ${p.index.dropped.join(', ') || '—'}`);
    for (const n of p.index.notes) L.push(`- note: ${n}`);
  }
  const counts = {};
  for (const a of p.actions) counts[a.kind] = (counts[a.kind] || 0) + 1;
  L.push('', `## Files (${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(', ') || 'none'})`, '', '| kind | from | to | note |', '|---|---|---|---|');
  for (const a of p.actions) L.push(`| ${a.kind} | ${a.from} | ${a.to} | ${a.note} |`);
  L.push('', `## Lessons to triage (${p.lessons.length}; learning/trick → AGENTS.md rule, skill 坑 or drop — decided by a human/agent, never automatic)`, '');
  for (const l of p.lessons) L.push(`- ${l}`);
  L.push('', `## issues.md draft (${p.issues.length} rows → issues.draft.md; replace proposals/vm-pending after confirmation)`, '');
  for (const r of p.issues.slice(0, 60)) L.push(`- ${r.type}: ${r.text.slice(0, 120)} (${r.found})`);
  const loose = p.actions.filter(a => a.kind === 'move').map(a => [a, archive.inventory(ctx, a.from).loose]).filter(([, l]) => l.length);
  L.push('', `## Untracked/ignored files that move but stay untracked (${loose.reduce((n, [, l]) => n + l.length, 0)}; a rollback leaves them at the new path; months holding them are not packed)`, '');
  for (const [a, l] of loose.slice(0, 30)) L.push(`- ${a.from}: ${l.length} file(s), e.g. ${l[0]}`);
  for (const n of p.notes || []) L.push('', `> ${n}`);
  L.push('', `## Blockers (${blocked.length})`, '');
  for (const b of blocked) L.push(`- ${b}`);
  L.push('', '## Rollback', '', `\`git reset --hard ${tag}\` (real run only). It restores tracked files only: afterwards move the untracked/ignored files listed above back to their old paths (or delete them) and remove \`.ai_state/.runtime/{probe.json,_index.v1.md,snapshots/}\` — the restored .gitignore no longer hides them, so a later \`git add -A\` would commit them.`, '');
  return L.join('\n');
}

function apply(ctx, p) {
  const A = ctx.aiState;
  const staged = [archive.stateRel(ctx, '_index.md'), '.gitignore'];
  if (!p.index.already) {
    const index = path.join(A, '_index.md');
    const old = fs.readFileSync(index, 'utf8');
    fs.mkdirSync(ctx.runtime, { recursive: true });
    fs.writeFileSync(path.join(ctx.runtime, 'probe.json'), `${JSON.stringify({ migrated: today(), ...p.index.probe }, null, 2)}\n`);
    fs.writeFileSync(path.join(ctx.runtime, '_index.v1.md'), old);
    fs.writeFileSync(index, state.render('_index.md', { version: VERSION() }));
    state.setFields(index, { ...p.index.v2, route: p.index.v2.route });
  }
  for (const a of p.actions) {
    const from = path.join(A, a.from);
    const to = path.join(A, a.to);
    if (a.kind === 'move') {
      const { tracked } = archive.inventory(ctx, a.from);
      const prefix = archive.stateRel(ctx, a.from);
      fs.mkdirSync(path.dirname(to), { recursive: true });
      const ignored = archive.ignoredIn(ctx, a.from);
      fs.renameSync(from, to);
      archive.redirect(ctx, a.from, a.to);
      staged.push(archive.keepIgnored(ctx, ignored, a.from, a.to));
      staged.push(...tracked, ...tracked.map(f => archive.stateRel(ctx, a.to) + f.slice(prefix.length)), archive.stateRel(ctx, 'archive/README.md'));
    } else if (a.kind === 'pause') {
      const design = path.join(from, 'design.md');
      if (fs.existsSync(design) && fs.readFileSync(design, 'utf8').startsWith('---')) { state.setFields(design, { status: 'paused' }); staged.push(archive.stateRel(ctx, `${a.from}/design.md`)); }
    } else if (a.kind === 'untrack') {
      git(ctx.mainRoot, ['rm', '-r', '-q', '--cached', '--ignore-unmatch', '--', path.join(path.relative(ctx.mainRoot, A), a.from)]);
      fs.mkdirSync(path.dirname(to), { recursive: true });
      if (!fs.existsSync(to)) fs.renameSync(from, to);
    }
  }
  staged.push(...['issues.draft.md', 'issues.md', 'queue.md'].map(n => archive.stateRel(ctx, n)));
  if (p.issues.length) {
    fs.writeFileSync(path.join(A, 'issues.draft.md'), `${fs.readFileSync(path.join(state.templatesDir(), 'issues.md'), 'utf8')}${p.issues.map((r, i) => `| ${r.type === 'env' ? 'E' : 'D'}-D${String(i + 1).padStart(3, '0')} | ${r.type} | — | ${r.text.replace(/\|/g, '/').slice(0, 160)} | ${r.found} | 待确认 | draft |`).join('\n')}\n`);
  }
  for (const name of ['issues.md', 'queue.md']) if (!fs.existsSync(path.join(A, name))) fs.copyFileSync(path.join(state.templatesDir(), name), path.join(A, name));
  archive.stagePaths(ctx, staged); // moves must be in the index before packing sees them as tracked
  const packed = archive.packable(ctx).filter(name => !archive.packProblems(ctx, name).length).map(name => archive.pack(ctx, name));
  for (const pk of packed) staged.push(...pk.stage);
  const ignore = path.join(ctx.mainRoot, '.gitignore');
  const rel = path.relative(ctx.mainRoot, A).split(path.sep).join('/');
  let gi = fs.existsSync(ignore) ? fs.readFileSync(ignore, 'utf8') : '';
  for (const line of [`${rel}/.runtime/`, `${rel}/.snapshots/`]) if (!gi.split('\n').includes(line)) gi += `${gi.endsWith('\n') || !gi ? '' : '\n'}${line}\n`;
  fs.writeFileSync(ignore, gi);
  archive.stagePaths(ctx, staged); // exactly what migrate moved or wrote — never the user's other loose files
  return packed.map(pk => pk.rel);
}

function main(argv, io) {
  let f;
  try { f = flags(argv, { to: 'str', 'dry-run': 'bool', report: 'str', 'allow-reads': 'str' }).flags; } catch (error) { io.stderr.write(`athena migrate: ${error.message}\n`); return 2; }
  if (f.to !== '10.1') { io.stderr.write('usage: athena migrate --to 10.1 [--dry-run] [--report <file>] [--allow-reads "<reason>"]\n'); return 2; }
  let ctx;
  try { ctx = requireCtx(io); } catch (error) { io.stderr.write(`athena migrate: ${error.message}\n`); return 2; }
  const dry = Boolean(f['dry-run']);
  const p = plan(ctx.aiState);
  // --allow-reads "<reason>": literal mentions in frozen/historical sources may be accepted, with the reason logged
  const blocked = blockers(ctx, p, Boolean(f['allow-reads']));
  if (f['allow-reads']) p.notes = [`runtime-read check waived: ${f['allow-reads']}`];
  let tag = 'pre-athena-10.1-state';
  if (!dry && blocked.length) {
    io.stderr.write(`athena migrate: refused — ${blocked.length} blocker(s):\n${blocked.map(b => `  ${b}`).join('\n')}\n`);
    return 1;
  }
  if (!dry) {
    const dirty = git(ctx.mainRoot, ['status', '--porcelain', '--untracked-files=no']);
    if (dirty === null || dirty) { io.stderr.write(`athena migrate: tracked changes present; commit or stash first\n${dirty || ''}\n`); return 1; }
    if (git(ctx.mainRoot, ['rev-parse', '-q', '--verify', 'refs/tags/pre-athena-10.1-state'])) tag = `pre-athena-10.1-state-${Date.now()}`;
    if (git(ctx.mainRoot, ['tag', tag]) === null) { io.stderr.write('athena migrate: could not create the rollback tag\n'); return 1; }
    io.stderr.write(`rollback tag: ${tag}\n`);
    const packed = apply(ctx, p);
    if (packed.length) io.stderr.write(`packed: ${packed.join(', ')}\n`);
  }
  const text = report(ctx, p, dry, blocked, tag);
  if (f.report) { fs.mkdirSync(path.dirname(path.resolve(io.cwd, f.report)), { recursive: true }); fs.writeFileSync(path.resolve(io.cwd, f.report), text); }
  io.stdout.write(`${text}\n`);
  return 0;
}

module.exports = { main };
