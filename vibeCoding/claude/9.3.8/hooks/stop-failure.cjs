#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — StopFailure: API 错误恢复
// async hook — 记录错误但不阻断, 为 session resume 提供上下文
'use strict';

const fs = require('fs');
const path = require('path');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const stateDir = path.join(projectDir, '.ai_state');

    if (!fs.existsSync(stateDir)) {
      return process.exit(0);
    }

    // 记录错误到 lessons.md
    const lessonsPath = path.join(stateDir, 'lessons.md');
    const timestamp = new Date().toISOString().slice(0, 19);
    const errorType = data.error_type || 'unknown';
    const errorMsg = data.error_message || 'API error';

    let lessons = '';
    try { lessons = fs.readFileSync(lessonsPath, 'utf8'); } catch {}

    const entry = `- [${timestamp}] StopFailure: ${errorType} — ${errorMsg.slice(0, 100)}. 恢复策略: 用 claude --resume 继续, 或检查 .ai_state/state.json 当前阶段。\n`;

    fs.writeFileSync(lessonsPath, lessons + entry);
    process.stderr.write(`[stop-failure] 已记录 API 错误到 lessons.md。用 claude --resume 恢复。`);
  } catch {}
  process.exit(0);
});
