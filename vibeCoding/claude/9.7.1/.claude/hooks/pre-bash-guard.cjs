#!/usr/bin/env node
'use strict';

const fs = require('fs');

const P0_PATTERNS = [
  /\brm\s+-rf?\s+\/(\s|$)/,
  /\brm\s+-rf?\s+~(\s|$)/,
  /\brm\s+-rf?\s+\$HOME/,
  /\bcurl\b[^|]*\|\s*bash/,
  /\bwget\b[^|]*\|\s*bash/,
  /\bDROP\s+TABLE\b/i,
  /:\(\)\s*\{/,
  /\bdd\s+.*of=\/dev\/(sda|nvme|xvd)/,
  />\s*\/dev\/(sda|nvme|xvd)/,
];

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};
    const command = payload?.tool_input?.command || '';
    if (!command) { process.exit(0); }
    for (const pat of P0_PATTERNS) {
      if (pat.test(command)) {
        process.stderr.write(
          `[pre-bash-guard] BLOCKED: 检测到灾难命令模式 (${pat})\n` +
          `命令: ${command.slice(0, 200)}\n`
        );
        process.exit(2);
      }
    }
    process.exit(0);
  } catch (e) {
    if (e && e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[pre-bash-guard] non-blocking: ${e.message}\n`);
    }
    process.exit(0);
  }
}

main();
