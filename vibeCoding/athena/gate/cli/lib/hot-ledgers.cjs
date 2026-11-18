'use strict';
// Conservative Markdown ledger parser: only explicit terminal statuses may leave the hot layer.
const fs = require('fs');
const path = require('path');
const MAX_BYTES = 16 * 1024;
const NAMES = ['queue.md', 'SPRINTS.md'];
const DONE = new Set(['done', 'shipped', 'dropped', 'completed', 'closed', '完成', '已完成', '已交付', '已放弃']);
const read = file => { try { return fs.readFileSync(file, 'utf8'); } catch (_) { return ''; } };
const cells = line => line.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map(s => s.trim());
const separator = line => /^\|/.test(line || '') && cells(line).every(v => /^:?-+:?$/.test(v));
const clean = text => text.replace(/[`*_]/g, '').trim().toLowerCase();
function records(text) {
  const lines = text.split(/(?<=\n)/);
  const out = [];
  const headers = new Set();
  let statusCol = -1;
  // Independent pass: list scanning can jump over a fence opener before a blank line.
  const fenced = new Set();
  let fence = null;
  lines.forEach((line, i) => {
    const marker = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      fenced.add(i);
      if (marker && marker[1][0] === fence[0] && marker[1].length >= fence.length && !line.slice(marker[0].length).trim()) fence = null;
    } else if (marker) { fenced.add(i); fence = marker[1]; }
  });
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (fenced.has(i)) { statusCol = -1; continue; }
    if (/^\|/.test(line)) {
      const c = cells(line);
      const header = c.findIndex(v => /^(status|状态)$/i.test(clean(v)));
      if (separator(lines[i + 1])) { statusCol = header; headers.add(i); headers.add(i + 1); continue; }
      if (separator(line)) continue;
      out.push({ start: i, end: i + 1, text: line, done: statusCol >= 0 && DONE.has(clean(c[statusCol] || '')) });
    } else if (/^(?:[-*]|\d+[.)])\s+/.test(line)) {
      statusCol = -1;
      let end = i + 1;
      for (let next = end; next < lines.length; next++) {
        if (!lines[next].trim()) continue;
        if (!/^[ \t]+\S/.test(lines[next])) break;
        end = next + 1;
      }
      const block = lines.slice(i, end).join('');
      // Only a simple item's first-line suffix is authoritative. Nested metadata,
      // code examples and continuation blocks are ambiguous and stay hot.
      const status = line.trimEnd().match(/[;—]\s*status\s*[:=]\s*([\w-]+)[ \t]*$/i);
      const simple = end === i + 1;
      out.push({ start: i, end, text: block, done: simple && (/^\s*[-*]\s+\[x\]/i.test(line) || Boolean(status && DONE.has(clean(status[1])))) });
      i = end - 1;
    } else statusCol = -1;
  }
  return { lines, entries: out, headers };
}
function counts(text) {
  const entries = records(text).entries;
  return { total: entries.length, unfinished: entries.filter(r => !r.done).length };
}
function summary(aiState) {
  return Object.fromEntries(NAMES.map(name => {
    const hot = read(path.join(aiState, name));
    const cold = read(path.join(aiState, 'archive', 'ledgers', name));
    const h = counts(hot), a = counts(cold);
    return [name, { total: h.total + a.total, unfinished: h.unfinished + a.unfinished }];
  }));
}
function plan(aiState, name) {
  const file = path.join(aiState, name), text = read(file);
  if (Buffer.byteLength(text) <= MAX_BYTES) return null;
  const { lines, entries, headers } = records(text);
  const moving = entries.filter(r => r.done);
  const remove = new Set(moving.flatMap(r => Array.from({ length: r.end - r.start }, (_, n) => r.start + n)));
  const hot = lines.filter((_, i) => !remove.has(i)).join('');
  const target = path.join(aiState, 'archive', 'ledgers', name);
  // Copy the document's table headers too, so archived status cells keep their meaning.
  const cold = read(target) + '\n' + lines.filter((line, i) => remove.has(i) || headers.has(i)).join('');
  const before = counts(text), old = counts(read(target)), after = counts(hot), archived = counts(cold);
  if (before.total + old.total !== after.total + archived.total || before.unfinished + old.unfinished !== after.unfinished + archived.unfinished) throw new Error(`${name}: ledger reconciliation failed; nothing written`);
  return { file, target, hot, cold, moved: moving.length, remaining: Buffer.byteLength(hot) };
}
function queue(aiState) {
  return records(read(path.join(aiState, 'queue.md'))).entries.filter(r => !r.done).map(r => r.text.trim());
}
module.exports = { MAX_BYTES, NAMES, records, summary, plan, queue };
