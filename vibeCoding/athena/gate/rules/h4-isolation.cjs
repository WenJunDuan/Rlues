'use strict';
// H4 red-zone writer isolation (design §5.3): on Refactor/System, or with parallel_writers ≥ 2,
// a writer sub-agent must run isolated (CC isolation: worktree; any platform: a task that
// names a registered non-main worktree as `worktree: /abs/path`).
const path = require('path');
const { git, inside } = require('../lib/context.cjs');
const exemptions = require('../lib/exemptions.cjs');

const RED = new Set(['Refactor', 'System']);
const DECLARATION = /\bworktree\s*[:=]\s*['"]?(\/[^\s'"]+)/i;
const READ_ONLY_TYPES = new Set(['explore', 'explorer', 'plan', 'reviewer', 'claude-code-guide', 'statusline-setup']);
const REUSES_IMPL_WORKTREE = new Set(['polish-worker', 'polish_worker']);

/** Registered worktrees other than the main one. */
function linkedWorktrees(cwd) {
  const out = git(cwd, ['worktree', 'list', '--porcelain']) || '';
  return [...out.matchAll(/^worktree (.+)$/gm)].map(m => path.resolve(m[1])).slice(1);
}

function declaredIsolation(task, cwd) {
  const m = String(task || '').match(DECLARATION);
  if (!m) return false;
  const declared = path.resolve(m[1].replace(/^~(?=\/)/, process.env.HOME || '~'));
  return linkedWorktrees(cwd).some(root => inside(declared, root));
}

/** writer: true | false. A definition (ev.agent.def) decides; without one only known read-only built-ins are exempt. */
function isWriter(agent) {
  const def = agent.def;
  if (!def) return !READ_ONLY_TYPES.has(String(agent.type || '').toLowerCase()); // built-ins: only known read-only names are exempt
  if (def.sandbox) return def.sandbox !== 'read-only';
  if (def.tools !== undefined && def.tools !== '') return /\b(write|edit|multiedit|notebookedit|apply_patch)\b/i.test(String(def.tools));
  return true; // no tools list = inherits every tool
}

function check(ev, ctx) {
  if (!ctx || !ev.agent) return { verdict: null };
  const red = RED.has(ctx.path) || Boolean(ctx.invalid);
  const parallel = ctx.parallelWriters >= 2;
  if (!red && !parallel) return { verdict: null };
  const agent = ev.agent;
  if (REUSES_IMPL_WORKTREE.has(agent.type)) return { verdict: null, warn: 'H4: polish-worker reuses the implementation worktree' };
  if (!isWriter(agent)) return { verdict: null };
  const writeSet = Array.isArray(agent.write_set) ? agent.write_set : null;
  if (writeSet && writeSet.length) {
    const abs = writeSet.map(p => path.resolve(ev.cwd, p));
    const safe = abs.every(p => inside(p, path.join(ctx.mainRoot, '.ai_state')) || ![ctx.root, ctx.mainRoot].some(r => inside(p, r)));
    if (safe) return { verdict: null };
  }
  if (agent.isolation === 'worktree' || (agent.def && agent.def.isolation === 'worktree')) return { verdict: null };
  if (declaredIsolation(agent.task, ev.cwd)) return { verdict: null };
  for (const key of ['h4_worktree', 'harness_target_outside_repo']) {
    const hit = exemptions.active(ctx, key);
    if (hit) return { verdict: null, warn: `H4 exempt by ${key} until ${hit.entry.until}: ${hit.entry.reason}` };
  }
  const why = ctx.invalid ? `state unknown (${ctx.invalid})` : (RED.has(ctx.path) ? `path=${ctx.path}` : `parallel_writers=${ctx.parallelWriters}`);
  return {
    verdict: {
      rule: 'H4',
      reason: `H4 isolation: ${why}; writer sub-agent "${agent.type || 'unknown'}" is not isolated. CC: pass isolation: "worktree"; CX/Pi: create a worktree and put \`worktree: /abs/path\` in the task. Outside-repo work: exemption h4_worktree {key, until, reason}.`,
    },
  };
}

module.exports = { check, isWriter, declaredIsolation, linkedWorktrees };
