'use strict';
// Which sprint owns a command or a write (quantum-links G-008/G-009/G-010/G-012/G-013): work is
// attributed by the worktree it happens in, never by "whichever sprint the main checkout has active".
//
//   target dir   = the command's cwd, moved by a leading `cd X &&|;` and by the validation's own
//                  directory option (--prefix / -C / --dir / --cwd / --manifest-path); a write's file.
//   main checkout (or no git)  → the sprint active in _index (unchanged).
//   linked worktree W          → the hot sprint (.ai_state/sprints/<slug>/, active or paused) that names W:
//     1. design.md frontmatter `worktree:` (absolute, or relative to the main checkout) is W,
//        or `branch:` is W's branch;
//     2. sprints/<slug>/external-writer.json (athena writer dispatch) has worktree W or branch W's branch;
//     3. W's branch or W's directory name contains <slug> — or <slug> without its YYYY-MM-DD- prefix —
//        as a whole token (bounded by start/end or a non [A-Za-z0-9] character).
//     Rules are tried in order; within a rule several sprints → the longest key, a tie → none.
//   no match → a worktree nested inside the main checkout keeps the active sprint; any other
//   (sibling) worktree → null: evidence is not recorded (never charged to the active sprint).
const fs = require('fs');
const os = require('os');
const path = require('path');
const context = require('./context.cjs');
const frontmatter = require('./frontmatter.cjs');
const words = require('./shell-words.cjs');

const DIR_OPTIONS = new Set(['--prefix', '-C', '--dir', '--cwd', '--manifest-path', '--rootdir']);

function realpath(p) { try { return fs.realpathSync(p); } catch (_) { return path.resolve(p); } }

