'use strict';
// athena tidy [--dry-run]: the self-healing ledger (ai-state-v2 X7) — issues month-close,
// monthly packing, hot-layer limit, .runtime retention (14 days / 50 MB), dead links.
const fs = require('fs');
const path = require('path');
const { requireCtx, flags, today } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const archive = require('./lib/archive.cjs');
const issues = require('../lib/issues.cjs');
const frontmatter = require('../lib/frontmatter.cjs');
const advisory = require('../rules/advisory.cjs');

const HOT_MAX = 3;
const KEEP_MS = 14 * 24 * 3600 * 1000;
const CAP = 50 * 1024 * 1024;
// Never aged out: probe/baselines, migration keep-sakes, archived evidence and snapshots (review S4 P2).
const PROTECTED = /(^|\/)(probe\.json|[^/]*baseline[^/]*|_index\.v1\.md)$|^(snapshots|archive)\//;

function closeMonth(ctx, dry, report, touched) {
  const file = issues.file(ctx.aiState);
  if (!fs.existsSync(file)) return;
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const closedIds = new Set(issues.list(ctx.aiState).filter(r => ['closed', 'dropped'].includes(r.status)).map(r => r.id));
  const moving = lines.filter(l => { const m = l.match(/^\|\s*([BGUEDQ]-\d+)\s*\|/); return m && closedIds.has(m[1]); });
  if (!moving.length) return;
  report.push(`issues: ${moving.length} closed row(s) → archive/issues-${today().slice(0, 7)}.md`);
  if (dry) return;
  const target = path.join(ctx.aiState, 'archive', `issues-${today().slice(0, 7)}.md`);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  if (!fs.existsSync(target)) fs.writeFileSync(target, `# Closed issues ${today().slice(0, 7)}\n\n| id | 类型 | 级别 | 一句话 | 发现于 | 去向 | 状态 |\n|---|---|---|---|---|---|---|\n`);
  fs.appendFileSync(target, `${moving.join('\n')}\n`);
  fs.writeFileSync(file, lines.filter(l => !moving.includes(l)).join('\n'), 'utf8');
  touched.push(archive.stateRel(ctx, 'issues.md'), archive.stateRel(ctx, path.relative(ctx.aiState, target)));
}

function hotLimit(ctx, dry, report, touched) {
  let dirs = [];
  try { dirs = fs.readdirSync(path.join(ctx.aiState, 'sprints'), { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'archive').map(d => d.name).sort(); } catch (_) { return; }
  const paused = dirs.filter(slug => slug !== ctx.sprint).filter(slug => {
    try { return frontmatter.parse(fs.readFileSync(path.join(ctx.aiState, 'sprints', slug, 'design.md'), 'utf8')).status === 'paused'; } catch (_) { return false; }
  });
  let excess = dirs.length - HOT_MAX;
  for (const slug of paused) {
    if (excess <= 0) break;
    const blockers = [...archive.archiveProblems(ctx, slug), ...archive.runtimeReads(ctx, `sprints/${slug}`).map(h => `read by ${h}`)];
    if (blockers.length) { report.push(`hot layer: cannot archive ${slug}: ${blockers.join('; ')}`); continue; }
    excess -= 1;
    report.push(`hot layer > ${HOT_MAX}: archive paused ${slug} (item → deferred)`);
    if (dry) continue;
    const fm = frontmatter.parse(fs.readFileSync(path.join(ctx.aiState, 'sprints', slug, 'design.md'), 'utf8'));
    const itemsPath = fm.roadmap && fm.item ? state.itemsFile(ctx.aiState, fm.roadmap) : null;
    const moved = archive.archiveSprint(ctx, slug);
    touched.push(...moved.stage);
    if (itemsPath && fs.existsSync(itemsPath) && state.readItems(itemsPath).items.some(it => it.slug === fm.item)) {
      state.setItem(itemsPath, fm.item, { status: 'deferred', deferred: { reason: `paused sprint archived: ${moved.rel}/design.md`, resume_when: fm.resume_when || '' } });
      touched.push(archive.stateRel(ctx, `roadmap/${fm.roadmap}/items.yaml`));
    }
  }
  if (excess > 0) report.push(`hot layer still ${dirs.length} > ${HOT_MAX}: ship or pause more (non-paused sprints are never auto-archived)`);
}

function runtimeRetention(ctx, dry, report) {
  const files = [];
  const walk = (dir) => {
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.isFile()) { const st = fs.statSync(full); files.push({ full, rel: path.relative(ctx.runtime, full), size: st.size, mtime: st.mtimeMs }); }
    }
  };
  walk(ctx.runtime);
  // evidence of every hot sprint (active or paused) stays: resume needs it for H2
  let hot = [];
  try { hot = fs.readdirSync(path.join(ctx.aiState, 'sprints')); } catch (_) { /* none */ }
  const live = new Set(hot.map(slug => `evidence/${slug}.jsonl`));
  const candidates = files.filter(f => !PROTECTED.test(f.rel) && !live.has(f.rel.split(path.sep).join('/'))).sort((a, b) => a.mtime - b.mtime);
  const now = Date.now();
  let total = files.reduce((n, f) => n + f.size, 0);
  const drop = [];
  for (const f of candidates) {
    if (now - f.mtime > KEEP_MS || total > CAP) { drop.push(f); total -= f.size; }
  }
  if (!drop.length) return;
  report.push(`.runtime: remove ${drop.length} file(s) (>14 days or over 50 MB)`);
  if (!dry) for (const f of drop) fs.rmSync(f.full, { force: true });
}

function main(argv, io) {
  const { flags: f } = flags(argv, { 'dry-run': 'bool' });
  const ctx = requireCtx(io);
  const dry = Boolean(f['dry-run']);
  const report = [];
  const touched = [];
  closeMonth(ctx, dry, report, touched);
  for (const name of archive.packable(ctx)) {
    const why = archive.packProblems(ctx, name);
    if (why.length) { report.push(`pack skipped: ${why.join('; ')}`); continue; }
    report.push(`pack archive/sprints/${name}/ → archive/${name}.tar.${archive.hasZstd() ? 'zst' : 'gz'}`);
    if (!dry) touched.push(...archive.pack(ctx, name).stage);
  }
  hotLimit(ctx, dry, report, touched);
  runtimeRetention(ctx, dry, report);
  for (const w of advisory.run(ctx, { platform: 'cli' }, ['A6', 'A7', 'A8'])) report.push(`advisory ${w.rule}: ${w.message}`);
  if (!dry) archive.stagePaths(ctx, touched); // only what tidy itself changed
  io.stdout.write(`${report.length ? report.join('\n') : 'tidy: nothing to do'}${dry ? '\n(dry-run: nothing changed)' : ''}\n`);
  return 0;
}

module.exports = { main };
