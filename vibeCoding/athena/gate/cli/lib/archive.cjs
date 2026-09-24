'use strict';
// Archive mechanics (ai-state-v2 §3.5): runtime-read check, move a sprint into
// archive/sprints/YYYY-MM/, pack months outside the retention window, redirect table.
// Staging rule: only files git already tracked are staged at their new paths — untracked or
// ignored files travel on disk but never become tracked (review S4 P0/P1).
const fs = require('fs');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const { git } = require('../../lib/context.cjs');

const month = (date = new Date()) => date.toISOString().slice(0, 7);
const env = () => ({ ...process.env, GIT_OPTIONAL_LOCKS: '0' });
const stateRel = (ctx, rel) => path.join(path.relative(ctx.mainRoot, ctx.aiState), rel).split(path.sep).join('/');

/** Files under a .ai_state-relative path: {tracked:[], loose:[]} (loose = untracked + ignored). */
function inventory(ctx, rel) {
  const spec = stateRel(ctx, rel);
  const list = (args) => (git(ctx.mainRoot, ['ls-files', '-z', ...args, '--', spec]) || '').split('\0').filter(Boolean);
  return { tracked: list([]), loose: [...list(['--others']), ...list(['--others', '--ignored', '--exclude-standard'])] };
}

/** Code/tests/config outside .ai_state that read `.ai_state/<rel>` (NV-D3). Throws when git grep itself fails. */
function runtimeReads(ctx, rel) {
  const needle = `.ai_state/${rel}`;
  const hits = [];
  for (const root of [...new Set([ctx.mainRoot, ctx.root])]) {
    const run = spawnSync('git', ['-C', root, 'grep', '--untracked', '-n', '-F', needle, '--', '.', ':(exclude).ai_state'], { encoding: 'utf8', env: env() });
    if (run.status === 1) continue;
    if (run.status !== 0) throw new Error(`runtime-read check failed in ${root}: ${run.stderr.trim()}`);
    hits.push(...run.stdout.split('\n').filter(Boolean).map(l => (root === ctx.mainRoot ? l : `${root}: ${l}`)));
  }
  return hits;
}

function redirect(ctx, from, to) {
  const file = path.join(ctx.aiState, 'archive', 'README.md');
  let text = '';
  try { text = fs.readFileSync(file, 'utf8'); } catch (_) {
    text = '# Archive\n\n旧路径 → 新路径（历史档正文不改，NV-D10）。\n\n| 旧路径 | 新路径 |\n|---|---|\n';
  }
  if (text.includes(`| ${from} |`)) return;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${text.endsWith('\n') ? text : `${text}\n`}| ${from} | ${to} |\n`, 'utf8');
}

const archiveRel = (slug, when = new Date()) => path.join('archive', 'sprints', month(when), slug).split(path.sep).join('/');

/** Everything that would stop archiveSprint, checked before any write. */
function archiveProblems(ctx, slug, when = new Date()) {
  const problems = [];
  if (!fs.existsSync(path.join(ctx.aiState, 'sprints', slug))) problems.push(`sprints/${slug} does not exist`);
  if (fs.existsSync(path.join(ctx.aiState, archiveRel(slug, when)))) problems.push(`${archiveRel(slug, when)} already exists`);
  return problems;
}

/**
 * After a move, files that were ignored only by a path pattern would sit un-ignored at their new
 * path (and get committed by the next `git add -A`). Keep them ignored with exact entries in
 * .ai_state/archive/.gitignore. Returns the repo-relative .gitignore path when it changed.
 */
function keepIgnored(ctx, ignoredBefore, fromRel, toRel) {
  const fromPrefix = stateRel(ctx, fromRel);
  const exposed = ignoredBefore.map(f => stateRel(ctx, toRel) + f.slice(fromPrefix.length))
    .filter(f => spawnSync('git', ['-C', ctx.mainRoot, 'check-ignore', '-q', '--', f], { env: env() }).status !== 0);
  if (!exposed.length) return null;
  const file = path.join(ctx.aiState, 'archive', '.gitignore');
  const base = stateRel(ctx, 'archive');
  const prior = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : '# kept ignored after archiving (athena)\n';
  const escape = (s) => s.replace(/[\\*?[\]!#]/g, '\\$&').replace(/ $/, '\\ ');
  const add = exposed.map(f => `/${escape(f.slice(base.length + 1))}`).filter(l => !prior.split('\n').includes(l));
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${prior}${prior.endsWith('\n') ? '' : '\n'}${add.join('\n')}${add.length ? '\n' : ''}`);
  return stateRel(ctx, 'archive/.gitignore');
}

const ignoredIn = (ctx, rel) => (git(ctx.mainRoot, ['ls-files', '-z', '--others', '--ignored', '--exclude-standard', '--', stateRel(ctx, rel)]) || '').split('\0').filter(Boolean);

