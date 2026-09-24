'use strict';
// athena sprint start|stage|pause|resume|drop (design §7.4, ai-state-v2 §3.3/§3.6).
const fs = require('fs');
const path = require('path');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const archive = require('./lib/archive.cjs');
const frontmatter = require('../lib/frontmatter.cjs');
const { git, idle, PATHS, STAGES, SAFE_SLUG } = require('../lib/context.cjs');

const USAGE = `usage:
  athena sprint start <roadmap>/<item> [--path P] [--slug S]
  athena sprint start --req <file> --path P --slug S
  athena sprint stage <stage>
  athena sprint pause --resume-when "<condition>"      (e.g. "after athena-10-1/s3")
  athena sprint resume <slug>
  athena sprint drop --reason "<why>"`;

function designFm(ctx, slug) {
  const file = path.join(ctx.aiState, 'sprints', slug, 'design.md');
  return { file, fm: frontmatter.parse(fs.readFileSync(file, 'utf8')) };
}

function start(argv, io) {
  const { flags: f, rest } = flags(argv, { path: 'str', slug: 'str', req: 'str' });
  const ctx = requireCtx(io);
  if (!idle(ctx)) throw new UsageError(`sprint ${ctx.sprint || '?'} is in flight (stage ${ctx.stage || '?'}); pause, drop or ship it first`);
  let roadmap = '';
  let item = '';
  let itemData = {};
  if (rest[0]) {
    [roadmap, item] = rest[0].split('/');
    if (!roadmap || !item) throw new UsageError('start takes <roadmap>/<item>');
    const found = state.readItems(state.itemsFile(ctx.aiState, roadmap)).items.find(it => it.slug === item);
    if (!found) throw new UsageError(`roadmap/${roadmap}/items.yaml has no item ${item}`);
    itemData = found.data;
    if (state.DONE.has(String(itemData.status))) throw new UsageError(`${item} is already done`);
  } else if (!f.req) throw new UsageError(USAGE);
  const route = f.path || itemData.path;
  if (!PATHS.has(route)) throw new UsageError(`--path must be one of ${[...PATHS].join(', ')}`);
  const slug = f.slug || `${today()}-${item || path.basename(String(f.req), '.md')}`;
  if (!SAFE_SLUG.test(slug)) throw new UsageError(`invalid slug ${slug}`);
  const dir = path.join(ctx.aiState, 'sprints', slug);
  if (fs.existsSync(dir)) throw new UsageError(`sprints/${slug} already exists (resume it instead)`);
  const archived = (() => { try { return fs.readdirSync(path.join(ctx.aiState, 'archive', 'sprints')).filter(m => fs.existsSync(path.join(ctx.aiState, 'archive', 'sprints', m, slug))); } catch (_) { return []; } })();
  if (archived.length) throw new UsageError(`archive/sprints/${archived[0]}/${slug} already exists; pick another --slug`);
  const req = f.req || String(itemData.req || '');
  const fields = { sprint: slug, path: route, date: today(), req, roadmap, item, base_commit: git(ctx.mainRoot, ['rev-parse', '--short', 'HEAD']) || '', title: itemData.title || slug };
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'design.md'), state.render(route === 'Bugfix' ? 'bugfix-design.md' : 'design.md', fields));
  fs.writeFileSync(path.join(dir, 'log.md'), state.render('log.md', fields));
  if (roadmap) state.setItem(state.itemsFile(ctx.aiState, roadmap), item, { status: 'active', sprint: slug });
  const created = [];
  for (const name of ['issues.md', 'queue.md']) {
    if (!fs.existsSync(path.join(ctx.aiState, name))) { fs.copyFileSync(path.join(state.templatesDir(), name), path.join(ctx.aiState, name)); created.push(name); }
  }
  const stage = route === 'Hotfix' ? 'impl' : 'design';
  state.setFields(path.join(ctx.aiState, '_index.md'), {
    path: route, stage, sprint: slug, roadmap: roadmap || undefined,
    next_action: route === 'Hotfix' ? 'fix, then athena run the check' : 'write design.md acceptance lines (- ACn:)',
    route_push: `${today()} ${route} ${roadmap ? `${roadmap}/${item}` : slug}`,
  });
  archive.stage(ctx, ['_index.md', `sprints/${slug}/design.md`, `sprints/${slug}/log.md`, ...created, ...(roadmap ? [`roadmap/${roadmap}/items.yaml`] : [])]);
  io.stdout.write(`sprint ${slug} started: path=${route} stage=${stage}\n  design: .ai_state/sprints/${slug}/design.md\n`);
  return 0;
}

function stageCmd(argv, io) {
  const target = argv[0];
  if (!STAGES.has(target)) throw new UsageError(`stage must be one of ${[...STAGES].join(', ')}`);
  const ctx = requireCtx(io);
  if (!ctx.sprint) throw new UsageError('no sprint in flight');
  state.setFields(path.join(ctx.aiState, '_index.md'), { stage: target });
  io.stdout.write(`stage: ${ctx.stage || '""'} → ${target}\n`);
  return 0;
}

