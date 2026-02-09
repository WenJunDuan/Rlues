#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const aiState = path.resolve('.ai_state');
if (!fs.existsSync(aiState)) {
  console.log('[VibeCoding] No .ai_state/ found. Run vibe-init first.');
  process.exit(0);
}
const doing = path.join(aiState, 'doing.md');
if (fs.existsSync(doing)) {
  const content = fs.readFileSync(doing, 'utf8');
  if (content.includes('task:') && !content.includes('task: \n')) {
    console.log('[VibeCoding] Unfinished task detected. Consider vibe-resume.');
  }
}
