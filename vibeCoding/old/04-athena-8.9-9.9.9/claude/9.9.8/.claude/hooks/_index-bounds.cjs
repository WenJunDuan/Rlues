#!/usr/bin/env node
/**
 * Athena 9.9.8 _index.md bounds: ≤12 KiB, lists ≤10, item ≤160 bytes.
 * Overflow is copied to sprints/{slug}/index-overflow.md, never dropped.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ITEM_MAX_BYTES = 160;
const INDEX_MAX_BYTES = 12 * 1024;
const LIST_MAX = 10;

function byteLen(text) {
  return Buffer.byteLength(String(text), "utf8");
}

function utf8Prefix(text, maxBytes) {
  const buf = Buffer.from(String(text), "utf8");
  if (buf.length <= maxBytes) return String(text);
  let end = maxBytes;
  while (end > 0 && (buf[end] & 0xc0) === 0x80) end -= 1;
  return buf.subarray(0, end).toString("utf8");
}

function summarize(full, pointer) {
  const suffix = ` →${pointer}`;
  const budget = ITEM_MAX_BYTES - byteLen(suffix);
  if (budget < 1) return utf8Prefix(pointer, ITEM_MAX_BYTES);
  return utf8Prefix(String(full).replace(/\s+/g, " ").trim(), budget) + suffix;
}

function splitQuotedList(inner) {
  const items = [];
  let cur = "";
  let quote = "";
  let escaped = false;
  const raw = String(inner).trim();
  if (!raw) return items;
  for (const char of raw) {
    if (escaped) { cur += char; escaped = false; continue; }
    if (char === "\\" && quote === "\"") { escaped = true; cur += char; continue; }
    if (quote) {
      cur += char;
      if (char === quote) quote = "";
      continue;
    }
    if (char === "\"" || char === "'") { quote = char; cur += char; continue; }
    if (char === ",") { items.push(cur.trim()); cur = ""; continue; }
    cur += char;
  }
  if (cur.trim()) items.push(cur.trim());
  return items;
}

function unquote(item) {
  const text = String(item).trim();
  if (text.length >= 2 && text[0] === text[text.length - 1] && (text[0] === "\"" || text[0] === "'")) {
    return text.slice(1, -1).replace(/\\"/g, "\"");
  }
  return text;
}

function readSlug(content) {
  const match = String(content).match(/^current_sprint_slug:\s*"?([^"\n]*)"?/m);
  return match ? match[1].trim() : "";
}

function spillPath(aiState, slug) {
  if (slug) return path.join(aiState, "sprints", slug, "index-overflow.md");
  return path.join(aiState, "index-overflow.md");
}

function loadSpill(filePath) {
  try { return fs.readFileSync(filePath, "utf8"); } catch (_) { return ""; }
}

function nextId(existing, prefix) {
  const nums = [...String(existing).matchAll(new RegExp(`^## ${prefix}-(\\d+)`, "gm"))].map((m) => Number(m[1]));
  return nums.length ? Math.max(...nums) + 1 : 0;
}

function makeSpiller(aiState, slug) {
  const filePath = spillPath(aiState, slug);
  let body = loadSpill(filePath);
  if (!body) {
    body = `# _index overflow — ${slug || "project"}\n\nFull items moved off \`_index.md\` (AC9). Do not delete.\n`;
  }
  return {
    pointer(id) { return `index-overflow.md#${id}`; },
    spill(prefix, full) {
      const id = `${prefix}-${nextId(body, prefix)}`;
      body += `\n## ${id}\n\n${full}\n`;
      return id;
    },
    flush() {
      fs.mkdirSync(path.dirname(filePath), { recursive: true });
      fs.writeFileSync(filePath, body, "utf8");
    },
  };
}

function enforceRouteHistory(content, spiller) {
  const match = content.match(/^route_history:\s*\[(.*)\]\s*(?:#.*)?$/m);
  if (!match) return content;
  let values = splitQuotedList(match[1]).map(unquote);
  const extra = values.length > LIST_MAX ? values.slice(0, values.length - LIST_MAX) : [];
  values = values.slice(-LIST_MAX);
  for (const full of extra) spiller.spill("rh", full);
  const next = values.map((full) => {
    if (byteLen(full) <= ITEM_MAX_BYTES) return full;
    const id = spiller.spill("rh", full);
    return summarize(full, spiller.pointer(id));
  });
  const rendered = `[${next.map((item) => JSON.stringify(item)).join(", ")}]`;
  return content.replace(/^route_history:\s*\[.*\]\s*(?:#.*)?$/m, `route_history: ${rendered}  # re-route ≤10, item ≤160B`);
}

function enforceBulletSection(content, heading, spillPrefix, spiller) {
  const match = content.match(new RegExp(`^(${heading}[^\\n]*\\n)([\\s\\S]*?)(?=^## |\\Z)`, "m"));
  if (!match) return content;
  const header = match[1];
  const lines = match[2].split(/\n/);
  const prefix = [];
  const items = [];
  const suffix = [];
  let seen = false;
  for (const line of lines) {
    if (/^\s*-\s+/.test(line)) { seen = true; items.push(line.replace(/^\s*-\s+/, "")); }
    else if (!seen) prefix.push(line);
    else suffix.push(line);
  }
  const overflowCount = Math.max(0, items.length - LIST_MAX);
  const keepCount = overflowCount ? LIST_MAX - 1 : LIST_MAX;
  const keep = items.slice(0, keepCount);
  const extra = items.slice(keepCount);
  let archiveId = "";
  if (extra.length) {
    archiveId = spiller.spill(spillPrefix, extra.map((item, i) => `### archived-${i}\n${item}`).join("\n\n"));
  }
  const out = keep.map((full) => {
    if (byteLen(full) <= ITEM_MAX_BYTES) return `- ${full}`;
    if (full.includes("index-overflow.md#")) return `- ${utf8Prefix(full, ITEM_MAX_BYTES)}`;
    const id = spiller.spill(spillPrefix, full);
    return `- ${summarize(full, spiller.pointer(id))}`;
  });
  if (archiveId) out.push(`- older ${heading.replace(/^##\s+/, "")} →${spiller.pointer(archiveId)}`);
  const newBody = [...prefix, ...out, ...suffix].join("\n");
  return content.slice(0, match.index) + header + newBody + content.slice(match.index + match[0].length);
}

function enforceIndexBounds(content, aiState) {
  const slug = readSlug(content);
  const spiller = makeSpiller(aiState, slug);
  let next = enforceRouteHistory(content, spiller);
  next = enforceBulletSection(next, "## 当前状态", "st", spiller);
  next = enforceBulletSection(next, "## 历史", "hi", spiller);
  spiller.flush();
  return next;
}

module.exports = {
  ITEM_MAX_BYTES,
  INDEX_MAX_BYTES,
  LIST_MAX,
  byteLen,
  utf8Prefix,
  summarize,
  splitQuotedList,
  unquote,
  enforceIndexBounds,
};
