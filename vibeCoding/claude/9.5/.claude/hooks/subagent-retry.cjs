#!/usr/bin/env node
'use strict';
// PostToolUse hook - 治 subagent / Skill / Task 的懒惰式降级
// 触发条件: 关键词驱动 (Q1 决策)
//   仅当 subagent 输出含明确"放弃信号"时注入 retry 提示
// 计数器: per-session (用 ~/.claude/state/retry-counter.json)
// 协议: PostToolUse 输出 hookSpecificOutput.additionalContext (向主 agent 注入压力)

const fs=require('fs'),path=require('path');
const home=process.env.HOME||require('os').homedir();
const sessionDir=path.join(home,'.claude','state');
const counterFile=path.join(sessionDir,'retry-counter.json');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// 关键词 (Q1 决策: 关键词驱动而非全部触发)
const ABANDON_KEYWORDS=[
  /本\s*session\s*没有\s*Bash\s*工具/i,
  /子\s*agent\s*也一样/i,
  /无\s*Bash\s*工具权限/i,
  /请\s*(您|你)\s*(直接|手动|自己)/,
  /请在(提示框|终端)/,
  /用\s*!\s*前缀/,
  /\bI cannot execute\b/i,
  /\bplease run (this|the following) (command|manually)\b/i,
  /\bpaste (it|this|the command)\b.*\bagain\b/i,
  /\bnot listed as available to me\b/i,
];

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  const toolName=event.tool_name||'';
  // 只看 Task 和 Skill 工具的输出 (subagent 触发的)
  if(!['Task','Skill','SkillCall'].some(t=>toolName.includes(t))){process.exit(0);return;}

  // 取 tool_output / tool_response
  let output='';
  if(event.tool_response){
    output=typeof event.tool_response==='string'?event.tool_response:JSON.stringify(event.tool_response);
  }else if(event.tool_output){
    output=typeof event.tool_output==='string'?event.tool_output:JSON.stringify(event.tool_output);
  }
  if(!output){process.exit(0);return;}

  // 关键词检测
  const matched=ABANDON_KEYWORDS.find(re=>re.test(output));
  if(!matched){process.exit(0);return;}

  // 加载/更新计数器
  fs.mkdirSync(sessionDir,{recursive:true});
  let counter={};
  try{counter=JSON.parse(fs.readFileSync(counterFile,'utf8'));}catch(e){}
  const sessionId=event.session_id||'unknown';
  counter[sessionId]=(counter[sessionId]||0)+1;
  try{fs.writeFileSync(counterFile,JSON.stringify(counter));}catch(e){}

  const count=counter[sessionId];
  process.stderr.write('[subagent-retry] 检测到放弃信号 ('+count+'/3): '+matched.toString().slice(0,40)+'\n');

  // hook-trace
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'subagent-retry',count,tool:toolName,signal:matched.toString().slice(0,40)})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}

  let msg;
  if(count<3){
    msg='⚠ Hermes 铁律 8: subagent 报告无能为力是不接受的 (第 '+count+'/3 次)。\n'+
        '重试要求:\n'+
        '  1. 实测一次失败的命令, 看真实 stderr 和 exit code\n'+
        '  2. permission denied → 报具体缺失的 settings.json 规则, 用 settings.local.json 临时绕过\n'+
        '  3. subagent 自我设限 → 主 agent 接管, 不要把任务推回用户\n'+
        '  4. 完全禁止 "请你用 ! 前缀手动执行" 作为响应';
  }else{
    msg='🛑 已重试 3 次仍报无能为力, 按铁律 8 接受失败。\n'+
        'lesson-drafter 应已在 ~/.claude/lessons/draft-*.md 起草此问题。';
  }

  // PostToolUse 协议: hookSpecificOutput.additionalContext
  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PostToolUse',
      additionalContext:msg
    }
  }));
  process.exit(0);
});
