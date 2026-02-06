#!/usr/bin/env node
// VibeCoding Kernel v8.0 - Session End Hook
// Saves session state on interrupt

const fs = require('fs');
const path = require('path');

const stateDir = path.join(process.cwd(), '.ai_state');
const sessionFile = path.join(stateDir, 'session.md');

if (fs.existsSync(stateDir)) {
  const timestamp = new Date().toISOString();
  const content = `# 会话状态\n\n- **locked**: false\n- **last_updated**: ${timestamp}\n- **paused**: true\n- **reason**: session_interrupt\n`;
  fs.writeFileSync(sessionFile, content);
  console.error('[VibeCoding] Session state saved on interrupt');
}
