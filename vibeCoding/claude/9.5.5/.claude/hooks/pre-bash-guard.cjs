#!/usr/bin/env node
'use strict';
// VibeCoding PreToolUse Bash 软拦截。
// v9.5: 只拦截"会让机器进医院"的灾难命令。其他靠流程约束 + evaluator 兜底。
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let cmd='';
  try{const d=JSON.parse(input);cmd=(d.tool_input&&d.tool_input.command)||'';}catch(e){process.exit(0);return;}
  if(!cmd){process.exit(0);return;}
  const deny=r=>{
    process.stderr.write('[bash-guard] deny: '+r+' ('+cmd.slice(0,60)+')\n');
    process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'deny',permissionDecisionReason:r}}));
    process.exit(0);
  };
  // 灾难级 (3 条):
  if(/rm\s+-[rR]f\s+(\/\*?|~\/?)(\s|;|&|\||$)/.test(cmd))return deny('禁止删除系统/用户根目录');
  if(/curl\s+.*\|\s*(bash|sh|zsh)/.test(cmd)||/wget\s+.*\|\s*(bash|sh|zsh)/.test(cmd))return deny('禁止管道执行远程脚本');
  if(/mkfs\./.test(cmd)||/dd\s+if=.*of=\/dev\/sd/.test(cmd)||/>\s*\/dev\/sd[a-z]/.test(cmd))return deny('禁止格式化磁盘/写设备');
  process.exit(0);
});