/** Move sprints/<slug> (with its loose files) and its raw evidence. Returns {rel, stage: [paths]}. */
function archiveSprint(ctx, slug, when = new Date()) {
  const problems = archiveProblems(ctx, slug, when);
  if (problems.length) throw new Error(problems.join('; '));
  const from = `sprints/${slug}`;
  const rel = archiveRel(slug, when);
  const { tracked } = inventory(ctx, from);
  const ignored = ignoredIn(ctx, from);
  const src = path.join(ctx.aiState, from);
  const dest = path.join(ctx.aiState, rel);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(src, dest);
  const ignoreFile = keepIgnored(ctx, ignored, from, rel);
  const raw = path.join(ctx.runtime, 'evidence', `${slug}.jsonl`);
  if (fs.existsSync(raw)) {
    const keep = path.join(ctx.runtime, 'archive', 'evidence', `${slug}.jsonl`);
    fs.mkdirSync(path.dirname(keep), { recursive: true });
    fs.renameSync(raw, keep);
  }
  redirect(ctx, `${from}/`, `${rel}/`);
  const prefix = stateRel(ctx, from);
  const moved = tracked.map(f => stateRel(ctx, rel) + f.slice(prefix.length));
  return { rel, stage: [...tracked, ...moved, stateRel(ctx, 'archive/README.md'), ignoreFile] };
}

function hasZstd() {
  return spawnSync('zstd', ['--version'], { stdio: 'ignore' }).status === 0;
}

/** Months strictly older than the previous month (retention window: this + last month). */
function packable(ctx, now = new Date()) {
  const dir = path.join(ctx.aiState, 'archive', 'sprints');
  const floor = month(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1)));
  let names = [];
  try { names = fs.readdirSync(dir); } catch (_) { return []; }
  return names.filter(n => /^\d{4}-\d{2}$/.test(n) && n < floor).sort();
}

/** Why a month cannot be packed (loose files would end up in a tracked tarball, or be deleted). */
function packProblems(ctx, name) {
  const problems = [];
  const { loose } = inventory(ctx, `archive/sprints/${name}`);
  if (loose.length) problems.push(`archive/sprints/${name} holds untracked/ignored files (${loose.slice(0, 3).join(', ')}${loose.length > 3 ? ', …' : ''}); move them out first`);
  const base = path.join(ctx.aiState, 'archive');
  for (const ext of ['zst', 'gz']) if (fs.existsSync(path.join(base, `${name}.tar.${ext}`))) problems.push(`archive/${name}.tar.${ext} already exists`);
  return problems;
}

/** Pack tracked files only; returns {rel, stage}. Caller checked packProblems. */
function pack(ctx, name) {
  const problems = packProblems(ctx, name);
  if (problems.length) throw new Error(problems.join('; '));
  const base = path.join(ctx.aiState, 'archive');
  const zst = hasZstd();
  const out = path.join(base, `${name}.tar.${zst ? 'zst' : 'gz'}`);
  const { tracked } = inventory(ctx, `archive/sprints/${name}`);
  const sprintsRoot = path.join(base, 'sprints');
  const members = tracked.map(f => path.relative(sprintsRoot, path.join(ctx.mainRoot, f)));
  const tarEnv = { ...process.env, COPYFILE_DISABLE: '1' };
  const tar = spawnSync('tar', ['-cf', '-', '-C', sprintsRoot, '-T', '-'], { env: tarEnv, input: members.join('\n'), maxBuffer: 1 << 30 });
  if (tar.status !== 0) throw new Error(`tar failed: ${tar.stderr}`);
  if (zst) execFileSync('zstd', ['-q', '-19', '-o', out], { input: tar.stdout });
  else fs.writeFileSync(out, require('zlib').gzipSync(tar.stdout, { level: 9 }));
  fs.rmSync(path.join(sprintsRoot, name), { recursive: true, force: true });
  redirect(ctx, `archive/sprints/${name}/`, `archive/${path.basename(out)}`);
  return { rel: path.relative(ctx.aiState, out), stage: [...tracked, stateRel(ctx, path.relative(ctx.aiState, out)), stateRel(ctx, 'archive/README.md')] };
}

/** Stage exactly these repo-relative paths (additions, modifications and deletions); never commits. */
function stagePaths(ctx, paths) {
  // a pathspec that is neither on disk nor in the index makes the whole `git add` fail
  const indexed = new Set((git(ctx.mainRoot, ['ls-files', '-z']) || '').split('\0'));
  const list = [...new Set(paths)].filter(p => p && (indexed.has(p) || fs.existsSync(path.join(ctx.mainRoot, p))));
  for (let i = 0; i < list.length; i += 200) git(ctx.mainRoot, ['add', '-A', '--', ...list.slice(i, i + 200)]);
}

/** Stage state files by .ai_state-relative path (files the CLI itself wrote). */
function stage(ctx, rels) { stagePaths(ctx, rels.map(r => stateRel(ctx, r))); }

module.exports = { keepIgnored, ignoredIn, runtimeReads, archiveSprint, archiveProblems, archiveRel, packable, pack, packProblems, redirect, stage, stagePaths, stateRel, inventory, month, hasZstd };
