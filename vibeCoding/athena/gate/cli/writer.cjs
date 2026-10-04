'use strict';
// athena writer dispatch | collect | status: the external-writer window (grok / codex CLIs the
// main agent runs itself). This prepares and collects; it never launches the tool — those CLIs'
// flags and output formats are not stable. Merging is probe + fast-forward only: a conflict or
// a non-ff merge is handed back to the main agent, never resolved here.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const { requireCtx, flags, UsageError } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const { idle, SAFE_SLUG } = require('../lib/context.cjs');

const USAGE = `usage:
  athena writer dispatch --tool <name> --family <anthropic|openai|xai|…> [--model <m>] [--brief <file>] [--branch <name>]
  athena writer collect [--keep-worktree]
  athena writer status [--json]`;
const DISPATCH = 'athena writer dispatch --tool <name> --family <family>';

/** A refusal: exit code + the command that moves things forward (every non-zero exit names one). */
class Refusal extends Error {
  constructor(message, next, code = 1) { super(message); this.next = next; this.code = code; }
}

/** git with its exit status and stderr (context.git folds every failure into null). */
function git(dir, args) {
  const run = spawnSync('git', ['-C', dir, ...args], { encoding: 'utf8', timeout: 60000, maxBuffer: 64 * 1024 * 1024 });
  return { status: run.status, out: String(run.stdout || '').trim(), err: String(run.stderr || '').trim() };
}

const recordFile = (ctx) => path.join(ctx.sprintDir, 'external-writer.json');
const indexFile = (ctx) => path.join(ctx.aiState, '_index.md');
const save = (ctx, rec) => fs.writeFileSync(recordFile(ctx), `${JSON.stringify(rec, null, 2)}\n`, 'utf8');

function load(ctx) {
  let text;
  try { text = fs.readFileSync(recordFile(ctx), 'utf8'); } catch (_) { return null; }
  try { return JSON.parse(text); } catch (error) {
    throw new Refusal(`${path.relative(ctx.mainRoot, recordFile(ctx))} is not valid JSON (${error.message})`, 'athena writer status');
  }
}

function sprintCtx(io) {
  const ctx = requireCtx(io);
  if (ctx.invalid) throw new Refusal(`project state unknown (${ctx.invalid}); fix .ai_state/_index.md`, 'athena status');
  if (idle(ctx) || !ctx.sprintDir || !fs.existsSync(ctx.sprintDir)) throw new Refusal('no sprint in flight', 'athena sprint start <roadmap>/<item>');
  return ctx;
}

function rules(rec) {
  return [
    '--- paste into the writer brief ---',
    `- Work only inside the worktree ${rec.worktree} (branch ${rec.branch}, base ${rec.base_commit.slice(0, 12)}).`,
    '- Commit your work on that branch. Do not push, do not switch branches, do not touch other worktrees.',
    '- Do not create or edit anything under .ai_state/ (state, evidence and review receipts belong to the main repo).',
    '- Your own test runs are not evidence: the main repo re-runs every check with `athena run` after collection.',
    '- Report: commits made, files changed, checks you ran and their real exit codes, anything left undone.',
    '--- end ---',
  ].join('\n');
}

