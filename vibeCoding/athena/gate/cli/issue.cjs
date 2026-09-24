'use strict';
// athena issue add|close|list — the one problem ledger (ai-state-v2 §4).
const fs = require('fs');
const path = require('path');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const issues = require('../lib/issues.cjs');
const archive = require('./lib/archive.cjs');

const USAGE = `usage:
  athena issue add --type bug|gate|upstream|env|debt|question --text "<一句话>" [--sev P0..P3] [--found <where>] [--next <去向>]
  athena issue close <id> [--note "<how>"] [--status closed|dropped]
  athena issue list [--type T] [--all] [--export]`;
const OPEN = (row) => !['closed', 'dropped'].includes(row.status);

function add(argv, io) {
  const { flags: f } = flags(argv, { type: 'str', text: 'str', sev: 'str', found: 'str', next: 'str', status: 'str' });
  if (!f.type || !f.text) throw new UsageError('add needs --type and --text');
  if (f.sev && !/^(P[0-3]|—)$/.test(f.sev)) throw new UsageError('--sev must be P0..P3');
  const ctx = requireCtx(io);
  const id = issues.add(ctx.aiState, { type: f.type, sev: f.sev, text: f.text, found: f.found || ctx.sprint || today(), next: f.next, status: f.status || 'open' });
  archive.stage(ctx, ['issues.md']);
  io.stdout.write(`${id}\n`);
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

module.exports = { main, OPEN };
