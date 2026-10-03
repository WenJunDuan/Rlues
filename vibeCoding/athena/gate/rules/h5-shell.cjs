'use strict';
// H5 shell safety (design §5.3): a danger table (union of the 9.9.9 CC and CX guards plus
// force-push to a default branch) and the push-stage rule judged by the repository pushed.
const path = require('path');
const lex = require('../lib/shell-lex.cjs');
const words = require('../lib/shell-words.cjs');
const project = require('../lib/git-project.cjs');
const context = require('../lib/context.cjs');

const SHELLS = new Set(['bash', 'sh', 'zsh', 'dash', 'ksh']);
const DB_CLIENTS = new Set(['mysql', 'psql', 'sqlite3', 'mariadb']);
// A push of this project is allowed only here; every other (or unknown) stage has code in flight.
const PUSH_OK_STAGES = new Set(['', 'ship', 'brainstorm', 'roadmap']);
// The evidence ledger and review.json are written by athena itself. This catches the plain
// shell forms (redirect, tee, cp/mv/install/ln destination, sed -i, dd of=); interpreter
// one-liners (node -e / python -c) are a declared gap — integrity against accidents, not a sandbox.
const LEDGER = /(?:\.runtime\/evid[^/\s'"]*\/|(?:^|\/)review\.json$|\/review\.json['"]?$)/;
const LEDGER_REDIRECT = /[0-9]?>>?\|?\s*['"]?[^\s;&|'"]*(?:\.runtime\/evid[^\s;&|'"]*|\/review\.json)\b/;

/** The narrow heredoc of a command, or null; a lexer failure means "analyze as before". */
function narrowHeredoc(command) {
  try { return lex.simpleHeredoc(command); } catch (_) { return null; }
}

/** Command text bash actually executes: quoted narrow heredoc body masked, comments stripped. */
function activeText(command) {
  const heredoc = narrowHeredoc(command);
  let active = command;
  const heredocs = [];
  // Extend the same closed data-consumer grammar to complete top-level lines after
  // ordinary commands. Never cross quotes, continuations, grouping or unknown heredocs.
  let quote = '', escaped = false, lineStart = 0;
  for (let i = 0; i < active.length; i += 1) {
    const ch = active[i];
    if (escaped) { escaped = false; continue; }
    if (ch === '\\' && quote !== "'") { escaped = true; continue; }
    if (quote) { if (ch === quote) quote = ''; continue; }
    if (ch === "'" || ch === '"') { quote = ch; continue; }
    if (ch !== '\n') continue;
    const line = active.slice(lineStart, i);
    const segments = lex.scan(line);
    const header = segments.length ? segments[segments.length - 1].text : '';
    if (line.includes('<<')) {
      const prefix = line.slice(0, line.length - header.length);
      const span = !/[(){}\\`]|\$\(|<</.test(prefix) ? narrowHeredoc(header + active.slice(i)) : null;
      if (!span) break; // unknown shell input remains fully visible
      const offset = i - header.length;
      const body = { start: offset + span.start, end: offset + span.end, quoted: span.quoted };
      heredocs.push(body);
      const close = active.indexOf('\n', body.end);
      const end = close < 0 ? active.length : close;
      active = words.maskBody(active, { start: body.start, end }); // delimiter is data too
      i = end - 1;
    }
    lineStart = i + 1;
  }
  return { heredoc, heredocs, masked: active, active: words.stripComments(active) };
}

/** Does a parsed command write a ledger path (as its destination, not as a source)? */
function writesLedger(item) {
  const values = item.args.map(token => token.value);
  const plain = values.filter(v => !v.startsWith('-'));
  if (['cp', 'mv', 'install', 'ln', 'rsync'].includes(item.name)) {
    if (plain.length < 2) return false;
    const dest = plain[plain.length - 1].replace(/\/+$/, '');
    const sources = plain.slice(0, -1).map(v => path.basename(v));
    return LEDGER.test(dest) || (/(?:^|\/)\.ai_state\/sprints\/[^/]+$/.test(dest) && sources.includes('review.json'))
      || (/\.runtime\/evid[^/]*$/.test(dest) && sources.some(s => s.endsWith('.jsonl')));
  }
  if (item.name === 'git' && ['checkout', 'restore'].includes(words.gitSubcommand(item.args))) return plain.some(v => LEDGER.test(v));
  if (['curl', 'wget'].includes(item.name)) return values.some(v => !v.includes('://') && LEDGER.test(v.replace(/^--output(?:-document)?=/, '')));
  if (item.name === 'tee') return plain.some(v => LEDGER.test(v));
  if (item.name === 'sed' && values.some(v => /^-[A-Za-z]*i/.test(v) || v.startsWith('--in-place'))) return plain.some(v => LEDGER.test(v));
  if (item.name === 'dd') return values.some(v => v.startsWith('of=') && LEDGER.test(v.slice(3)));
  return false;
}

function hasRecursiveForce(args) {
  const values = args.map(token => token.value);
  const flags = values.filter(v => /^-[A-Za-z]+$/.test(v)).join('');
  const recursive = /[rR]/.test(flags) || values.includes('--recursive');
  return recursive && (flags.includes('f') || values.includes('--force'));
}

/** Index of the script argument after a -c style flag (-c, -ec, -xc, -lc …), or -1. */
function scriptIndex(values) {
  const i = values.findIndex(v => /^-[A-Za-z]*c[A-Za-z]*$/.test(v));
  if (i < 0) return -1;
  let j = i + 1;
  while (j < values.length && /^[-+][A-Za-z]+$/.test(values[j])) j += 1; // bash -c -e 'script'
  return j < values.length ? j : -1;
}

function normalizeTarget(value) {
  let normalized = value.replace(/\/{2,}/g, '/');
  let previous;
  do {
    previous = normalized;
    normalized = normalized.replace(/\/(?:\*\*|\*|\.)$/, '');
  } while (normalized !== previous && normalized.length);
  if (normalized.length > 1) normalized = normalized.replace(/\/$/, '');
  return normalized || '/';
}

function dangerousTarget(value) {
  const normalized = normalizeTarget(value);
  return ['/', '~', '$HOME', '${HOME}'].includes(normalized) || normalized.startsWith('$HOME/') || normalized.startsWith('${HOME}/');
}

const DEFAULT_REF = /(?:^|:)(?:refs\/heads\/)?(?:main|master)$/;

/** {force, refs, deletes}: force = --force / -f / --force-with-lease / +refspec. */
function pushShape(values) {
  const force = values.some(v => v === '--force' || /^--force-with-lease(?:=|$)/.test(v) || /^-[a-zA-Z]*f[a-zA-Z]*$/.test(v));
  const refs = values.filter(v => !v.startsWith('-')).slice(1);
  const deleting = values.includes('--delete') || values.includes('-d');
  return { force: force || refs.some(v => v.startsWith('+')), refs, deleting };
}

/** Explicit rewrite/removal of main/master (branch-independent part of the rule). */
function forcePushToDefault(values) {
  const { force, refs, deleting } = pushShape(values);
  if (refs.some(v => /^:(?:refs\/heads\/)?(?:main|master)$/.test(v))) return true;
  if (deleting && refs.some(v => /^(?:refs\/heads\/)?(?:main|master)$/.test(v))) return true;
  return force && refs.some(v => DEFAULT_REF.test(v.replace(/^\+/, '')));
}

function heredocSubstitutions(body) {
  const spans = [];
  for (let i = 0; i < body.length; i += 1) {
    if (body[i] === '\\' && /[$`\\\n]/.test(body[i + 1] || '')) { i += 1; continue; }
    if (body[i] !== '`' && body.slice(i, i + 2) !== '$(') continue;
    const span = words.findSubstitutions(body.slice(i))[0];
    if (!span) continue;
    spans.push({ ...span, start: i + span.start, end: span.end < 0 ? -1 : i + span.end });
    if (span.end < 0) break;
    i += span.end - 1;
  }
  return spans;
}

function commandPrefix(parsed, index) {
  const q = value => "'" + value.replace(/'/g, "'\\''") + "'";
  return parsed.slice(0, index).map(item => item.segment.words.map(t => q(t.value)).join(' ') + (item.segment.after || '')).join(' ');
}

function analyzeSubstitutions(command, depth, heredocBody = false) {
  const pushes = [];
  for (const span of (heredocBody ? heredocSubstitutions(command) : words.findSubstitutions(command))) {
    if (span.end < 0) return { danger: 'unparsable command substitution' };
    const nested = analyze(span.inner, depth + 1);
    if (nested.danger) return nested;
    for (const push of nested.pushes || []) pushes.push({ ...push, contexts: [...(heredocBody ? [] : [command.slice(0, span.start)]), ...(push.contexts || [])] });
  }
  return { pushes };
}

/** {danger} | {push, allowPush} | {} for one command string. */
function analyze(command, depth = 0) {
  if (depth > 2) return { danger: 'nested shell depth exceeds policy' };
  const { heredocs, masked, active } = activeText(command);
  if (/:\s*\(\s*\)\s*\{[^}]*:\s*\|\s*:/.test(active)) return { danger: 'fork bomb' };
  if (LEDGER_REDIRECT.test(active)) return { danger: 'shell write to the evidence ledger or review.json (only athena writes them)' };
  const substitution = analyzeSubstitutions(active, depth);
  if (substitution.danger) return substitution;
  const pushes = [...substitution.pushes];
  // An unquoted body is expanded by bash: scan it on its own as well (findings only added).
  for (const span of heredocs.filter(h => !h.quoted)) {
    const body = analyzeSubstitutions(command.slice(span.start, span.end), depth, true);
    if (body.danger) return body;
    pushes.push(...body.pushes.map(p => ({ ...p, contexts: [words.stripComments(masked.slice(0, span.start)), ...(p.contexts || [])] })));
  }
  const parsed = words.parse(active);
  let pushIndex = 0;
  for (let itemIndex = 0; itemIndex < parsed.length; itemIndex += 1) {
    const item = parsed[itemIndex];
    const name = item.name;
    const values = item.args.map(token => token.value);
    if (item.forwarded !== null && item.forwarded !== undefined) {
      const nested = analyze(item.forwarded, depth + 1);
      if (nested.danger) return nested;
      pushes.push(...(nested.pushes || []).map(p => ({ ...p, contexts: [commandPrefix(parsed, itemIndex + 1), ...(p.contexts || [])] })));
      continue;
    }
    if (writesLedger(item)) return { danger: 'shell write to the evidence ledger or review.json (only athena writes them)' };
    if (name === 'rm' && hasRecursiveForce(item.args) && values.some(dangerousTarget)) return { danger: 'recursive force removal of root/home' };
    if (name === 'dd' && values.some(value => /^of=\/dev\/(?:sd|nvme|xvd|disk)/.test(value))) return { danger: 'raw block-device write' };
    if (DB_CLIENTS.has(name) && /\bdrop\s+(?:table|database)\b/i.test(values.join(' '))) return { danger: 'DROP TABLE through database client' };
    if (SHELLS.has(name)) {
      const c = scriptIndex(values);
      if (c >= 0) {
        const nested = analyze(values[c], depth + 1);
        if (nested.danger) return nested;
        pushes.push(...(nested.pushes || []).map(p => ({ ...p, contexts: [commandPrefix(parsed, itemIndex + 1), ...(p.contexts || [])] })));
      }
    }
    if (name === 'git' && words.gitSubcommand(item.args) === 'push') {
      const pushArgs = values.slice(values.indexOf('push') + 1);
      if (forcePushToDefault(pushArgs)) return { danger: 'force push to default branch' };
      const shape = pushShape(pushArgs);
      pushes.push({ command: active, index: pushIndex++, allowPush: item.env.ATHENA_ALLOW_PUSH === '1', force: shape.force && shape.refs.every(v => /^\+?HEAD$/.test(v)) });
    }
  }
  for (let i = 0; i + 1 < parsed.length; i += 1) {
    if (parsed[i].segment.after === '|' && ['curl', 'wget'].includes(parsed[i].name) && SHELLS.has(parsed[i + 1].name)) {
      return { danger: 'network response piped to shell' };
    }
  }
  return pushes.length ? { push: true, allowPush: pushes.every(p => p.allowPush), pushes } : {};
}

/**
 * {ctx, dir} of the project a push targets; ctx null when that repository has no .ai_state.
 * The session cwd is the strict fallback; a Codex workdir only acts as a leading `cd`.
 */
function pushProjects(push, cwd, start, ctx) {
  let dirs = [start];
  for (const prefix of push.contexts || []) {
    const targets = dirs.map(dir => project.pushTarget(prefix, cwd, dir, 0, true));
    if (targets.some(t => t.uncertain)) return [{ uncertain: true }];
    dirs = [...new Set(targets.flatMap(t => t.dirs || [t.dir]))];
  }
  const targets = dirs.map(dir => project.pushTarget(push.command, cwd, dir, push.index));
  if (targets.some(t => t.uncertain)) return [{ uncertain: true }];
  return targets.flatMap(target => (target.dirs || [target.dir]).map(dir => ({
    ctx: dir === cwd || project.sameProject(dir, cwd, target.dest) ? ctx : context.load(dir), dir,
  })));
}

/** Hard gate. ev.tool === 'bash' at pre_tool. */
function check(ev, ctx) {
  const command = String(ev.command || '');
  if (!command) return null;
  const verdict = analyze(command);
  if (verdict.danger) return { rule: 'H5', reason: `H5 shell safety: ${verdict.danger}` };
  for (const push of verdict.pushes || []) {
    if (push.allowPush) continue;
    const cwd = path.resolve(ev.cwd);
    for (const target of pushProjects(push, cwd, ev.workdir ? path.resolve(ev.workdir) : cwd, ctx)) {
      if (target.uncertain) return { rule: 'H5', reason: 'H5 push: target repository is unresolved; entire command was not executed. Use an explicit git -C repository.' };
      const { ctx: owner, dir } = target;
      if (push.force && /^(?:main|master)$/.test(context.git(dir, ['symbolic-ref', '--short', 'HEAD']) || '')) {
        return { rule: 'H5', reason: 'H5 shell safety: force push while main/master is checked out' };
      }
      if (owner && (owner.invalid || !PUSH_OK_STAGES.has(owner.stage))) {
        const why = owner.invalid ? `state unknown (${owner.invalid})` : `stage=${owner.stage}`;
        return { rule: 'H5', reason: `H5 push: ${why}; pushing this project waits for ship (or idle). Unrelated repositories are judged by their own stage; entire command was not executed. Split the push into a separate tool call.` };
      }
    }
  }
  return null;
}

module.exports = { check, analyze, activeText, PUSH_OK_STAGES };
