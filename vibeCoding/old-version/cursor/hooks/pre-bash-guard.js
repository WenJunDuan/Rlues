#!/usr/bin/env node
// VibeCoding v3.0-cursor — beforeShellExecution: 危险命令拦截
// 位置: ~/.cursor/hooks/pre-bash-guard.js
//
// Cursor beforeShellExecution 协议:
//   stdin:  { command, cwd, conversation_id, workspace_roots }
//   stdout: { continue: bool, permission: "allow"|"deny"|"ask", userMessage?, agentMessage? }
//
// 设计原则:
//   - 只拦截真正危险的命令，不误杀正常操作
//   - rm -rf /tmp/build 是正常操作，rm -rf / 是灾难
//   - 输出 JSON 到 stdout 控制，不用 exit code

const fs = require('fs');

function deny(reason) {
  process.stdout.write(JSON.stringify({
    continue: false,
    permission: 'deny',
    userMessage: `[VibeCoding] 拦截: ${reason}`,
    agentMessage: `命令被安全守卫拦截 (${reason})。请使用更安全的替代方案。`
  }));
  process.exit(0);
}

function allow() {
  process.stdout.write(JSON.stringify({ continue: true, permission: 'allow' }));
  process.exit(0);
}

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const cmd = (input.command || '').trim();

  const BLOCKED = [
    // rm -rf 只拦截根目录和家目录，不拦截 /tmp/build 等正常路径
    { pattern: /rm\s+(-[a-z]*f[a-z]*\s+)?\/\s*$/,      reason: 'rm 根目录 /' },
    { pattern: /rm\s+(-[a-z]*f[a-z]*\s+)?\/\*\s*/,      reason: 'rm /*' },
    { pattern: /rm\s+(-[a-z]*f[a-z]*\s+)?~\s*$/,        reason: 'rm 家目录 ~' },
    { pattern: /rm\s+(-[a-z]*f[a-z]*\s+)?~\/\s*$/,      reason: 'rm 家目录 ~/' },
    { pattern: /rm\s+(-[a-z]*f[a-z]*\s+)?~\/\*/,        reason: 'rm ~/*' },
    // 其他高危操作
    { pattern: /chmod\s+777\s+\//,                        reason: 'chmod 777 系统路径' },
    { pattern: /curl\s+.*\|\s*(?:sudo\s+)?(?:bash|sh)/,  reason: 'curl pipe to shell' },
    { pattern: /wget\s+.*\|\s*(?:sudo\s+)?(?:bash|sh)/,  reason: 'wget pipe to shell' },
    { pattern: />\s*\/etc\//,                             reason: '覆写 /etc/' },
    { pattern: /mkfs\./,                                  reason: '格式化磁盘' },
    { pattern: /dd\s+.*of=\/dev\//,                       reason: '直写设备' },
  ];

  for (const { pattern, reason } of BLOCKED) {
    if (pattern.test(cmd)) {
      deny(reason);
    }
  }

  allow();
} catch (e) {
  allow(); // 解析失败默认放行
}
