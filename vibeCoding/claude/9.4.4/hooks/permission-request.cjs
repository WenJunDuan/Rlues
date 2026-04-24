#!/usr/bin/env node
'use strict';
// PermissionRequest hook (Claude Code v2.0.45+)
// 触发: Claude 请求用户批准某个工具调用时
// 作用: VibeCoding 不自动 allow/deny, 只记录 + 让用户最终决定
// 输出: hookSpecificOutput.decision.behavior = "ask" → 保留原提示由用户决定
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let data={};try{data=JSON.parse(input);}catch(e){process.exit(0);return;}
  const toolName=data.tool_name||'unknown';
  const cmd=(data.tool_input&&data.tool_input.command)||'';
  const short=cmd.length>80?cmd.slice(0,80)+'...':cmd;
  process.stderr.write('[permission-request] '+toolName+': '+short+'\n');
  // behavior=ask → 保留用户确认流程, 不跳过也不自动 deny
  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PermissionRequest',
      decision:{behavior:'ask'}
    }
  }));
  process.exit(0);
});
