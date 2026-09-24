'use strict';
// Key-level, in-place writers for _index.md and items.yaml (S4). Comments, unknown keys and the
// file's own spelling (v1 current_sprint_slug / v2 sprint …) are preserved.
const fs = require('fs');
const path = require('path');
const frontmatter = require('../../lib/frontmatter.cjs');

const ALIASES = {
  sprint: ['sprint', 'current_sprint_slug'],
  roadmap: ['roadmap', 'current_roadmap_slug'],
  route: ['route', 'route_history'],
};
const ROUTE_MAX = { route: 3, route_history: 10 };

const q = (value) => JSON.stringify(value === undefined || value === null ? '' : value);

function templatesDir() { return path.join(__dirname, '..', '..', 'templates'); }

/** Render a template with {{name}} fields (unknown names are left visible, never silently empty). */
function render(name, fields) {
  const text = fs.readFileSync(path.join(templatesDir(), name), 'utf8');
  return text.replace(/\{\{(\w+)\}\}/g, (m, key) => (fields[key] === undefined ? m : String(fields[key])));
}

/** Frontmatter line range [start, end) of text's --- block, or null. */
function fmRange(lines) {
  if (lines[0] === undefined || lines[0].replace(/^﻿/, '').trimEnd() !== '---') return null;
  const end = lines.findIndex((l, i) => i > 0 && l.trimEnd() === '---');
  return end < 0 ? null : [1, end];
}

/** Which key spelling a document uses for a logical field (first existing alias; default = first). */
function spelling(fm, field) {
  const names = ALIASES[field] || [field];
  return names.find(n => n in fm) || names[0];
}

/**
 * Set top-level frontmatter scalars / flow values in a markdown file, in place.
 * values: {field: value}; value undefined = leave; arrays/objects rendered as JSON flow.
 * Special: {route_push: "line"} prepends to route/route_history within its bound.
 */
/** The unquoted " # …" tail of a `key: value` line (kept when the value is rewritten). */
function trailingComment(line) {
  let quote = '';
  for (let i = line.indexOf(':') + 1; i < line.length; i += 1) {
    const ch = line[i];
    if (quote) { if (ch === quote) quote = ''; continue; }
    if (ch === '"' || ch === "'") { quote = ch; continue; }
    if (ch === '#' && /\s/.test(line[i - 1] || '')) return line.slice(i).replace(/^/, '  ');
  }
  return '';
}

