// VibeCoding v9.1.7 — PreToolUse(Bash): 安全守卫
const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
const cmd = input?.tool_input?.command || '';

const BLOCKED = [
  /rm\s+-rf\s+[\/~]/,
  /chmod\s+777/,
  /curl\s+.*\|\s*(?:bash|sh)/,
  /wget\s+.*\|\s*(?:bash|sh)/,
  />\s*\/etc\//,
  /mkfs\./,
  /dd\s+.*of=\/dev\//,
];

for (const pattern of BLOCKED) {
  if (pattern.test(cmd)) {
    process.stderr.write(`[pre-bash] 阻断危险命令: ${cmd}\n`);
    process.exit(2);
  }
}
process.exit(0);
