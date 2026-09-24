'use strict';
// Project context for one hook event: repository roots, the .ai_state that governs the
// event, and the _index fields the rules read (v1 and v2 spellings, normalized).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const frontmatter = require('./frontmatter.cjs');

const PATHS = new Set(['Hotfix', 'Bugfix', 'Quick', 'Feature', 'Refactor', 'System']);
const STAGES = new Set(['brainstorm', 'roadmap', 'plan', 'design', 'impl', 'runtime-verify', 'polish', 'review', 'ship']);
const SAFE_SLUG = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const FLAG_DEFAULTS = {
  cc_workflows: false, cc_tasks_sync: false, grok_adapter: false,
  pi_hard_stop: true, bugfix_test_lock: true, cross_family_review: false,
};

/** stdout of `git -C dir …` (trimmed), or null on any failure. */
function git(dir, args, options = {}) {
  try {
    return execFileSync('git', ['-C', dir, ...args], {
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000, ...options,
    }).trim();
  } catch (_) { return null; }
}

/** Nearest .ai_state walking up from cwd; never crosses a git repository boundary. */
function findAiState(cwd) {
  let current = path.resolve(cwd);
  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = path.join(current, '.ai_state');
    try { if (fs.statSync(candidate).isDirectory()) return candidate; } catch (_) { /* absent */ }
    if (fs.existsSync(path.join(current, '.git'))) return null;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function realpath(p) {
  try { return fs.realpathSync(p); } catch (_) { return path.resolve(p); }
}

/** Worktree top level of cwd and the main checkout that owns its git common dir. */
function roots(cwd) {
  const top = git(cwd, ['rev-parse', '--show-toplevel']);
  if (!top) return { root: null, mainRoot: null };
  const common = git(cwd, ['rev-parse', '--git-common-dir']);
  let mainRoot = top;
  if (common) {
    const abs = realpath(path.resolve(cwd, common));
    if (path.basename(abs) === '.git') mainRoot = path.dirname(abs);
  }
  return { root: realpath(top), mainRoot: realpath(mainRoot) };
}

function readIndex(aiState) {
  const file = path.join(aiState, '_index.md');
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (_) { return { exists: false, fm: {}, malformed: null }; }
  if (!frontmatter.block(text)) return { exists: true, fm: {}, malformed: '_index.md has no parseable frontmatter (--- … ---)' };
  const fm = frontmatter.parse(text);
  if (!('stage' in fm) && !('path' in fm)) return { exists: true, fm, malformed: '_index.md frontmatter has neither path nor stage' };
  return { exists: true, fm, malformed: null };
}

const str = (value) => (value === undefined || value === null ? '' : String(value).trim());

/**
 * Load the context for an event. Returns null when the event is outside any Athena project
 * (no .ai_state reachable) — every rule then allows. The main checkout's .ai_state wins
 * over a worktree's checked-out copy (P3: a worktree's copy may lag).
 */
function load(cwd) {
  const local = findAiState(cwd);
  const { root, mainRoot } = roots(cwd);
  const main = mainRoot ? findAiState(mainRoot) : null;
  const aiState = main || local;
  if (!aiState) return null;
  const { exists, fm, malformed } = readIndex(aiState);
  const sprint = str(fm.sprint !== undefined ? fm.sprint : fm.current_sprint_slug);
  const stage = str(fm.stage);
  const route = str(fm.path);
  // Unknown state is never idle: the rules apply their strict branch (review S2 P1/P2).
  let invalid = malformed;
  if (!invalid && stage && !STAGES.has(stage)) invalid = `_index stage "${stage}" is not a known stage`;
  if (!invalid && route && !PATHS.has(route)) invalid = `_index path "${route}" is not a known path`;
  if (!invalid && (route || sprint) && !stage) invalid = '_index has a path/sprint but no stage';
  const flags = { ...FLAG_DEFAULTS };
  if (fm.flags && typeof fm.flags === 'object') {
    for (const [key, value] of Object.entries(fm.flags)) flags[key] = value === true || value === 'true';
  }
  return {
    cwd: path.resolve(cwd),
    root: root || path.dirname(aiState),
    mainRoot: mainRoot || path.dirname(aiState),
    aiState,
    runtime: path.join(aiState, '.runtime'),
    indexExists: exists,
    index: fm,
    schema: str(fm.schema) === 'athena-state/2' ? 2 : 1,
    path: route,
    stage,
    invalid,
    sprint: SAFE_SLUG.test(sprint) ? sprint : '',
    rawSprint: sprint,
    sprintDir: SAFE_SLUG.test(sprint) ? path.join(aiState, 'sprints', sprint) : null,
    roadmap: str(fm.roadmap !== undefined ? fm.roadmap : fm.current_roadmap_slug),
    parallelWriters: Number(fm.parallel_writers) || 1,
    exemptions: Array.isArray(fm.exemptions) ? fm.exemptions : [],
    flags,
  };
}

/** Idle = a well-formed index with no route in flight (path, stage and sprint all empty). */
function idle(ctx) {
  return !ctx.invalid && !ctx.path && !ctx.stage && !ctx.rawSprint;
}

/** Is abs inside dir (after resolving symlinks of the deepest existing ancestor)? */
function inside(abs, dir) {
  const rel = path.relative(realpath(dir), realExisting(abs));
  return rel === '' || (!rel.startsWith(`..${path.sep}`) && rel !== '..' && !path.isAbsolute(rel));
}

/** realpath of the deepest existing ancestor, with the missing tail re-appended. */
function realExisting(abs) {
  const tail = [];
  let current = path.resolve(abs);
  for (;;) {
    try { return path.join(fs.realpathSync(current), ...tail); } catch (_) { /* climb */ }
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(abs);
    tail.unshift(path.basename(current));
    current = parent;
  }
}

module.exports = { load, idle, git, findAiState, roots, inside, realExisting, PATHS, STAGES, SAFE_SLUG, FLAG_DEFAULTS };
