#!/usr/bin/env node
'use strict';
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let cmd='';
  try{const d=JSON.parse(input);cmd=(d.tool_input&&d.tool_input.command)||'';}catch(e){process.exit(0);return;}
  if(!cmd){process.exit(0);return;}
  const deny=r=>{process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'deny',permissionDecisionReason:r}}));process.exit(0);};
  if(/rm\s+-[rR]f\s+[\/~]/.test(cmd))return deny('禁止删除系统/用户根目录');
  if(/curl\s+.*\|\s*(bash|sh|zsh)/.test(cmd)||/wget\s+.*\|\s*(bash|sh|zsh)/.test(cmd))return deny('禁止管道执行远程脚本');
  if(/git\s+push\s+.*--force/.test(cmd))return deny('禁止 force push');
  if(/git\s+push\s+origin\s+(main|master)\b/.test(cmd))return deny('禁止直接 push main/master');
  process.exit(0);
});
