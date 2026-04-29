#!/usr/bin/env node
'use strict';
// PermissionRequest hook (Claude Code v2.0.45+)
// behavior=ask → 保留用户确认流程
// 安全: 写 hook-trace 前过 redact (token/secret 脱敏)
const fs=require('fs'),path=require('path');
const {redact}=require('./_redact.cjs');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let data={};try{data=JSON.parse(input);}catch(e){process.exit(0);return;}
  const toolName=data.tool_name||'unknown';
  const cmdRaw=(data.tool_input&&data.tool_input.command)||'';
  const cmd=redact(cmdRaw);
  const short=cmd.length>80?cmd.slice(0,80)+'...':cmd;
  process.stderr.write('[permission-request] '+toolName+': '+short+'\n');
  // trace (best-effort, 失败不影响)
  try{
    if(fs.existsSync(sd)){
      const line=JSON.stringify({ts:new Date().toISOString(),hook:'permission-request',tool:toolName,cmd:short})+'\n';
      fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
    }
  }catch(e){}
  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PermissionRequest',
      decision:{behavior:'ask'}
    }
  }));
  process.exit(0);
});
