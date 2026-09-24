'use strict';
// YAML-subset reader shared by every rule (blockers P5: three copies merged into one).
// Supports: scalars (plain / "double" / 'single', trailing " #" comments), inline lists
// [a, "b"], inline maps {k: v}, block lists of scalars or flat maps, one level of nested
// maps. Anything else is kept as its raw string — the gate never throws on odd YAML.

function scalar(raw) {
  let value = String(raw).trim();
  const quoted = value.match(/^"((?:[^"\\]|\\.)*)"|^'((?:[^']|'')*)'/);
  if (quoted) {
    if (quoted[1] !== undefined) {
      try { return JSON.parse(`"${quoted[1]}"`); } catch (_) { return quoted[1]; }
    }
    return quoted[2].replace(/''/g, "'");
  }
  const hash = value.search(/\s#/);
  if (hash >= 0) value = value.slice(0, hash).trim();
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (value === 'null' || value === '~') return null;
  if (/^-?\d+(?:\.\d+)?$/.test(value)) return Number(value);
  if (value.startsWith('[') && value.endsWith(']')) return splitFlow(value.slice(1, -1)).map(scalar);
  if (value.startsWith('{') && value.endsWith('}')) {
    const out = {};
    for (const part of splitFlow(value.slice(1, -1))) {
      const m = part.match(/^\s*("[^"]*"|'[^']*'|[^:]+?)\s*:\s*(.*)$/);
      if (m) out[String(scalar(m[1]))] = scalar(m[2]);
    }
    return out;
  }
  return value;
}

/** Split a flow collection body on top-level commas, respecting quotes and brackets. */
function splitFlow(body) {
  const parts = [];
  let buf = '';
  let quote = '';
  let depth = 0;
  for (const ch of body) {
    if (quote) { buf += ch; if (ch === quote) quote = ''; continue; }
    if (ch === '"' || ch === "'") { quote = ch; buf += ch; continue; }
    if (ch === '[' || ch === '{') depth += 1;
    if (ch === ']' || ch === '}') depth -= 1;
    if (ch === ',' && depth === 0) { if (buf.trim()) parts.push(buf); buf = ''; continue; }
    buf += ch;
  }
  if (buf.trim()) parts.push(buf);
  return parts;
}

/** The frontmatter block of a document (text between the first two "---" lines), or null. */
function block(text) {
  const lines = String(text || '').replace(/^\uFEFF/, '').split(/\r?\n/);
  const fence = (line) => line.trimEnd() === '---';
  if (!fence(lines[0])) return null;
  const end = lines.findIndex((line, i) => i > 0 && fence(line));
  return end < 0 ? null : lines.slice(1, end);
}

const KEY = /^([A-Za-z0-9_.-]+)\s*:(?:\s+(.*)|\s*)$/;

function parseLines(lines) {
  const result = {};
  let i = 0;
  const indent = (line) => line.match(/^ */)[0].length;
  const skip = (line) => !line.trim() || line.trim().startsWith('#');
  while (i < lines.length) {
    const line = lines[i];
    if (skip(line) || indent(line) > 0) { i += 1; continue; }
    const m = line.match(KEY);
    i += 1;
    if (!m) continue;
    const [, key, rest] = m;
    if (rest !== undefined && rest.trim() !== '' && !rest.trim().startsWith('#')) {
      result[key] = scalar(rest);
      continue;
    }
    const child = [];
    // YAML allows a block list at the key's own indent ("key:\n- a"): collect it as the value.
    const listAtZero = i < lines.length && /^- |^-$/.test(lines[i]);
    while (i < lines.length && (skip(lines[i]) || indent(lines[i]) > 0 || (listAtZero && /^- |^-$/.test(lines[i])))) {
      child.push(listAtZero && !/^\s/.test(lines[i]) ? `  ${lines[i]}` : lines[i]);
      i += 1;
    }
    result[key] = nested(child);
  }
  return result;
}

function nested(lines) {
  const body = lines.filter(line => line.trim() && !line.trim().startsWith('#'));
  if (!body.length) return '';
  const base = Math.min(...body.map(line => line.match(/^ */)[0].length));
  const dedent = body.map(line => line.slice(base));
  if (!dedent[0].startsWith('- ') && dedent[0] !== '-') return parseLines(dedent);
  const items = [];
  let current = null;
  for (const line of dedent) {
    if (line.startsWith('- ') || line === '-') {
      if (current) items.push(finish(current));
      current = [line.slice(2)];
    } else if (current) current.push(line.replace(/^ {2}/, ''));
  }
  if (current) items.push(finish(current));
  return items;
}

function finish(lines) {
  if (lines.length === 1 && !KEY.test(lines[0])) return scalar(lines[0]);
  return parseLines(lines);
}

/** Parse the frontmatter of text; {} when there is none. */
function parse(text) {
  const lines = block(text);
  return lines ? parseLines(lines) : {};
}

module.exports = { parse, scalar, block };
