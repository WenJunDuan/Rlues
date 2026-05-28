#!/usr/bin/env node
/**
 * v9.6.2 · CC Stop hook (优先级低于 delivery-gate)
 * 职责: 在 _index.md 末尾追加 "current_sprint stage=X completed @ <ts>" 历史条目
 *       但不阻塞 (delivery-gate 已经做硬约束).
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

    // 解析 frontmatter 取当前 stage / sprint
    const content = fs.readFileSync(idx, 'utf-8');
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch) { process.exit(0); }
    const fm = fmMatch[1];
    const stage = (fm.match(/stage:\s*"?([^"\n]+)"?/) || [])[1] || '';
    const sprint = (fm.match(/current_sprint:\s*(\d+)/) || [])[1] || '?';

    if (!stage) { process.exit(0); }

    // 追加到 history 段 (在末尾)
    const ts = new Date().toISOString().slice(0, 19).replace('T', ' ');
    const entry = `- \`${ts}\`: stage=${stage} sprint=${sprint} turn-end\n`;

    const HIST_MARKER = '## 历史 (按时间倒序';
    if (content.includes(HIST_MARKER)) {
      // 在 marker 后插入
      const updated = content.replace(
        /(## 历史 \(按时间倒序[^\n]*\n[^\n]*\n)/,
        `$1${entry}`
      );
      fs.writeFileSync(idx, updated, 'utf-8');
    } else {
      // 末尾追加
      fs.appendFileSync(idx, `\n\n## 历史\n${entry}`);
    }
  } catch (e) {
    process.stderr.write(`[pace-continuator] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
