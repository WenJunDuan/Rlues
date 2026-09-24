'use strict';
// Evidence (design §8, D5): `athena run` records real exit codes; the post_tool collector is
// the fallback with the 9.9.9 provability rules. Records live in the MAIN checkout's
// .ai_state/.runtime/evidence/<sprint>.jsonl (a reclaimed worktree loses nothing) and are
// valid only while their tree_sha equals the current source tree.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const lex = require('./shell-lex.cjs');
const words = require('./shell-words.cjs');

// Anchored at the start of a quote-aware segment (shell-lex.scan): a validation word inside
// quotes ("echo '; pytest'") is data, not a command (review S2 P1).
// Runner prefixes (npx, uv/poetry/pipenv run) and path-prefixed tools (.venv/bin/pytest,
// node_modules/.bin/jest) classify like the bare tool (review r4 P2).
// Only relative, in-repo prefixes: no leading / or ~, no .. (a tool outside the tree is not evidence).
const PREFIX = String.raw`^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*(?:npx\s+|(?:uv|poetry|pipenv|hatch)\s+run\s+)?(?:\.\/)?(?:(?!\.\.\/)\.?[\w-][\w.-]*\/)*`;
const PATTERNS = [
  ['test', String.raw`(?:python[0-9.]*\s+-m\s+(?:pytest|unittest)|pytest|jest|vitest|unittest|(?:npm|pnpm|yarn|bun)\s+(?:test|run\s+test)|cargo\s+test|go\s+test|mvn\s+(?:test|verify)|\./gradlew\s+test|node\s+--test)`],
  ['lint', String.raw`(?:eslint|prettier\s+--check|ruff|(?:npm|pnpm|yarn|bun)\s+run\s+lint|cargo\s+clippy|go\s+vet|node\s+--check|git\s+diff\s+--check)`],
  ['typecheck', String.raw`(?:tsc|(?:npm|pnpm|yarn|bun)\s+run\s+(?:typecheck|check)|cargo\s+check)`],
  ['build', String.raw`(?:(?:npm|pnpm|yarn|bun)\s+run\s+build|cargo\s+build|go\s+build|mvn\s+compile|\./gradlew\s+build|cmake\s+--build)`],
].map(([kind, pattern]) => [kind, new RegExp(`${PREFIX}${pattern}\\b`, 'im')]);
const PROVABLE_KINDS = new Set(['test', 'typecheck', 'build']);

function classifySegment(text) {
  const hit = PATTERNS.find(([, pattern]) => pattern.test(String(text || '')));
  return hit ? hit[0] : null;
}

/** test | lint | typecheck | build | null — the first classified segment of the command. */
function classify(command) {
  let segments;
  try { segments = lex.scan(String(command || '')); } catch (_) { return null; }
  for (const segment of segments) {
    const kind = classifySegment(segment.text);
    if (kind) return kind;
  }
  return null;
}

/** true / false when a segment is `set -o pipefail` / `set +o pipefail`, else null. */
function pipefailDelta(text) {
  const toks = words.tokenize(text).filter(t => t.type === 'word').map(t => t.value);
  let i = 0;
  while (i < toks.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(toks[i])) i += 1;
  if (i >= toks.length || toks[i].split('/').pop() !== 'set') return null;
  let mentioned = null;
  for (i += 1; i < toks.length; i += 1) {
    const arg = toks[i];
    if ((arg === '-o' || arg === '+o') && toks[i + 1] === 'pipefail') { mentioned = arg === '-o'; i += 1; continue; }
    if (/^[-+][A-Za-z]+$/.test(arg) && arg.includes('o')) {
      const attached = arg.slice(arg.indexOf('o') + 1);
      if (attached === 'pipefail') mentioned = arg[0] === '-';
      else if (!attached && toks[i + 1] === 'pipefail') { mentioned = arg[0] === '-'; i += 1; }
    }
  }
  return mentioned;
}

/**
 * An exit 0 proves a validation succeeded only when every path to exit 0 runs it: its status
 * reaches its pipeline (last element, or pipefail), only '&&' follows, not backgrounded.
 */
