'use strict';
// athena ship: strict H2/H3 → runtime-read check → evidence.yaml → archive → items done →
// queue → _index idle → monthly pack → git add (never commits). Nothing is touched on refusal.
const fs = require('fs');
const path = require('path');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const archive = require('./lib/archive.cjs');
const evidence = require('../lib/evidence.cjs');
const frontmatter = require('../lib/frontmatter.cjs');
const { git, idle } = require('../lib/context.cjs');
const { tree, reviewIgnore } = require('../core.cjs');
const h1 = require('../rules/h1-design.cjs');
const h2 = require('../rules/h2-evidence.cjs');
const h3 = require('../rules/h3-review.cjs');
const advisory = require('../rules/advisory.cjs');

const yq = (v) => JSON.stringify(v === undefined || v === null ? '' : v);

function summary(ctx, criteria, valid, review) {
  const last = valid[valid.length - 1];
  const lines = [`sprint: ${yq(ctx.sprint)}`, `shipped: ${yq(new Date().toISOString())}`, `tree_sha: ${yq(ctx.tree)}`,
    `review: {run: ${yq(review && review.run)}, verdict: ${yq(review && review.verdict)}}`,
    `final: {id: ${yq(last.id)}, command: ${yq(last.command)}, kind: ${yq(last.kind)}, exit: ${last.exit}}`, 'acceptance:'];
  const uncovered = [];
  for (const ac of criteria) {
    const ids = valid.filter(r => (r.covers || []).includes(ac.id)).map(r => r.id);
    if (!ids.length) uncovered.push(ac.id);
    lines.push(`  - {id: ${ac.id}, text: ${yq(ac.text.slice(0, 160))}, evidence: ${JSON.stringify(ids)}}`);
  }
  return { text: `${lines.join('\n')}\n`, uncovered };
}

function main(argv, io) {
  let opts;
  try { opts = flags(argv, { 'dry-run': 'bool' }).flags; } catch (error) { io.stderr.write(`athena ship: ${error.message}\n`); return 2; }
  let ctx;
  try { ctx = requireCtx(io); } catch (error) { io.stderr.write(`athena ship: ${error.message}\n`); return 2; }
  if (ctx.invalid) { io.stderr.write(`athena ship: project state unknown (${ctx.invalid}); fix .ai_state/_index.md\n`); return 1; }
  if (idle(ctx) || !ctx.sprintDir) { io.stderr.write('athena ship: no sprint in flight\n'); return 1; }
  const ignore = reviewIgnore(ctx);
  const verdict = h2.check({ platform: 'cli' }, ctx, tree(ctx), ignore) || h3.check({ platform: 'cli' }, ctx, tree(ctx), ignore);
  if (verdict) { io.stderr.write(`athena ship: refused — ${verdict.reason}\n`); return 1; }
  const reads = archive.runtimeReads(ctx, `sprints/${ctx.sprint}`);
  if (reads.length) {
    io.stderr.write(`athena ship: refused — code outside .ai_state reads this sprint's path; repoint it first:\n${reads.slice(0, 20).map(r => `  ${r}`).join('\n')}\n`);
    return 1;
  }
  for (const w of advisory.run(ctx, { platform: 'cli' }, advisory.AT.ship)) io.stderr.write(`advisory ${w.rule}: ${w.message}\n`);
  const design = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8');
  const fm = frontmatter.parse(design);
  const valid = evidence.valid(ctx, ctx.tree, { anyProvableKind: ctx.path === 'Hotfix', ignore });
  const review = h3.readReview(ctx).data || null;
  const { text, uncovered } = summary(ctx, h1.criteria(design), valid, review);
  if (uncovered.length) io.stderr.write(`advisory evidence: no \`athena run --covers\` record for ${uncovered.join(', ')}\n`);
  const slug = ctx.sprint;
  const roadmap = String(fm.roadmap || '');
  const item = String(fm.item || '');
  // Every check that can fail runs before the first write (review S4 P1: no half-shipped state).
  const problems = archive.archiveProblems(ctx, slug);
  const itemsPath = roadmap && item ? state.itemsFile(ctx.aiState, roadmap) : null;
  if (itemsPath && (!fs.existsSync(itemsPath) || !state.readItems(itemsPath).items.some(it => it.slug === item))) {
    problems.push(`design names ${roadmap}/${item} but roadmap/${roadmap}/items.yaml has no such item`);
  }
  if (problems.length) { io.stderr.write(`athena ship: refused — ${problems.join('; ')}\n`); return 1; }
  const months = archive.packable(ctx).filter(name => {
    const why = archive.packProblems(ctx, name);
    for (const w of why) io.stderr.write(`advisory pack: ${w}\n`);
    return !why.length;
  });
  if (opts['dry-run']) { io.stdout.write(`dry-run: would archive ${slug}${months.length ? ` and pack ${months.join(', ')}` : ''}\n${text}`); return 0; }
  fs.writeFileSync(path.join(ctx.sprintDir, 'evidence.yaml'), text, 'utf8');
  fs.appendFileSync(path.join(ctx.sprintDir, 'log.md'), `- ${today()} shipped (evidence ${valid[valid.length - 1].id}${review ? `, review ${review.run || 'PASS'}` : ''})\n`);
  // the sprint's four tracked files (design, evidence, review receipt, log) go into the ship commit
  archive.stage(ctx, ['design.md', 'evidence.yaml', 'review.json', 'log.md'].map(n => `sprints/${slug}/${n}`));
  const touched = ['_index.md', 'queue.md'];
  if (itemsPath) {
    // `after`: the commit this ship lands on top of (ship stages, the agent commits).
    state.setItem(itemsPath, item, { status: 'done', done: { after: git(ctx.mainRoot, ['rev-parse', '--short', 'HEAD']) || '', review: (review && review.run) || '' } });
    touched.push(`roadmap/${roadmap}/items.yaml`);
  }
  const moved = archive.archiveSprint(ctx, slug);
  state.queueRemove(ctx.aiState, slug, itemsPath ? `${roadmap}/${item}` : '');
  state.setFields(path.join(ctx.aiState, '_index.md'), { path: '', stage: '', sprint: '', next_action: '', route_push: `${today()} shipped ${slug}` });
  archive.stagePaths(ctx, moved.stage);
  const packed = months.map(name => archive.pack(ctx, name));
  archive.stage(ctx, touched);
  archive.stagePaths(ctx, packed.flatMap(p => p.stage));
  io.stdout.write(`shipped ${slug} → ${moved.rel}${packed.length ? `; packed ${packed.map(p => p.rel).join(', ')}` : ''}\nstate staged; commit it together with the change.\n`);
  return 0;
}

module.exports = { main };
