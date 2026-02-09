#!/usr/bin/env node
const { execSync } = require('child_process');
try {
  const staged = execSync('git diff --cached --name-only').toString();
  if (staged.includes('.ai_state/') || staged.includes('.knowledge/')) {
    console.log('[VibeCoding] Warning: committing .ai_state or .knowledge files.');
  }
} catch (e) {}
