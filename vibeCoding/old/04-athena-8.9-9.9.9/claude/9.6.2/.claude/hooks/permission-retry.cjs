#!/usr/bin/env node
/**
 * v9.6.2 · CC PermissionDenied hook
 * 职责: 当 Bash 命令因 deny 规则被拒, 给主 agent 一个明确的反馈
 * 输出协议: { decision: "block", reason: "..." } 或 retry hint
 * 源: https://docs.anthropic.com/en/docs/claude-code/hooks#permission-denied
 */
'use strict';
const fs = require('fs');

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};
    const deniedCmd = payload?.tool_input?.command || payload?.command || '';

    // 输出: hint 主 agent 用更窄的命令或者让用户手工跑
    const reason =
      `[permission-retry] 命令被 deny 规则拦截: ${deniedCmd.slice(0, 100)}\n` +
      `建议: 用更窄的命令 (例如 \`Read\` tool 替代 cat), 或让用户手工 confirm 跑.`;

    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PermissionDenied',
        retry: false,
        message: reason,
      }
    }));
    process.exit(0);
  } catch (e) {
    process.stderr.write(`[permission-retry] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}
main();