function pause(argv, io) {
  const { flags: f } = flags(argv, { 'resume-when': 'str' });
  if (!f['resume-when']) throw new UsageError('pause needs --resume-when "<condition>"');
  const ctx = requireCtx(io);
  if (!ctx.sprint) throw new UsageError('no sprint in flight');
  const { file, fm } = designFm(ctx, ctx.sprint);
  const itemsPath = fm.roadmap && fm.item ? state.itemsFile(ctx.aiState, fm.roadmap) : null;
  if (itemsPath && (!fs.existsSync(itemsPath) || !state.readItems(itemsPath).items.some(it => it.slug === fm.item))) {
    throw new UsageError(`design names ${fm.roadmap}/${fm.item} but that item does not exist; fix design.md first`);
  }
  state.setFields(file, { status: 'paused', resume_when: f['resume-when'], paused_stage: ctx.stage });
  fs.appendFileSync(path.join(ctx.sprintDir, 'log.md'), `- ${today()} paused at ${ctx.stage}: resume when ${f['resume-when']}\n`);
  if (fm.roadmap && fm.item) state.setItem(state.itemsFile(ctx.aiState, fm.roadmap), fm.item, { status: 'paused', deferred: { reason: 'paused', resume_when: f['resume-when'] } });
  state.setFields(path.join(ctx.aiState, '_index.md'), { path: '', stage: '', sprint: '', next_action: `paused ${ctx.sprint}` });
  archive.stage(ctx, ['_index.md', `sprints/${ctx.sprint}/design.md`, `sprints/${ctx.sprint}/log.md`, ...(itemsPath ? [`roadmap/${fm.roadmap}/items.yaml`] : [])]);
  io.stdout.write(`paused ${ctx.sprint}\n`);
  return 0;
}

function resume(argv, io) {
  const slug = argv[0];
  const ctx = requireCtx(io);
  if (!slug || !SAFE_SLUG.test(slug)) throw new UsageError('resume <slug>');
  if (!idle(ctx)) throw new UsageError(`sprint ${ctx.sprint} is in flight; pause or ship it first`);
  if (!fs.existsSync(path.join(ctx.aiState, 'sprints', slug, 'design.md'))) throw new UsageError(`sprints/${slug}/design.md not found (archived sprints: move it back first)`);
  const { file, fm } = designFm(ctx, slug);
  const stage = STAGES.has(String(fm.paused_stage)) ? fm.paused_stage : 'impl';
  state.setFields(file, { status: 'active' });
  if (fm.roadmap && fm.item) state.setItem(state.itemsFile(ctx.aiState, fm.roadmap), fm.item, { status: 'active' });
  state.setFields(path.join(ctx.aiState, '_index.md'), { path: fm.path, stage, sprint: slug, roadmap: fm.roadmap || undefined, next_action: `resumed ${slug}` });
  fs.appendFileSync(path.join(ctx.aiState, 'sprints', slug, 'log.md'), `- ${today()} resumed at ${stage}\n`);
  io.stdout.write(`resumed ${slug} at stage ${stage}\n`);
  return 0;
}

function drop(argv, io) {
  const { flags: f } = flags(argv, { reason: 'str' });
  if (!f.reason) throw new UsageError('drop needs --reason');
  const ctx = requireCtx(io);
  if (!ctx.sprint) throw new UsageError('no sprint in flight');
  const slug = ctx.sprint;
  const { fm } = designFm(ctx, slug);
  const itemsPath = fm.roadmap && fm.item ? state.itemsFile(ctx.aiState, fm.roadmap) : null;
  const problems = [...archive.archiveProblems(ctx, slug), ...archive.runtimeReads(ctx, `sprints/${slug}`).map(h => `read by ${h}`)];
  if (itemsPath && (!fs.existsSync(itemsPath) || !state.readItems(itemsPath).items.some(it => it.slug === fm.item))) problems.push(`no item ${fm.roadmap}/${fm.item}`);
  if (problems.length) throw new UsageError(`refused — ${problems.join('; ')}`);
  fs.appendFileSync(path.join(ctx.sprintDir, 'log.md'), `- ${today()} dropped: ${f.reason}\n`);
  git(ctx.mainRoot, ['add', '--', archive.stateRel(ctx, `sprints/${slug}/log.md`)]);
  if (itemsPath) state.setItem(itemsPath, fm.item, { status: 'dropped', dropped: f.reason });
  const moved = archive.archiveSprint(ctx, slug);
  state.queueRemove(ctx.aiState, slug, itemsPath ? `${fm.roadmap}/${fm.item}` : '');
  state.setFields(path.join(ctx.aiState, '_index.md'), { path: '', stage: '', sprint: '', next_action: '', route_push: `${today()} dropped ${slug}: ${f.reason}` });
  archive.stage(ctx, ['_index.md', 'queue.md', ...(itemsPath ? [`roadmap/${fm.roadmap}/items.yaml`] : [])]);
  archive.stagePaths(ctx, moved.stage);
  io.stdout.write(`dropped ${slug} → ${moved.rel}\n`);
  return 0;
}

function main(argv, io) {
  const [sub, ...rest] = argv;
  const table = { start, stage: stageCmd, pause, resume, drop };
  if (!table[sub]) { io.stderr.write(`${USAGE}\n`); return 2; }
  try { return table[sub](rest, io); } catch (error) {
    if (error instanceof UsageError) { io.stderr.write(`athena sprint ${sub}: ${error.message}\n`); return 2; }
    throw error;
  }
}

module.exports = { main };
