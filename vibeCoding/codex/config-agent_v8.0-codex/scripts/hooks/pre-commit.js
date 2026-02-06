#!/usr/bin/env node
// VibeCoding Kernel v8.0 - Pre-commit Hook
// Warns about console.log and debug code

const fs = require('fs');
const filePath = process.env.file_path || '';

if (fs.existsSync(filePath)) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  if (/console\.log/.test(content)) {
    console.error('[Hook] ⚠ Remove console.log before commit');
  }
  if (/debugger/.test(content)) {
    console.error('[Hook] ⚠ Remove debugger statement before commit');
  }
  if (/TODO|FIXME|HACK/.test(content)) {
    console.error('[Hook] ⚠ Resolve TODO/FIXME/HACK before commit');
  }
}
