'use strict';
// athena status [--json]: the human view, generated on the spot (ai-state-v2 §3.7).
const fs = require('fs');
const path = require('path');
const { requireCtx, flags } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const issues = require('../lib/issues.cjs');
const exemptions = require('../lib/exemptions.cjs');
const frontmatter = require('../lib/frontmatter.cjs');
const advisory = require('../rules/advisory.cjs');
const evidence = require('../lib/evidence.cjs');
const archive = require('./lib/archive.cjs');
const { idle } = require('../lib/context.cjs');
const { tree, reviewIgnore } = require('../core.cjs');
const h1 = require('../rules/h1-design.cjs');
const h2 = require('../rules/h2-evidence.cjs');
const h3 = require('../rules/h3-review.cjs');

const RUN = (id) => `athena run --covers ${id} -- <test/typecheck/build command>`;

/**
 * Per-AC evidence state against the CURRENT source tree, with the same validity rule H2 uses
 * (evidence.valid): covered = a provable PASS on this tree; stale = a PASS on another tree
 * (or another review_ignore list); missing = no PASS at all.
 */
function matrix(ctx, sha, ignore) {
  let design = '';
  try { design = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8'); } catch (_) { /* H1 territory */ }
  const hotfix = ctx.path === 'Hotfix';
  const current = new Set(sha ? evidence.valid(ctx, sha, { anyProvableKind: hotfix, ignore }).map(r => r.id) : []);
  const pass = (r) => r.exit === 0 && (r.provable === true || (hotfix && r.kind === 'lint' && r.reason === null));
  const rows = evidence.read(ctx);
  return h1.criteria(design).map(ac => {
    const mine = rows.filter(r => (r.covers || []).includes(ac.id));
    const fresh = mine.filter(r => current.has(r.id));
    const old = mine.filter(r => pass(r) && !current.has(r.id));
    const last = mine[mine.length - 1];
    const state = fresh.length ? 'covered' : (old.length ? 'stale' : 'missing');
    let detail = '';
    if (state === 'stale') detail = `PASS ${old[old.length - 1].id} is for tree ${String(old[old.length - 1].tree_sha).slice(0, 12)}; source changed since`;
    else if (state === 'missing' && last) detail = last.exit === 0 ? `record ${last.id} is not provable (${last.kind}${last.reason ? `, ${last.reason}` : ''})` : `record ${last.id} exited ${last.exit}`;
    return { id: ac.id, text: ac.text.slice(0, 160), state, evidence: (fresh.length ? fresh : old).map(r => r.id), detail, fix: state === 'covered' ? '' : RUN(ac.id) };
  });
}

/**
 * What `athena ship` would refuse on right now — the same checks in the same order, but all of
 * them reported (ship stops at the first). Read-only: h2/h3.check are called directly, so the
 * Stop breaker and the ledger are never touched.
 */
function precheck(ctx, sha, ignore, acs) {
  const ev = { platform: 'cli' };
  const blockers = [];
  const add = (rule, reason, fix) => blockers.push({ rule, reason, fix });
  const guard = (rule, fn) => { try { fn(); } catch (error) { add(rule, `${rule} check failed: ${error.message}`, 'athena doctor'); } };
  guard('H2', () => { const v = h2.check(ev, ctx, sha, ignore); if (v) add('H2', v.reason, 'athena run -- <test/typecheck/build command>'); });
  guard('H3', () => { const v = h3.check(ev, ctx, sha, ignore); if (v) add('H3', v.reason, 'athena review prepare'); });
  guard('runtime-read', () => {
    const reads = archive.runtimeReads(ctx, `sprints/${ctx.sprint}`);
    if (reads.length) add('runtime-read', `code outside .ai_state reads this sprint's path: ${reads.slice(0, 5).join('; ')}`, 'repoint those reads, then athena ship --dry-run');
  });
  guard('archive', () => {
    const problems = archive.archiveProblems(ctx, ctx.sprint);
    if (problems.length) add('archive', problems.join('; '), 'athena ship --dry-run');
  });
  guard('roadmap', () => {
    const fm = frontmatter.parse(fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8'));
    const roadmap = String(fm.roadmap || ''), item = String(fm.item || '');
    const file = roadmap && item ? state.itemsFile(ctx.aiState, roadmap) : null;
    if (file && (!fs.existsSync(file) || !state.readItems(file).items.some(it => it.slug === item))) {
      add('roadmap', `design names ${roadmap}/${item} but roadmap/${roadmap}/items.yaml has no such item`, 'restore the design/item link, then athena ship --dry-run');
    }
  });
  // ship only warns about these (it never refuses on them), so they are not blockers
  const uncovered = acs.filter(a => a.state !== 'covered').map(a => a.id);
  return { ok: !blockers.length, tree_sha: sha || null, stage: ctx.stage, blockers, uncovered };
}

/** AC matrix + ship pre-check for the sprint in flight; null when there is none. */
function sprintView(ctx) {
  if (ctx.invalid || idle(ctx) || !ctx.sprintDir) return null;
  const ignore = reviewIgnore(ctx);
  const sha = tree(ctx);
  const acs = matrix(ctx, sha, ignore);
  return { acs, ship_precheck: precheck(ctx, sha, ignore, acs) };
}

/** Everything status and session-start show. */
function collect(ctx) {
  const items = state.allItems(ctx.aiState);
  let hot = [];
  try {
    hot = fs.readdirSync(path.join(ctx.aiState, 'sprints'), { withFileTypes: true })
      .filter(d => d.isDirectory() && d.name !== 'archive').map(d => {
        let fm = {};
        try { fm = frontmatter.parse(fs.readFileSync(path.join(ctx.aiState, 'sprints', d.name, 'design.md'), 'utf8')); } catch (_) { /* none */ }
        return { slug: d.name, status: d.name === ctx.sprint ? 'active' : String(fm.status || 'unknown'), resume_when: fm.resume_when || '' };
      });
  } catch (_) { /* none */ }
  const waiting = [
    ...items.filter(it => ['deferred', 'paused'].includes(String(it.data.status)))
      .map(it => ({ ref: `${it.roadmap}/${it.slug}`, when: (it.data.deferred && it.data.deferred.resume_when) || '' })),
    ...hot.filter(h => h.status === 'paused' && !items.some(it => it.data.sprint === h.slug || it.data.sprint_slug === h.slug))
      .map(h => ({ ref: `sprint ${h.slug}`, when: h.resume_when })),
  ].map(w => ({ ...w, ready: state.resumeReady(ctx.aiState, w.when, items) }));
  let queue = [];
  try { queue = fs.readFileSync(path.join(ctx.aiState, 'queue.md'), 'utf8').split('\n').filter(l => /^\s*(?:\d+[.)]|[-*])\s/.test(l)).slice(0, 10); } catch (_) { /* none */ }
  const roadmaps = {};
  for (const it of items) {
    const r = (roadmaps[it.roadmap] = roadmaps[it.roadmap] || {});
    const s = state.DONE.has(String(it.data.status)) ? 'done' : String(it.data.status || 'pending');
    r[s] = (r[s] || 0) + 1;
  }
  const open = issues.list(ctx.aiState).filter(r => !['closed', 'dropped'].includes(r.status));
  return {
    route: { path: ctx.path, stage: ctx.stage, sprint: ctx.sprint, roadmap: ctx.roadmap, next_action: String(ctx.index.next_action || ''), invalid: ctx.invalid || null },
    hot, waiting, queue, roadmaps,
    questions: open.filter(r => r.type === 'question'),
    issues_open: open.length,
    exemptions: exemptions.review(ctx).map(x => ({ key: x.entry && x.entry.key, until: x.entry && x.entry.until, status: x.status, why: x.why })),
    advisories: advisory.run(ctx, { platform: 'cli' }, advisory.AT.session),
    ...(sprintView(ctx) || {}), // acs + ship_precheck; absent when idle so idle output is unchanged
  };
}

function main(argv, io) {
  const { flags: f } = flags(argv, { json: 'bool' });
  const ctx = requireCtx(io);
  const s = collect(ctx);
  if (f.json) { io.stdout.write(`${JSON.stringify(s, null, 2)}\n`); return 0; }
  const out = [];
  const r = s.route;
  out.push(r.invalid ? `route: UNKNOWN (${r.invalid})` : `route: ${r.path || 'idle'} ${r.stage} ${r.sprint}`.trim());
  if (r.next_action) out.push(`next: ${r.next_action}`);
  if (s.hot.length) out.push(`hot (${s.hot.length}/3): ${s.hot.map(h => `${h.slug}[${h.status}]`).join(', ')}`);
  for (const [name, counts] of Object.entries(s.roadmaps)) out.push(`roadmap ${name}: ${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(', ')}`);
  for (const q of s.queue) out.push(`queue ${q.trim()}`);
  for (const w of s.waiting) out.push(`waiting ${w.ref}${w.when ? ` — ${w.when}` : ''}${w.ready === true ? '  ← READY' : ''}`);
  for (const q of s.questions) out.push(`待裁定 ${q.id}: ${q.text}`);
  if (s.acs) {
    out.push(`acceptance (${s.acs.filter(a => a.state === 'covered').length}/${s.acs.length} covered on tree ${String(s.ship_precheck.tree_sha || '?').slice(0, 12)}):`);
    if (!s.acs.length) out.push('  no acceptance lines in design.md — add `- AC1: <observable result>`');
    for (const a of s.acs) {
      out.push(`  ${a.id} [${a.state}] ${a.text.slice(0, 80)}${a.evidence.length ? ` (${a.evidence.join(', ')})` : ''}`);
      if (a.state !== 'covered') out.push(`      ${a.detail ? `${a.detail} → ` : '→ '}${a.fix}`);
    }
    const p = s.ship_precheck;
    out.push(`ship pre-check: ${p.ok ? 'athena ship would not refuse' : `athena ship would refuse (${p.blockers.length})`}${p.stage === 'ship' ? '' : ` — stage is ${p.stage || '""'}; the Stop gate enforces H2/H3 at stage=ship`}`);
    for (const b of p.blockers) out.push(`  ${b.reason}\n      → ${b.fix}`);
    if (p.uncovered.length) out.push(`  advisory (ship warns, does not refuse): no current \`--covers\` record for ${p.uncovered.join(', ')}\n      → ${RUN(p.uncovered.join(','))}`);
  }
  out.push(`issues open: ${s.issues_open}`);
  for (const x of s.exemptions) out.push(`exemption ${x.key} until ${x.until} [${x.status}]${x.why ? ` ${x.why}` : ''}`);
  out.push('exemptions: athena exemption add|list|remove');
  for (const a of s.advisories) out.push(`advisory ${a.rule}: ${a.message}`);
  io.stdout.write(`${out.join('\n')}\n`);
  return 0;
}

module.exports = { main, collect, sprintView };