/** A directory word resolved without the shell; null when it needs expansion or does not exist. */
function resolveDir(raw, base, fileOk = false) {
  if (typeof raw !== 'string' || !raw || /[$`*?]/.test(raw)) return null;
  let value = raw;
  if (value === '~' || value.startsWith('~/')) value = path.join(os.homedir(), value.slice(1));
  else if (value.startsWith('~')) return null;
  const abs = path.resolve(base, value);
  try {
    const st = fs.statSync(abs);
    if (st.isDirectory()) return abs;
    return fileOk && st.isFile() ? path.dirname(abs) : null;
  } catch (_) { return null; }
}

/** Directory the validation in `command` runs against (see header). Unresolvable parts keep cwd. */
function targetDir(command, cwd) {
  let items;
  try { items = words.parse(String(command || '')); } catch (_) { return cwd; }
  const { classifySegment } = require('./evidence.cjs');
  let base = cwd;
  for (const item of items) {
    const values = item.args.map(t => t.value);
    if (item.name === 'cd') {
      if (!['&&', ';'].includes(item.segment.after) || ['(', ')', '||'].includes(item.segment.before)) return base;
      base = resolveDir(values[0], base) || base;
      continue;
    }
    const text = item.segment.words.map(w => w.value).join(' ');
    // the validation segment; a command without one is judged by its first command
    if (!classifySegment(text) && items.some(o => o.name !== 'cd' && classifySegment(o.segment.words.map(w => w.value).join(' ')))) continue;
    for (let i = 0; i < values.length; i += 1) {
      const [flag, inline] = values[i].startsWith('--') ? values[i].split(/=(.*)/s) : [values[i], undefined];
      if (!DIR_OPTIONS.has(flag)) continue;
      const raw = inline !== undefined ? inline : values[i + 1];
      const dir = resolveDir(raw, base, flag === '--manifest-path');
      if (dir) return dir;
    }
    return base;
  }
  return base;
}

function readFm(file) {
  try { return frontmatter.parse(fs.readFileSync(file, 'utf8')); } catch (_) { return {}; }
}

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (_) { return null; }
}

const str = (v) => (v === undefined || v === null ? '' : String(v).trim());
const token = (hay, key) => {
  if (!key) return false;
  const at = (i) => i < 0 || i >= hay.length || !/[A-Za-z0-9]/.test(hay[i]);
  for (let i = hay.indexOf(key); i >= 0; i = hay.indexOf(key, i + 1)) if (at(i - 1) && at(i + key.length)) return true;
  return false;
};

/** Hot sprint slugs of ctx (sprints/<slug>/design.md present). */
function hotSprints(ctx) {
  let names = [];
  try { names = fs.readdirSync(path.join(ctx.aiState, 'sprints')); } catch (_) { return []; }
  return names.filter(n => context.SAFE_SLUG.test(n) && fs.existsSync(path.join(ctx.aiState, 'sprints', n, 'design.md'))).sort();
}

/** Pick one of [{slug, key}]: the longest key; a tie → null. */
function pick(hits) {
  if (!hits.length) return null;
  const best = Math.max(...hits.map(h => h.key.length));
  const top = [...new Set(hits.filter(h => h.key.length === best).map(h => h.slug))];
  return top.length === 1 ? top[0] : null;
}

/** Sprint slug that names worktree root `wt` (branch `branch`), or null. */
function sprintForWorktree(ctx, wt, branch) {
  const slugs = hotSprints(ctx);
  const same = (raw) => raw && realpath(path.resolve(ctx.mainRoot, raw)) === wt;
  const explicit = [];
  const writer = [];
  const named = [];
  const dirName = path.basename(wt);
  for (const slug of slugs) {
    const dir = path.join(ctx.aiState, 'sprints', slug);
    const fm = readFm(path.join(dir, 'design.md'));
    if (same(str(fm.worktree)) || (branch && str(fm.branch) === branch)) explicit.push({ slug, key: slug });
    const rec = readJson(path.join(dir, 'external-writer.json'));
    if (rec && (same(str(rec.worktree)) || (branch && str(rec.branch) === branch))) writer.push({ slug, key: slug });
    for (const key of new Set([slug, slug.replace(/^\d{4}-\d{2}-\d{2}-/, '')])) {
      if (token(branch, key) || token(dirName, key)) named.push({ slug, key });
    }
  }
  return pick(explicit) || pick(writer) || pick(named);
}

/** The context of sprint `slug` (active or paused) for work rooted at `root`. */
function sprintCtx(ctx, slug, root = ctx.root) {
  if (slug === ctx.sprint) return { ...ctx, root, tree: undefined };
  const fm = readFm(path.join(ctx.aiState, 'sprints', slug, 'design.md'));
  const stage = context.STAGES.has(str(fm.paused_stage)) ? str(fm.paused_stage) : 'impl';
  return {
    ...ctx, root, tree: undefined, sprint: slug, rawSprint: slug, sprintDir: path.join(ctx.aiState, 'sprints', slug),
    stage, path: str(fm.path), invalid: null,
  };
}

/** Linked worktree root containing `abs` (longest match; the main checkout excluded), or null. */
function linkedWorktree(ctx, abs) {
  const main = realpath(ctx.mainRoot);
  const roots = context.worktrees(ctx.mainRoot).filter(r => r !== main && context.inside(abs, r));
  return roots.sort((a, b) => b.length - a.length)[0] || null;
}

/**
 * Owner of work in `dir` for project ctx (loaded from dir): {ctx, worktree, branch, why}.
 * ctx null = not attributable (reason in why).
 */
function owner(ctx, dir) {
  if (!ctx) return { ctx: null, why: 'no .ai_state' };
  const wt = linkedWorktree(ctx, dir);
  if (!wt) return { ctx: ctx.sprint ? ctx : null, worktree: null, why: ctx.sprint ? 'main checkout' : 'no active sprint' };
  const branch = context.git(wt, ['symbolic-ref', '--short', '-q', 'HEAD']) || '';
  const slug = sprintForWorktree(ctx, wt, branch);
  // A worktree nested inside the main checkout (Claude Code `isolation: worktree` agents under
  // .claude/worktrees/) is still in the main tree: unmapped, it keeps the active sprint.
  if (!slug && ctx.sprint && context.inside(wt, ctx.mainRoot)) return { ctx: { ...ctx, root: wt, tree: undefined }, worktree: wt, branch, why: 'nested worktree' };
  if (!slug) {
    return { ctx: null, worktree: wt, branch, why: `worktree ${wt}${branch ? ` (branch ${branch})` : ''} maps to no sprint — set \`worktree:\` or \`branch:\` in that sprint's design.md frontmatter, or name the branch after the sprint slug` };
  }
  return { ctx: sprintCtx(ctx, slug, wt), worktree: wt, branch, why: `worktree ${wt} → ${slug}` };
}

module.exports = { targetDir, owner, sprintForWorktree, sprintCtx, linkedWorktree, hotSprints };
