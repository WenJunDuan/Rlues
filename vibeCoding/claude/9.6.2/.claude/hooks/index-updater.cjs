#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.2 · CC PostToolUse(Edit|Write|MultiEdit) hook
 * 
 * 职责: 当用户/agent 编辑 .ai_state/details/*.md 时, 自动重算 _index.md.counts
 * 
 * 与 cx 版本不同: cc 端 PostToolUse matcher 可直接匹配 Edit/Write/MultiEdit 工具,
 * 所以 cc 不需要 mtime 比对 hack, 直接在 hook 里增量更新.
 *
 * 源: https://docs.anthropic.com/en/docs/claude-code/hooks#post-tool-use
 */
'use strict';

const fs = require('fs');
const path = require('path');

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return { fm: {}, body: content };
  const parts = content.split('---', 3);
  if (parts.length < 3) return { fm: {}, body: content };
  const fm = {};
  for (const line of parts[1].split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const m = t.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
    if (m) {
      let v = m[2].trim();
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      fm[m[1]] = v;
    }
  }
  return { fm, body: parts[2] };
}

function writeFrontmatter(fm, body) {
  let out = '---\n';
  for (const [k, v] of Object.entries(fm)) {
    if (typeof v === 'number') out += `${k}: ${v}\n`;
    else out += `${k}: "${v}"\n`;
  }
  out += '---\n';
  return out + body;
}

function computeCounts(aiState) {
  const detailsDir = path.join(aiState, 'details');
  if (!fs.existsSync(detailsDir)) {
    return { features_count: 0, reviews_count: 0, cleanup_count: 0 };
  }

  let features = 0, reviews = 0, cleanups = 0;

  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        if (entry.name.startsWith('feature-') || entry.name === 'features.md') features++;
        if (entry.name.startsWith('cleanup-pass-')) cleanups++;
        if (entry.name.includes('review') || path.basename(dir) === 'reviews') reviews++;
      }
    }
  }
  walk(detailsDir);
  return { features_count: features, reviews_count: reviews, cleanup_count: cleanups };
}

function main() {
  try {
    // Hook payload via stdin
    let payload = {};
    try {
      const chunks = [];
      // sync read stdin (small payload)
      let data = '';
      try {
        data = fs.readFileSync(0, 'utf-8');
      } catch (_) { /* no stdin */ }
      if (data) payload = JSON.parse(data);
    } catch (_) { /* ignore */ }

    const cwd = process.cwd();
    const aiState = findAiState(cwd);
    if (!aiState) return;

    const idxPath = path.join(aiState, '_index.md');
    if (!fs.existsSync(idxPath)) return;

    const content = fs.readFileSync(idxPath, 'utf-8');
    const { fm, body } = parseFrontmatter(content);

    const newCounts = computeCounts(aiState);
    // counts 是嵌套字段, frontmatter parser 简化了, 我们用平铺存
    let changed = false;
    if (parseInt(fm.features_count || '0') !== newCounts.features_count) {
      fm.features_count = newCounts.features_count;
      changed = true;
    }
    if (parseInt(fm.reviews_count || '0') !== newCounts.reviews_count) {
      fm.reviews_count = newCounts.reviews_count;
      changed = true;
    }
    if (parseInt(fm.cleanup_count || '0') !== newCounts.cleanup_count) {
      fm.cleanup_count = newCounts.cleanup_count;
      changed = true;
    }

    if (changed) {
      fs.writeFileSync(idxPath, writeFrontmatter(fm, body), 'utf-8');
    }
  } catch (e) {
    if (e && e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[index-updater] non-blocking: ${e.message}\n`);
    }
  }
  process.exit(0);
}

main();
