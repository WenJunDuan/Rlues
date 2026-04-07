// VibeCoding v9.3.7 — PreToolUse(Bash): 危险命令拦截
let input = ''; try { input = require('fs').readFileSync('/dev/stdin','utf8'); } catch(e) {}
let hi = {}; try { hi = JSON.parse(input); } catch(e) {}
const cmd = hi.tool_input?.command || '';
const bad = [/rm\s+-rf\s+\//, />\s*\/dev\/sd/, /mkfs\./, /dd\s+if=/, /curl.*\|\s*bash/, /wget.*\|\s*sh/];
for (const p of bad) { if (p.test(cmd)) { process.stderr.write(`[pre-bash] 拦截: ${cmd}`); process.exit(2); } }
process.exit(0);
