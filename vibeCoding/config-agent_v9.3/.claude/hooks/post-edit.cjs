// VibeCoding v9.3.1 — PostToolUse(Write|Edit): 格式化
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
const file = input?.tool_input?.file_path || input?.tool_input?.path || '';

if (!file) { process.exit(0); }

try {
  if (file.match(/\.(ts|tsx|js|jsx)$/)) {
    if (fs.existsSync('node_modules/.bin/prettier')) {
      execFileSync('npx', ['prettier', '--write', file], { timeout: 5000, stdio: 'ignore' });
    }
  } else if (file.match(/\.py$/)) {
    try { execFileSync('which', ['black'], { stdio: 'ignore', timeout: 2000 }); } catch { process.exit(0); }
    execFileSync('python3', ['-m', 'black', file, '--quiet'], { timeout: 5000, stdio: 'ignore' });
  }
} catch {}
process.exit(0);
