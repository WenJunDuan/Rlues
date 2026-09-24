#!/usr/bin/env node
/**
 * v9.6.2 · CC PostCompact hook
 * 职责: compact 后注入 .ai_state/_index.md 摘要到 additionalContext (恢复 state 感知)
 * 源: PostCompact 输出协议同 SessionStart
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

    const content = fs.readFileSync(idx, 'utf-8');
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch) { process.exit(0); }

    const additional = `## Athena 项目状态 (post-compact restore)\n\n${fmMatch[1]}\n\n详见 .ai_state/_index.md`;
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PostCompact',
        additionalContext: additional,
      }
    }));
  } catch (e) {
    process.stderr.write(`[compact-restore] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
