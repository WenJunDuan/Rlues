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
  out.push(`issues open: ${s.issues_open}`);
  for (const x of s.exemptions) out.push(`exemption ${x.key} until ${x.until} [${x.status}]${x.why ? ` ${x.why}` : ''}`);
  for (const a of s.advisories) out.push(`advisory ${a.rule}: ${a.message}`);
  io.stdout.write(`${out.join('\n')}\n`);
  return 0;
}

module.exports = { main, collect };
