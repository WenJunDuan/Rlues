// v9.1.8 PreToolUse(Bash): 安全
const input=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
const cmd=input?.tool_input?.command||'';
const B=[/rm\s+-rf\s+[\/~]/,/chmod\s+777/,/curl\s+.*\|\s*(?:bash|sh)/,/wget\s+.*\|\s*(?:bash|sh)/,/>\s*\/etc\//,/mkfs\./,/dd\s+.*of=\/dev\//];
for(const p of B){if(p.test(cmd)){process.stderr.write(`[pre-bash] 阻断: ${cmd}\n`);process.exit(2);}}
process.exit(0);
