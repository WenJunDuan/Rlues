#!/usr/bin/env node
// VibeCoding Kernel v8.0 - Session Start Hook
// Loads .ai_state/session.md and reports status

const fs = require('fs');
const path = require('path');

const stateDir = path.join(process.cwd(), '.ai_state');
const sessionFile = path.join(stateDir, 'session.md');
const doingFile = path.join(stateDir, 'doing.md');

if (fs.existsSync(sessionFile)) {
  const session = fs.readFileSync(sessionFile, 'utf8');
  console.error('[VibeCoding] Session state loaded');
  
  if (fs.existsSync(doingFile)) {
    const doing = fs.readFileSync(doingFile, 'utf8');
    const tasks = (doing.match(/\[→\]/g) || []).length;
    if (tasks > 0) {
      console.error(`[VibeCoding] ⚠ ${tasks} task(s) in progress from previous session`);
    }
  }
} else {
  console.error('[VibeCoding] No .ai_state found. Run vibe-init to initialize.');
}
