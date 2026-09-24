'use strict';
// Runtime ledgers under .ai_state/.runtime: queued advisories (injected on the next prompt)
// and the Stop circuit breaker (design §5.6) that turns a repeated block into an issue row.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const issues = require('./issues.cjs');

const WINDOW_MS = 30 * 60 * 1000;
const ESCALATE_AT = 3;

function appendJsonl(file, row) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, `${JSON.stringify(row)}\n`, { encoding: 'utf8', mode: 0o600 });
}

function readJsonl(file) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (_) { return []; }
  const rows = [];
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try { rows.push(JSON.parse(line)); } catch (_) { /* torn */ }
  }
  return rows;
}

/** Queue advisory messages for injection on the next prompt/session start. */
function advise(ctx, warnings) {
  const file = path.join(ctx.runtime, 'advisories.jsonl');
  for (const w of warnings) appendJsonl(file, { ts: new Date().toISOString(), rule: w.rule, message: w.message, sprint: ctx.sprint });
}

/** Undelivered advisories (deduplicated), advancing the cursor. */
function drain(ctx) {
  const file = path.join(ctx.runtime, 'advisories.jsonl');
  const cursorFile = `${file}.cursor`;
  let offset = 0;
  try { offset = Number(fs.readFileSync(cursorFile, 'utf8')) || 0; } catch (_) { /* first */ }
  let buf;
  try { buf = fs.readFileSync(file); } catch (_) { return []; }
  if (offset > buf.length) offset = 0;
  const fresh = buf.subarray(offset).toString('utf8');
  const consumed = offset + Buffer.byteLength(fresh.slice(0, fresh.lastIndexOf('\n') + 1));
  fs.writeFileSync(cursorFile, String(consumed));
  const seen = new Set();
  const out = [];
  for (const line of fresh.split('\n')) {
    try {
      const row = JSON.parse(line);
      const key = `${row.rule}:${row.message}`;
      if (!seen.has(key)) { seen.add(key); out.push(row); }
    } catch (_) { /* torn or empty */ }
  }
  return out;
}

/** Stable key of a reason: numbers, hex shas and paths do not make a block "different". */
function reasonKey(reason) {
  const norm = String(reason).replace(/[0-9a-f]{7,64}/gi, '#').replace(/\/[^\s'"`]+/g, '/…').replace(/\d+/g, 'N');
  return crypto.createHash('sha1').update(norm).digest('hex');
}

/**
 * Stop only (a pre_tool block is never released). Returns 'block' or 'release'.
 * Chain = trailing same-session rows within the window with the same reason key.
 */
function breaker(ctx, ev, reason) {
  const file = path.join(ctx.runtime, 'gate-ledger.jsonl');
  const session = ev.session_id || '';
  const key = reasonKey(reason);
  const now = Date.now();
  let count = 0;
  const rows = readJsonl(file);
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    const row = rows[i];
    if ((row.session_id || '') !== session) continue; // Pi sends no session id: '' chains only with ''
    if (now - Date.parse(row.ts) > WINDOW_MS) break;
    if (row.event === 'pass' || row.key !== key) break;
    if (row.event === 'release') break;
    count += 1;
  }
  const consecutive = count + 1;
  const release = consecutive >= ESCALATE_AT;
  appendJsonl(file, { ts: new Date(now).toISOString(), event: release ? 'release' : 'block', session_id: session, key, consecutive, sprint: ctx.sprint, stage: ctx.stage });
  if (release) {
    try {
      issues.add(ctx.aiState, { type: 'gate', sev: 'P2', text: `熔断放行(${consecutive}次): ${String(reason).split('\n')[0]}`, found: ctx.sprint || 'idle', next: 'harness-iteration 分诊', status: 'triage' });
    } catch (_) { /* ledger is best-effort; the release itself still happens */ }
  }
  return release ? 'release' : 'block';
}

/** A Stop that passed every hard gate closes any open chain. */
function pass(ctx, ev) {
  const file = path.join(ctx.runtime, 'gate-ledger.jsonl');
  const rows = readJsonl(file);
  const last = rows.reverse().find(row => (row.session_id || '') === (ev.session_id || ''));
  if (last && last.event === 'block') appendJsonl(file, { ts: new Date().toISOString(), event: 'pass', session_id: ev.session_id || '', key: last.key, sprint: ctx.sprint });
}

module.exports = { advise, drain, breaker, pass, reasonKey, appendJsonl, readJsonl };