function dispatch(argv, io) {
  const { flags: f, rest } = flags(argv, { tool: 'str', family: 'str', model: 'str', brief: 'str', branch: 'str' });
  if (rest.length || !f.tool || !f.family) throw new UsageError(USAGE);
  if (!SAFE_SLUG.test(f.tool)) throw new UsageError(`--tool "${f.tool}" must be a plain name (letters, digits, . _ -)`);
  if (!/^[a-z][a-z0-9_-]*$/.test(f.family)) throw new UsageError(`--family "${f.family}" must be a lowercase family name (anthropic, openai, xai, …)`);
  const ctx = sprintCtx(io);
  const prior = load(ctx);
  if (prior && prior.status === 'dispatched') {
    throw new Refusal(`a writer dispatch is already open for ${ctx.sprint} (${prior.tool}, branch ${prior.branch})`, 'athena writer collect');
  }
  let brief;
  if (f.brief) {
    try { brief = crypto.createHash('sha256').update(fs.readFileSync(path.resolve(io.cwd, f.brief))).digest('hex'); }
    catch (error) { throw new UsageError(`--brief ${f.brief}: ${error.message}`); }
  }
  const head = git(ctx.root, ['rev-parse', '--verify', '--quiet', 'HEAD^{commit}']);
  if (head.status !== 0) throw new Refusal('the repository has no commit to branch from', 'git commit');
  const branch = f.branch || `writer/${ctx.sprint}-${f.tool}`;
  if (git(ctx.root, ['check-ref-format', '--branch', branch]).status !== 0) throw new UsageError(`--branch "${branch}" is not a valid branch name`);
  if (git(ctx.root, ['rev-parse', '--verify', '--quiet', `refs/heads/${branch}`]).status === 0) {
    throw new Refusal(`branch ${branch} already exists`, `athena writer dispatch --tool ${f.tool} --family ${f.family} --branch <new-name>`);
  }
  // A sibling of the main checkout, never nested in it: a nested worktree's files would sit
  // inside the main repo's tree (untracked noise, tree-sha drift, H1 path confusion).
  const worktree = path.join(`${ctx.mainRoot}-wt`, `${ctx.sprint}-${f.tool}`);
  if (fs.existsSync(worktree)) throw new Refusal(`${worktree} already exists`, `git -C ${ctx.mainRoot} worktree list`);
  fs.mkdirSync(path.dirname(worktree), { recursive: true });
  const added = git(ctx.root, ['worktree', 'add', '-q', '-b', branch, worktree, head.out]);
  if (added.status !== 0) throw new Refusal(`git worktree add failed: ${added.err}`, `git -C ${ctx.mainRoot} worktree list`);
  const before = ctx.index.parallel_writers;
  const during = Math.max(2, Number(before) || 1);
  const rec = {
    schema: 1, external: true, status: 'dispatched', sprint: ctx.sprint,
    tool: f.tool, family: f.family, model: f.model || '',
    base_commit: head.out, branch, worktree, target: ctx.root,
    target_ref: git(ctx.root, ['symbolic-ref', '-q', 'HEAD']).out,
    ...(brief ? { brief_sha256: brief } : {}),
    parallel_writers_before: before === undefined ? null : before,
    dispatched_at: new Date().toISOString(),
    // earlier windows of this sprint stay on record (flattened, newest last)
    ...(prior ? { previous: [...(prior.previous || []), { ...prior, previous: undefined }] } : {}),
  };
  save(ctx, rec);
  // ≥2 switches H4 on for the window: the main agent's own writer sub-agents must be isolated
  // while a second writer is live.
  state.setFields(indexFile(ctx), { parallel_writers: during });
  io.stdout.write(`writer dispatched: ${f.tool} (${f.family}${f.model ? `, ${f.model}` : ''})\n  worktree: ${worktree}\n  branch:   ${branch}\n  base:     ${head.out}\n  record:   ${path.relative(ctx.mainRoot, recordFile(ctx))}\n  parallel_writers: ${before === undefined ? '(unset)' : before} → ${during}\n${rules(rec)}\nwhen the writer has committed: athena writer collect\n`);
  return 0;
}

/**
 * Conflicted paths of merging `theirs` into `ours`, without touching any working tree.
 * git ≥ 2.38: merge-tree --write-tree (exit 0 clean, 1 conflicts). Older git: the three-argument
 * form, whose output carries conflict markers. null = could not probe.
 */
function conflicts(dir, ours, theirs) {
  const modern = git(dir, ['merge-tree', '--write-tree', '--name-only', '--no-messages', ours, theirs]);
  if (modern.status === 0) return [];
  if (modern.status === 1) return modern.out.split('\n').slice(1).filter(Boolean);
  const base = git(dir, ['merge-base', ours, theirs]);
  if (base.status !== 0) return null;
  const legacy = git(dir, ['merge-tree', base.out, ours, theirs]);
  if (legacy.status !== 0) return null;
  const files = [];
  for (const block of legacy.out.split(/^(?=\S)/m)) {
    if (!/^\+<<<<<<< /m.test(block)) continue;
    const m = block.match(/^\s+(?:our|their|base)\s+\d+ [0-9a-f]+ (.+)$/m);
    files.push(m ? m[1] : '(unnamed path)');
  }
  return files;
}