/** Lines after `at` that belong to its block value: deeper-indented (or `- ` items at column 0 for top-level keys). */
function blockEnd(lines, at, limit, keyIndent) {
  let end = at + 1;
  const zeroList = keyIndent === 0 && /^- |^-$/.test(lines[end] || '');
  // A line belongs to the block when it is deeper than the key (comments included), a column-0
  // list item of a top-level key, or a blank/comment line followed by more of the block.
  const member = (line) => line.trim() && (line.match(/^ */)[0].length > keyIndent || (zeroList && /^- |^-$/.test(line)));
  while (end < limit) {
    if (member(lines[end])) { end += 1; continue; }
    let k = end;
    while (k < limit && (!lines[k].trim() || /^\s*#/.test(lines[k]))) k += 1;
    if (k > end && k < limit && member(lines[k]) && !/^\s*#/.test(lines[k])) { end = k; continue; }
    break;
  }
  return end;
}

function setFields(file, values) {
  const raw = fs.readFileSync(file, 'utf8');
  const crlf = raw.includes('\r\n');
  const text = crlf ? raw.replace(/\r\n/g, '\n') : raw;
  const lines = text.split('\n');
  const range = fmRange(lines);
  if (!range) throw new Error(`${file}: no frontmatter block`);
  const fm = frontmatter.parse(text);
  const updates = {};
  for (const [field, value] of Object.entries(values)) {
    if (value === undefined) continue;
    if (field === 'route_push') {
      const key = spelling(fm, 'route');
      const current = Array.isArray(fm[key]) ? fm[key] : [];
      updates[key] = [String(value).slice(0, 160), ...current].slice(0, ROUTE_MAX[key] || 3);
      continue;
    }
    updates[spelling(fm, field)] = value;
  }
  for (const [key, value] of Object.entries(updates)) {
    const rendered = `${key}: ${typeof value === 'object' ? JSON.stringify(value) : q(value)}`;
    let at = -1;
    for (let i = range[0]; i < range[1]; i += 1) if (new RegExp(`^${key.replace(/\./g, '\\.')}\\s*:`).test(lines[i])) { at = i; break; }
    if (at >= 0) {
      const end = blockEnd(lines, at, range[1], 0); // drop the old block value with the key
      const comment = trailingComment(lines[at]);
      lines.splice(at, end - at, rendered + (typeof value === 'object' ? '' : comment));
      range[1] -= end - at - 1;
    } else {
      lines.splice(range[1], 0, rendered);
      range[1] += 1;
    }
  }
  fs.writeFileSync(file, crlf ? lines.join('\r\n') : lines.join('\n'), 'utf8');
}

function readIndex(aiState) {
  const file = path.join(aiState, '_index.md');
  return { file, fm: frontmatter.parse(fs.readFileSync(file, 'utf8')) };
}

// ---- items.yaml -------------------------------------------------------------------------

function itemsFile(aiState, roadmap) { return path.join(aiState, 'roadmap', roadmap, 'items.yaml'); }

/** Items of a roadmap as parsed maps (YAML subset), each with its line span. */
function readItems(file) {
  const raw = fs.readFileSync(file, 'utf8');
  const crlf = raw.includes('\r\n');
  const text = crlf ? raw.replace(/\r\n/g, '\n') : raw;
  const lines = text.split('\n');
  const itemsKey = lines.findIndex(l => /^items\s*:/.test(l)); // items live under `items:` (other lists are data)
  const items = [];
  let current = null;
  let itemIndent = null; // the first `- slug:`/`- id:` fixes the item level; deeper ones are nested data
  lines.forEach((line, i) => {
    const m = line.match(/^(\s*)- slug:\s*(.+?)\s*$/) || line.match(/^(\s*)- id:\s*(.+?)\s*$/);
    const underItems = itemsKey < 0 || i > itemsKey;
    if (m && underItems && itemIndent === null) itemIndent = m[1].length;
    if (m && underItems && m[1].length === itemIndent) {
      if (current) current.end = i;
      current = { indent: m[1].length, start: i, end: lines.length, slug: String(frontmatter.scalar(m[2])) };
      items.push(current);
    } else if (current && line.trim() && !/^\s/.test(line) && !/^#/.test(line)) { current.end = i; current = null; }
  });
  for (const item of items) {
    const body = lines.slice(item.start, item.end).map((l, k) => (k === 0 ? l.replace(/^(\s*)- /, '$1  ') : l));
    const pad = Math.min(...body.filter(l => l.trim()).map(l => l.match(/^ */)[0].length));
    item.data = frontmatter.parse(`---\n${body.map(l => l.slice(pad)).join('\n')}\n---\n`);
  }
  return { text, lines, items, crlf };
}

/** Set scalar/flow keys of one item in place; returns the item's parsed data before the change. */
function setItem(file, slug, values) {
  const { lines, items, crlf } = readItems(file);
  const item = items.find(it => it.slug === slug);
  if (!item) throw new Error(`${path.basename(path.dirname(file))}/items.yaml has no item ${slug}`);
  const keyIndent = ' '.repeat(item.indent + 2);
  for (const [rawKey, value] of Object.entries(values)) {
    let key = rawKey;
    if (key === 'sprint' && !('sprint' in item.data) && 'sprint_slug' in item.data) key = 'sprint_slug';
    const rendered = `${keyIndent}${key}: ${typeof value === 'object' ? JSON.stringify(value) : q(value)}`;
    let at = -1;
    for (let i = item.start; i < item.end; i += 1) {
      const probe = i === item.start ? lines[i].replace(/^(\s*)- /, '$1  ') : lines[i];
      if (probe.startsWith(`${keyIndent}${key}:`)) { at = i; break; }
    }
    if (at === item.start) throw new Error('refusing to rewrite the item key line');
    if (at >= 0) {
      const end = blockEnd(lines, at, item.end, keyIndent.length); // replace the whole old block value
      lines.splice(at, end - at, rendered);
      item.end -= end - at - 1;
    } else {
      // insert right after the last line that still belongs to this item (trailing blanks stay outside)
      let at2 = item.end;
      while (at2 > item.start + 1 && !lines[at2 - 1].trim()) at2 -= 1;
      lines.splice(at2, 0, rendered);
      item.end += 1;
    }
  }
  fs.writeFileSync(file, lines.join(crlf ? '\r\n' : '\n'), 'utf8');
  return item.data;
}

/** Every item across roadmaps: [{roadmap, slug, data}]. */
function allItems(aiState) {
  const dir = path.join(aiState, 'roadmap');
  const out = [];
  let names = [];
  try { names = fs.readdirSync(dir).sort(); } catch (_) { return out; }
  for (const roadmap of names) {
    const file = itemsFile(aiState, roadmap);
    if (!fs.existsSync(file)) continue;
    try { for (const item of readItems(file).items) out.push({ roadmap, slug: item.slug, data: item.data }); } catch (_) { /* skip */ }
  }
  return out;
}

const DONE = new Set(['done', 'completed']);

/** resume_when "after <item>" / "after <roadmap>/<item>" satisfied? null = not machine-checkable. */
function resumeReady(aiState, when, items = allItems(aiState)) {
  const m = String(when || '').trim().match(/^after\s+(?:([\w.-]+)\/)?([\w.-]+)\s*$/i);
  if (!m) return null;
  const hit = items.find(it => it.slug === m[2] && (!m[1] || it.roadmap === m[1]));
  return hit ? DONE.has(String(hit.data.status)) : false;
}

// ---- queue.md ---------------------------------------------------------------------------

/** Remove queue lines naming the sprint slug or its <roadmap>/<item> (ship / drop). Returns removed lines. */
function queueRemove(aiState, slug, ref = '') {
  const file = path.join(aiState, 'queue.md');
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (_) { return []; }
  const lines = text.split('\n');
  const word = (s) => new RegExp(`(^|[^\\w/.-])${s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w-])`);
  const removed = lines.filter(l => /^\s*(?:[-*]|\d+[.)]|\|)/.test(l) && (word(slug).test(l) || (ref && word(ref).test(l))));
  if (removed.length) fs.writeFileSync(file, lines.filter(l => !removed.includes(l)).join('\n'), 'utf8');
  return removed;
}

module.exports = { render, setFields, readIndex, spelling, itemsFile, readItems, setItem, allItems, resumeReady, queueRemove, DONE, templatesDir };
