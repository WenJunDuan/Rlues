'use strict';
// issues.md — the one problem ledger (ai-state-v2 §4). Hooks and the CLI append rows;
// only rows are machine-written, the table header is created on first use.
const fs = require('fs');
const path = require('path');

const TYPES = { bug: 'B', gate: 'G', upstream: 'U', env: 'E', debt: 'D', question: 'Q' };
const HEADER = '# Issues\n\n| id | 类型 | 级别 | 一句话 | 发现于 | 去向 | 状态 |\n|---|---|---|---|---|---|---|\n';
const ROW = /^\|\s*([BGUEDQ])-(\d+)\s*\|\s*([a-z]+)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|/;

const cell = (value) => String(value === undefined || value === null || value === '' ? '—' : value)
  .replace(/\r?\n/g, ' ').replace(/\|/g, '/').trim().slice(0, 160);

function file(aiState) { return path.join(aiState, 'issues.md'); }

function list(aiState) {
  let text;
  try { text = fs.readFileSync(file(aiState), 'utf8'); } catch (_) { return []; }
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(ROW);
    if (m) rows.push({ id: `${m[1]}-${m[2]}`, type: m[3], sev: m[4].trim(), text: m[5].trim(), found: m[6].trim(), next: m[7].trim(), status: m[8].trim() });
  }
  return rows;
}

/** Append a row; returns its id. */
function add(aiState, { type, sev, text, found, next, status = 'open' }) {
  const prefix = TYPES[type];
  if (!prefix) throw new Error(`unknown issue type ${type}; one of ${Object.keys(TYPES).join(', ')}`);
  const target = file(aiState);
  let body = '';
  try { body = fs.readFileSync(target, 'utf8'); } catch (_) { body = HEADER; }
  const numbers = list(aiState).filter(row => row.id.startsWith(`${prefix}-`)).map(row => Number(row.id.slice(2)));
  const id = `${prefix}-${String((numbers.length ? Math.max(...numbers) : 0) + 1).padStart(3, '0')}`;
  const row = `| ${id} | ${type} | ${cell(sev)} | ${cell(text)} | ${cell(found)} | ${cell(next)} | ${cell(status)} |\n`;
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, (body.endsWith('\n') ? body : `${body}\n`) + row, 'utf8');
  return id;
}

module.exports = { add, list, file, TYPES };
