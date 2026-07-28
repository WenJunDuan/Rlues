#!/usr/bin/env node
/**
 * Athena · CC PostCompact hook (B3 重写, 2026-07-28 台账 W28)
 * 职责: compact 后注入 _index.md **白名单摘要 + 未消解告警** 到 additionalContext。
 * v9.6.2 旧版注入整段 frontmatter (~90 行含能力表/counts) — post-compact 恰是 context
 * 最紧张时刻, 打最肥 payload; 且不带 specialAlerts (design_changed_after_impl/熔断未消解
 * 会在 compact 后失联)。渲染逻辑与 session-start 共用 _index-render.cjs, 无双写。
 * 输出协议同 SessionStart: { hookSpecificOutput: { hookEventName, additionalContext } }
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { parseFrontmatter, renderIndexWhitelist, specialAlerts } = require('./_index-render.cjs');

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

    const fm = parseFrontmatter(idx);
    const summary = renderIndexWhitelist(fm);
    if (!summary) { process.exit(0); }

    const parts = ['## Athena 项目状态 (post-compact restore)', '', summary];
    const alerts = specialAlerts(fm, aiState);
    if (alerts.length) { parts.push('', '## 🚨 重要提醒', '', alerts.join('\n\n')); }
    parts.push('', '详见 .ai_state/_index.md');

    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PostCompact',
        additionalContext: parts.join('\n'),
      }
    }));
  } catch (e) {
    process.stderr.write(`[compact-restore] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
