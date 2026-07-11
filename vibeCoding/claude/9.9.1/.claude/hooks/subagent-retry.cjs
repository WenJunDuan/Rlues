#!/usr/bin/env node
/**
 * v9.9.1 · CC PostToolUseFailure(Agent) hook
 * 职责: subagent 工具调用失败记录 runtime-events.md (供主 agent 参考)
 * v9.9.0 修: details/ 是 9.6.4 前旧布局, 触发即复活死目录 → 改写 sprints/{slug}/, 无 slug 落 .ai_state/ 根
 * 命名注: CX 端同名 hook 处理 Codex 可观察的工具结果; 双端 payload 与职责有意不对称
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
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};
    if (payload?.hook_event_name !== 'PostToolUseFailure') { process.exit(0); }

    const aiState = findAiState(payload?.cwd || process.cwd());
    if (!aiState) { process.exit(0); }

    // v9.9.0: 优先当前 sprint 目录, 无 slug 落 .ai_state/ 根 (不再写死 details/)
    let slug = '';
    try {
      const idx = fs.readFileSync(path.join(aiState, '_index.md'), 'utf-8');
      slug = ((idx.match(/^current_sprint_slug:\s*"?([^"\n]*)"?/m) || [])[1] || '').trim();
    } catch (_) {}
    const events = slug
      ? path.join(aiState, 'sprints', slug, 'runtime-events.md')
      : path.join(aiState, 'runtime-events.md');
    fs.mkdirSync(path.dirname(events), { recursive: true });
    const ts = new Date().toISOString();
    const error = String(payload?.error || 'unknown failure')
      .replace(/((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+/gi, '$1[REDACTED]')
      .slice(0, 500);
    fs.appendFileSync(
      events,
      `\n## ${ts} · Agent tool failure\n` +
      `- interrupted: ${payload?.is_interrupt === true}\n` +
      `- duration_ms: ${Number.isFinite(payload?.duration_ms) ? payload.duration_ms : 'unknown'}\n` +
      `- error: \`${error}\`\n`,
    );
  } catch (e) {
    process.stderr.write(`[subagent-retry] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
