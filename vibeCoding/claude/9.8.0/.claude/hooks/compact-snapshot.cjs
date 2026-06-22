#!/usr/bin/env node
/**
 * v9.6.2 · CC PreCompact hook
 * 职责: compact 前快照 .ai_state/_index.md 到 .ai_state/.snapshots/pre-compact-<ts>.md
 */
'use strict';
const fs = require('fs');
const path = require('path');

function findAiState(cwd) {
  for (let i = 0, c = cwd; i < 5; i++) {
    const cand = path.join(c, '.ai_state');
    if (fs.existsSync(cand) && fs.statSync(cand).isDirectory()) return cand;
    const p = path.dirname(c);
    if (p === c) return null;
    c = p;
  }
  return null;
}

function main() {
  try {
    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }
    const idx = path.join(aiState, '_index.md');
    if (!fs.existsSync(idx)) { process.exit(0); }

    const snapDir = path.join(aiState, '.snapshots');
    fs.mkdirSync(snapDir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const dst = path.join(snapDir, `pre-compact-${ts}.md`);
    fs.copyFileSync(idx, dst);
  } catch (e) {
    process.stderr.write(`[compact-snapshot] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