function collect(argv, io) {
  const { flags: f, rest } = flags(argv, { 'keep-worktree': 'bool' });
  if (rest.length) throw new UsageError(USAGE);
  const ctx = sprintCtx(io);
  const rec = load(ctx);
  if (!rec) throw new Refusal(`no external writer recorded for ${ctx.sprint}`, DISPATCH);
  if (rec.status !== 'dispatched') throw new Refusal(`the writer record is already ${rec.status} (head ${String(rec.head || '').slice(0, 12)})`, 'athena writer status');
  const target = rec.target; // merge only into the checkout and branch that dispatched
  if (!target || !fs.existsSync(target)) throw new Refusal('dispatch target checkout no longer exists', 'athena writer status');
  if (git(target, ['symbolic-ref', '-q', 'HEAD']).out !== rec.target_ref) {
    throw new Refusal('target branch changed since dispatch; nothing merged',
      `git -C ${target} switch ${rec.target_ref ? rec.target_ref.replace(/^refs\/heads\//, '') : `--detach ${rec.base_commit}`}`);
  }
  const again = 'athena writer collect';
  const tip = git(target, ['rev-parse', '--verify', '--quiet', `refs/heads/${rec.branch}^{commit}`]);
  if (tip.status !== 0) throw new Refusal(`writer branch ${rec.branch} does not exist`, `git -C ${target} branch --list`);
  const commits = git(target, ['rev-list', '--reverse', `${rec.base_commit}..${tip.out}`]).out.split('\n').filter(Boolean);
  if (!commits.length) throw new Refusal(`writer branch ${rec.branch} has no commit beyond base ${String(rec.base_commit).slice(0, 12)} (the writer must commit in ${rec.worktree})`, `git -C ${rec.worktree} status`);
  const live = fs.existsSync(rec.worktree);
  const dirty = live ? git(rec.worktree, ['status', '--porcelain']).out : '';
  // `git worktree remove` would refuse later, after the merge — check before anything changes.
  if (dirty && !f['keep-worktree']) {
    throw new Refusal(`writer worktree has uncommitted changes:\n${dirty.split('\n').slice(0, 20).map(l => `  ${l}`).join('\n')}`,
      `git -C ${rec.worktree} status   (commit them there, or athena writer collect --keep-worktree)`);
  }
  const head = git(target, ['rev-parse', 'HEAD']).out;
  const ancestor = (a, b) => git(target, ['merge-base', '--is-ancestor', a, b]).status === 0;
  let how;
  if (ancestor(tip.out, head)) how = 'already-merged'; // the main agent ran the --no-ff merge itself
  else if (ancestor(head, tip.out)) {
    // Only the delta about to be merged matters: a rebase may inherit the main agent's state commits.
    const stateDelta = git(target, ['diff', '--name-only', head, tip.out, '--', '.ai_state']);
    if (stateDelta.status !== 0 || stateDelta.out) {
      throw new Refusal(`writer changes main-owned .ai_state; nothing merged:\n${stateDelta.out || stateDelta.err}`,
        `restore .ai_state in ${rec.worktree} to the target HEAD, commit the correction, then ${again}`);
    }
    const merged = git(target, ['merge', '--ff-only', '-q', rec.branch]);
    if (merged.status !== 0) {
      throw new Refusal(`git merge --ff-only ${rec.branch} failed (nothing merged): ${merged.err}`,
        `git -C ${target} status   (clear the local changes it names, then ${again})`);
    }
    how = 'ff';
  } else {
    const files = conflicts(target, head, tip.out);
    if (files === null) {
      throw new Refusal(`could not probe the merge of ${rec.branch} (git merge-tree unavailable); nothing changed`,
        `git -C ${target} merge --no-ff --no-commit ${rec.branch}   (inspect, then commit or git merge --abort; then ${again})`);
    }
    if (files.length) {
      throw new Refusal(`merging ${rec.branch} into ${head.slice(0, 12)} conflicts in ${files.length} file(s); nothing changed:\n${files.map(p => `  ${p}`).join('\n')}\nresolve by hand: rebase the writer branch in its worktree, or merge and resolve in the main repo`,
        `git -C ${rec.worktree} rebase ${head.slice(0, 12)}   (then ${again})`);
    }
    const merge = `git -C ${target} merge --no-ff ${rec.branch}`;
    // git refuses a real merge over a dirty index, and `athena sprint start` leaves state staged.
    const staged = git(target, ['diff', '--cached', '--quiet']).status === 1;
    throw new Refusal(`${rec.branch} merges cleanly but not as a fast-forward (the main branch moved since dispatch); athena does not create merge commits`,
      staged ? `git -C ${target} status   (commit staged state together with implementation; then ${merge}; then ${again})` : `${merge}   (then ${again})`);
  }
  let removed = false;
  let note = '';
  if (live && !f['keep-worktree']) {
    const rm = git(target, ['worktree', 'remove', rec.worktree]);
    removed = rm.status === 0;
    if (!removed) note = `  worktree not removed (${rm.err}); remove it with: git -C ${target} worktree remove ${rec.worktree}\n`;
    else { try { fs.rmdirSync(path.dirname(rec.worktree)); } catch (_) { /* other writers' worktrees live there */ } }
  }
  // setFields cannot delete a key; an absent parallel_writers reads as 1, so 1 restores it.
  const restored = rec.parallel_writers_before === null || rec.parallel_writers_before === undefined ? 1 : rec.parallel_writers_before;
  state.setFields(indexFile(ctx), { parallel_writers: restored });
  save(ctx, { ...rec, status: 'collected', merge: how, commits, head: tip.out, collected_at: new Date().toISOString(), worktree_removed: removed });
  io.stdout.write(`writer collected: ${commits.length} commit(s) from ${rec.branch} (${how}), head ${tip.out.slice(0, 12)}\n  parallel_writers restored to ${restored}\n  worktree ${removed ? 'removed' : 'kept'}: ${rec.worktree} (branch ${rec.branch} kept)\n${note}next steps:\n  1. re-run every check in the main repo — the writer's own runs are not evidence:\n       athena run --covers <ACn> -- <test/typecheck/build command>\n  2. athena status            (AC matrix + ship pre-check)\n  3. athena review prepare    (writer family is ${rec.family}: use a reviewer from a different family and record it with \`athena review accept --family\`)\n`);
  return 0;
}

