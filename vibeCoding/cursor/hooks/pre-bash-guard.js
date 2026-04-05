#!/usr/bin/env node
// VibeCoding v3.0-cursor — beforeShellExecution: 危险命令拦截
// 位置: ~/.cursor/hooks/pre-bash-guard.js
//
// Cursor beforeShellExecution 协议：
//   stdin:  { command, cwd, conversation_id, ... }
//   stdout: { continue: bool, permission: "allow"|"deny"|"ask", userMessage?, agentMessage? }
//   注意: 必须通过 stdout JSON 控制，exit code 无效

const fs = require('fs');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const cmd = input.command || '';

  const BLOCKED = [
    { pattern: /rm\s+-rf\s+[\/~]/, reason: 'rm -rf 危险路径' },
    { pattern: /chmod\s+777/,      reason: '全开权限' },
    { pattern: /curl\s+.*\|\s*(?:bash|sh)/, reason: 'curl pipe to shell' },
    { pattern: /wget\s+.*\|\s*(?:bash|sh)/, reason: 'wget pipe to shell' },
    { pattern: />\s*\/etc\//,      reason: '覆写系统文件' },
    { pattern: /mkfs\./,           reason: '格式化磁盘' },
    { pattern: /dd\s+.*of=\/dev\//, reason: '直写设备' },
    { pattern: /sudo\s+rm/,        reason: 'sudo rm' },
  ];

  for (const { pattern, reason } of BLOCKED) {
    if (pattern.test(cmd)) {
      const response = {
        continue: false,
        permission: 'deny',
        userMessage: `[VibeCoding] 已拦截危险命令: ${reason}`,
        agentMessage: `此命令被安全守卫拦截 (${reason})，请使用更安全的替代方案。`
      };
      process.stdout.write(JSON.stringify(response));
      process.exit(0);
    }
  }

  // 放行
  process.stdout.write(JSON.stringify({ continue: true, permission: 'allow' }));
  process.exit(0);
} catch (e) {
  // 解析失败，默认放行
  process.stdout.write(JSON.stringify({ continue: true, permission: 'allow' }));
  process.exit(0);
}