function policy(command) {
  let segments;
  try { segments = lex.scan(command); } catch (_) { return { provable: false, reason: 'validation_status_not_reported' }; }
  const hits = segments.map((s, i) => (classifySegment(s.text) ? i : -1)).filter(i => i >= 0);
  if (!hits.length) return { provable: true, reason: null };
  if (segments[segments.length - 1].op === '&') return { provable: false, reason: 'validation_backgrounded' };
  // 10.1 addition: exit 0 must imply the validation ran — no `||` before it, no earlier exit/exec/return.
  const first = hits[0];
  const skipped = segments.slice(0, first).some(s => s.op === '||' || /^\s*(?:exit|return|exec)\b/.test(s.text));
  if (skipped) return { provable: false, reason: 'validation_may_not_run' };
  // The tool itself can be replaced: traps, aliases, functions, shopt/enable, PATH rewrites.
  const last = hits[hits.length - 1];
  // venv activation is the normal workflow — relative, in-repo paths only.
  const activate = /^\s*(?:source|\.)\s+['"]?(?:\.\/)?(?:(?!\.\.\/)\.?[\w-][\w.-]*\/)*bin\/activate['"]?\s*$/;
  const shadow = segments.slice(0, last + 1).some(s => !activate.test(s.text)
    && /^\s*(?:trap|alias|shopt|enable|hash|source|\.|function)\s|^\s*[A-Za-z_][\w.-]*\s*\(\s*\)|(?:^|\s)(?:export\s+)?PATH=/.test(s.text));
  if (shadow) return { provable: false, reason: 'validation_shadowable' };
  for (const vi of hits) {
    let end = vi;
    while (end < segments.length && (segments[end].op === '|' || segments[end].op === '|&')) end += 1;
    const after = segments.slice(end).map(s => (s.op === '\n' ? ';' : s.op)).filter(op => op && op !== '|' && op !== '|&');
    if (after.some(op => op !== '&&')) return { provable: false, reason: 'validation_status_not_reported' };
    let pipefail = false;
    for (let i = 0; i < vi; i += 1) { const d = pipefailDelta(segments[i].text); if (d !== null) pipefail = d; }
    if (vi !== end && !pipefail) return { provable: false, reason: 'pipeline_without_pipefail' };
  }
  return { provable: true, reason: null };
}

/** Credential redaction (union of the 9.9.9 CC/CX rules) + head 300 / tail 1200 truncation. */
function redact(value) {
  const out = String(value || '')
    .replace(/\b(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|xox[abpr]-[A-Za-z0-9-]{8,}|AKIA[0-9A-Z]{16})\b/g, '[REDACTED]')
    .replace(/(authorization\s*:\s*(?:bearer|basic|token)\s+)[^\s,;'"]+/gi, '$1[REDACTED]')
    .replace(/((?:api[_-]?key|token|password|passwd|secret|private[_-]?key|client[_-]?secret|aws[_-](?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id)|database[_-]?url)\s*[=:]\s*)[^\s,;]+/gi, '$1[REDACTED]')
    .replace(/(--(?:password|token|api[-_]?key|secret)(?:=|\s+))[^\s,;]+/gi, '$1[REDACTED]')
    .replace(/(\b[a-z][a-z0-9+.-]*:\/\/)[^\s/@:]+:[^\s/@]+@/gi, '$1[REDACTED]@');
  const chars = [...out];
  if (chars.length <= 1500) return out;
  return `${chars.slice(0, 300).join('')}\n…[truncated ${chars.length - 1500} chars]…\n${chars.slice(-1200).join('')}`;
}

function file(ctx, sprint = ctx.sprint) {
  return path.join(ctx.runtime, 'evidence', `${sprint}.jsonl`);
}

/** Append one record (O_APPEND single write). Returns the record. */
function append(ctx, fields) {
  if (!ctx.sprint) return null;
  const kind = fields.kind || classify(fields.command) || 'other';
  const verdict = fields.policy || policy(fields.command || '');
  const record = {
    schema: 1,
    id: crypto.randomBytes(6).toString('hex'),
    ts: new Date().toISOString(),
    sprint: ctx.sprint,
    source: fields.source,
    platform: fields.platform || null,
    command: redact(fields.command).slice(0, 500),
    kind,
    exit: Number.isInteger(fields.exit) ? fields.exit : null,
    provable: PROVABLE_KINDS.has(kind) && verdict.provable && Number.isInteger(fields.exit),
    reason: verdict.reason || (Number.isInteger(fields.exit) ? null : 'exit_code_unknown'),
    tree_sha: fields.tree_sha || null,
    ignore: Array.isArray(fields.ignore) ? fields.ignore : [],
    covers: Array.isArray(fields.covers) ? fields.covers : [],
  };
  if (fields.output !== undefined) record.output = redact(fields.output);
  const target = file(ctx);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.appendFileSync(target, `${JSON.stringify(record)}\n`, { encoding: 'utf8', mode: 0o600 });
  return record;
}

function read(ctx, sprint = ctx.sprint) {
  let text;
  try { text = fs.readFileSync(file(ctx, sprint), 'utf8'); } catch (_) { return []; }
  const rows = [];
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try { rows.push(JSON.parse(line)); } catch (_) { /* torn line */ }
  }
  return rows.filter(row => row && row.sprint === sprint);
}

/** PASS records valid for tree: provable, exit 0, same tree_sha computed with the same ignore list. */
function valid(ctx, tree, { anyProvableKind = false, ignore = [] } = {}) {
  const key = JSON.stringify(ignore);
  return read(ctx).filter(row => row.exit === 0 && row.tree_sha === tree && JSON.stringify(row.ignore || []) === key
    && (row.provable === true || (anyProvableKind && row.kind === 'lint' && row.reason === null)));
}

module.exports = { classify, classifySegment, policy, redact, append, read, valid, file, PROVABLE_KINDS };
