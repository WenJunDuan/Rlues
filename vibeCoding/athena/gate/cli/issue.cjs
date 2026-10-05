'use strict';
// athena issue add|close|list — the one problem ledger (ai-state-v2 §4).
// `add --type gate` also appends one row to the upstream Athena feedback ledger (in Rlues:
// .ai_state/docs/research/athena-downstream-feedback.md) when one is
// configured (env ATHENA_FEEDBACK, else `feedback` in ~/.athena/config.json): gate problems
// found downstream reach the harness without a manual copy. Best-effort, never fails the add.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const issues = require('../lib/issues.cjs');
const archive = require('./lib/archive.cjs');

const USAGE = `usage:
  athena issue add --type bug|gate|upstream|env|debt|question --text "<一句话>" [--sev P0..P3] [--found <where>] [--next <去向>]
  athena issue close <id> [--note "<how>"] [--status closed|dropped]
  athena issue list [--type T] [--all] [--export]`;
const OPEN = (row) => !['closed', 'dropped'].includes(row.status);

const cell = (value) => String(value || '—').replace(/\r?\n/g, ' ').replace(/\|/g, '/').trim() || '—';

/** Configured upstream feedback ledger path, '' when switched off (ATHENA_FEEDBACK=""), or null. */
function feedbackFile(env) {
  if (env.ATHENA_FEEDBACK !== undefined) return String(env.ATHENA_FEEDBACK).trim();
  const home = env.HOME || os.homedir();
  try {
    const value = JSON.parse(fs.readFileSync(path.join(home, '.athena', 'config.json'), 'utf8')).feedback;
    return typeof value === 'string' && value.trim() ? value.trim().replace(/^~(?=\/|$)/, home) : null;
  } catch (_) { return null; }
}

/**
 * Append `| 项目账 | 级 | 现象 | 影响 | 当时绕法 | 建议 | 状态 |` to the configured file only:
 * after the last row of its last 项目账 table, else at the end under a new header.
 * Returns a warning string, or null when written or switched off.
 */
function upstream(ctx, env, id, f) {
  const target = feedbackFile(env);
  if (target === '') return null;
  if (!target) return 'no upstream feedback file configured (ATHENA_FEEDBACK or `feedback` in ~/.athena/config.json)';
  try {
    const file = path.resolve(ctx.mainRoot, target);
    const lines = fs.readFileSync(file, 'utf8').split('\n'); // a missing file is not created
    const row = `| ${id} | ${cell(f.sev)} | ${today()}，${cell(path.basename(ctx.mainRoot))}：${cell(f.text)} | — | — | — | 待修 |`;
    let at = -1;
    for (let i = 0; i < lines.length; i += 1) {
      if (!/^\|\s*项目账\s*\|/.test(lines[i])) continue;
      at = i;
      while (at + 1 < lines.length && lines[at + 1].startsWith('|')) at += 1;
    }
    if (at >= 0) lines.splice(at + 1, 0, row);
    else {
      while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
      lines.push('', '| 项目账 | 级 | 现象 | 影响 | 当时绕法 | 建议 | 状态 |', '|---|---|---|---|---|---|---|', row, '');
    }
    fs.writeFileSync(file, lines.join('\n'), 'utf8');
    return null;
  } catch (error) { return `upstream feedback not written (${error.code || error.message})`; }
}

function add(argv, io) {
  const { flags: f } = flags(argv, { type: 'str', text: 'str', sev: 'str', found: 'str', next: 'str', status: 'str' });
  if (!f.type || !f.text) throw new UsageError('add needs --type and --text');
  if (f.sev && !/^(P[0-3]|—)$/.test(f.sev)) throw new UsageError('--sev must be P0..P3');
  const ctx = requireCtx(io);
  const id = issues.add(ctx.aiState, { type: f.type, sev: f.sev, text: f.text, found: f.found || ctx.sprint || today(), next: f.next, status: f.status || 'open' });
  archive.stage(ctx, ['issues.md']);
  io.stdout.write(`${id}\n`);
  const warning = f.type === 'gate' ? upstream(ctx, io.env || process.env, id, f) : null;
  if (warning) io.stderr.write(`athena issue add: ${warning}; ${id} is recorded locally\n`);
  return 0;
}

function close(argv, io) {
  const { flags: f, rest } = flags(argv, { note: 'str', status: 'str' });
  const id = rest[0];
  if (!/^[BGUEDQ]-\d+$/.test(id || '')) throw new UsageError('close <id> (e.g. G-003)');
  const status = f.status || 'closed';
  if (!['closed', 'dropped'].includes(status)) throw new UsageError('--status closed|dropped');
  const ctx = requireCtx(io);
  const file = issues.file(ctx.aiState);
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const at = lines.findIndex(l => new RegExp(`^\\|\\s*${id}\\s*\\|`).test(l));
  if (at < 0) throw new UsageError(`${id} not found`);
  const cells = lines[at].split('|');
  const next = cells[cells.length - 3].trim();
  cells[cells.length - 3] = ` ${next && next !== '—' ? `${next}; ` : ''}${today()}${f.note ? ` ${f.note.replace(/\|/g, '/').slice(0, 80)}` : ''} `;
  cells[cells.length - 2] = ` ${status} `;
  lines[at] = cells.join('|');
  fs.writeFileSync(file, lines.join('\n'), 'utf8');
  archive.stage(ctx, ['issues.md']);
  io.stdout.write(`${id} ${status}\n`);
  return 0;
}

function list(argv, io) {
  const { flags: f } = flags(argv, { type: 'str', all: 'bool', export: 'bool' });
  const ctx = requireCtx(io);
  const rows = issues.list(ctx.aiState).filter(r => (f.all || OPEN(r)) && (!f.type || r.type === f.type));
  if (f.export) {
    const project = path.basename(ctx.mainRoot);
    io.stdout.write(`<!-- athena issue export: ${project} ${today()} -->\n| project | id | 类型 | 级别 | 一句话 | 发现于 | 状态 |\n|---|---|---|---|---|---|---|\n`);
    for (const r of rows) io.stdout.write(`| ${project} | ${r.id} | ${r.type} | ${r.sev} | ${r.text} | ${r.found} | ${r.status} |\n`);
    return 0;
  }
  for (const r of rows) io.stdout.write(`${r.id}  ${r.type.padEnd(8)} ${r.sev.padEnd(3)} ${r.status.padEnd(8)} ${r.text}\n`);
  if (!rows.length) io.stdout.write('(no matching issues)\n');
  return 0;
}

function main(argv, io) {
  const [sub, ...rest] = argv;
  const table = { add, close, list };
  if (!table[sub]) { io.stderr.write(`${USAGE}\n`); return 2; }
  try { return table[sub](rest, io); } catch (error) {
    if (error instanceof UsageError || /unknown issue type/.test(error.message)) { io.stderr.write(`athena issue ${sub}: ${error.message}\n`); return 2; }
    throw error;
  }
}

module.exports = { main, OPEN, feedbackFile };
