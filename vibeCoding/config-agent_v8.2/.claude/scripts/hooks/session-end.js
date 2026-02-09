#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const session = path.resolve('.ai_state/session.md');
if (fs.existsSync(session)) {
  fs.appendFileSync(session, `\n- ended: ${new Date().toISOString()}\n`);
}
