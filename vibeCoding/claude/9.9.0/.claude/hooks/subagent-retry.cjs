#!/usr/bin/env node
/**
 * v9.9.0 · CC PostToolUse(Task) hook
 * 职责: subagent 失败记录 runtime-events.md (供主 agent 参考)
 * v9.9.0 修: details/ 是 9.6.4 前旧布局, 触发即复活死目录 → 改写 sprints/{slug}/, 无 slug 落 .ai_state/ 根
 * 命名注: CX 端同名 hook 挂 PostToolUse(Bash) 干 tracker 活 (兼容旧 spawn_agent CLI), 双端职责不同, 有意不对称
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
    const stderr = (out.stderr || '').slice(0, 500);
    fs.appendFileSync(events, `\n## ${ts} · subagent 退出码 ${exitCode}\n- stderr: \`${stderr}\`\n`);
  } catch (e) {
    process.stderr.write(`[subagent-retry] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
