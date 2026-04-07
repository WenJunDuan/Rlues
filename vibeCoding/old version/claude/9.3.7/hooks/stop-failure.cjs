// VibeCoding v9.3.7 — StopFailure: 写恢复文件
const fs = require('fs');
const path = require('path');
let input = ''; try { input = fs.readFileSync('/dev/stdin','utf8'); } catch(e) {}
let ctx = {}; try { ctx = JSON.parse(input); } catch(e) {}
const ai = path.join(process.cwd(), '.ai_state');
try {
  if (!fs.existsSync(ai)) fs.mkdirSync(ai, {recursive:true});
  fs.writeFileSync(path.join(ai,'recovery.json'), JSON.stringify({
    timestamp: new Date().toISOString(), error: ctx.error||'unknown',
    details: ctx.error_details||'', action: (ctx.error||'').includes('rate_limit') ? 'wait_60s' : 'check_auth'
  }, null, 2));
} catch(e) {}
process.exit(0);