function status(argv, io) {
  const { flags: f, rest } = flags(argv, { json: 'bool' });
  if (rest.length) throw new UsageError(USAGE);
  const ctx = sprintCtx(io);
  const rec = load(ctx);
  if (f.json) { io.stdout.write(`${JSON.stringify(rec, null, 2)}\n`); return 0; }
  if (!rec) { io.stdout.write(`no external writer recorded for ${ctx.sprint}\n  start one: ${DISPATCH}\n`); return 0; }
  const out = [`writer ${rec.tool} (${rec.family}${rec.model ? `, ${rec.model}` : ''}) [${rec.status}]`,
    `  branch ${rec.branch}  base ${String(rec.base_commit).slice(0, 12)}${rec.head ? `  head ${String(rec.head).slice(0, 12)}` : ''}`,
    `  worktree ${rec.worktree}${fs.existsSync(String(rec.worktree)) ? '' : ' (gone)'}`,
    `  dispatched ${rec.dispatched_at}${rec.collected_at ? `  collected ${rec.collected_at} (${(rec.commits || []).length} commits, ${rec.merge})` : ''}`];
  if (rec.brief_sha256) out.push(`  brief sha256 ${rec.brief_sha256}`);
  if (rec.status === 'dispatched') {
    out.push(`  parallel_writers now ${ctx.parallelWriters} (was ${rec.parallel_writers_before === null ? 'unset' : rec.parallel_writers_before})`,
      '  when the writer has committed: athena writer collect');
  }
  io.stdout.write(`${out.join('\n')}\n`);
  return 0;
}

function main(argv, io) {
  const [sub, ...rest] = argv;
  const table = { dispatch, collect, status };
  if (!table[sub]) { io.stderr.write(`${USAGE}\nnext: ${DISPATCH}\n`); return 2; }
  try { return table[sub](rest, io); } catch (error) {
    if (error instanceof Refusal) { io.stderr.write(`athena writer ${sub}: ${error.message}\nnext: ${error.next}\n`); return error.code; }
    if (error instanceof UsageError) {
      const text = error.message === USAGE ? USAGE : `athena writer ${sub}: ${error.message}\n${USAGE}`;
      const next = /athena init/.test(error.message) ? 'athena init' : (sub === 'dispatch' ? DISPATCH : `athena writer ${sub}`);
      io.stderr.write(`${text}\nnext: ${next}\n`);
      return 2;
    }
    throw error;
  }
}

module.exports = { main };
