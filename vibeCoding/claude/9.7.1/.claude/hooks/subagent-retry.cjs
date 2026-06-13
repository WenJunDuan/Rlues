#!/usr/bin/env node
/**
 * v9.6.2 · CC PostToolUse(Task) hook
 * 职责: subagent 失败时记录到 details/runtime-events.md (供主 agent 参考)
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
    const out = payload?.tool_output || {};
    const exitCode = out.exit_code || 0;
    if (exitCode === 0) { process.exit(0); }

    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }

    const events = path.join(aiState, 'details', 'runtime-events.md');
    fs.mkdirSync(path.dirname(events), { recursive: true });
    const ts = new Date().toISOString();
    const stderr = (out.stderr || '').slice(0, 500);
    fs.appendFileSync(events, `\n## ${ts} · subagent 退出码 ${exitCode}\n- stderr: \`${stderr}\`\n`);
  } catch (e) {
    process.stderr.write(`[subagent-retry] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
