#!/usr/bin/env node
'use strict';
// PostToolUse hook v9.5 - 治 subagent / Skill / Task 的懒惰式降级
// 触发条件: 关键词驱动, 仅在 subagent 输出含明确"放弃信号"时注入
// 计数器: per-session (~/.claude/state/retry-counter.json)
// 协议: PostToolUse 输出 hookSpecificOutput.additionalContext
//
// v9.5 变更:
//   1. 删除"lesson-drafter 已起草"引用 (该 hook 已删除)
//   2. 触发消息改引用铁律 6 (完成度证据), 不再引用旧铁律 8
//   3. 消息精简 350→200 字符以内
//   4. effort=max 时降低触发频次 (高 effort 模型已经认真)

const fs=require('fs'),path=require('path');
const home=process.env.HOME||require('os').homedir();
const sessionDir=path.join(home,'.claude','state');
const counterFile=path.join(sessionDir,'retry-counter.json');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// 放弃信号关键词
const ABANDON_KEYWORDS=[
  /本\s*session\s*没有\s*Bash\s*工具/i,
  /Bash\s*工具.*?(不可用|无法使用|无法执行)/i,
  /子\s*agent\s*也一样/i,
  /无\s*Bash\s*工具权限/i,
  /请\s*(您|你)\s*(直接|手动|自己)/,
  /请在(提示框|终端)/,
  /用\s*!\s*前缀/,
  /\bI (cannot|can't|don't have).*Bash\b/i,
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
  if(!['Task','Skill','SkillCall'].some(t=>toolName.includes(t))){process.exit(0);return;}

  // CC 2.1.133+: effort 输入
  const effort=(event.effort&&event.effort.level)||process.env.CLAUDE_EFFORT||'';
  const isMax=effort==='max';

  let output='';
  if(event.tool_response){
    output=typeof event.tool_response==='string'?event.tool_response:JSON.stringify(event.tool_response);
  }else if(event.tool_output){
    output=typeof event.tool_output==='string'?event.tool_output:JSON.stringify(event.tool_output);
  }
  if(!output){process.exit(0);return;}

  const matched=ABANDON_KEYWORDS.find(re=>re.test(output));
  if(!matched){process.exit(0);return;}

  // effort=max 时只在第 2 次以上才注入 (减少打扰)
  fs.mkdirSync(sessionDir,{recursive:true});
  let counter={};
  try{counter=JSON.parse(fs.readFileSync(counterFile,'utf8'));}catch(e){}
  const sessionId=event.session_id||'unknown';
  counter[sessionId]=(counter[sessionId]||0)+1;
  try{fs.writeFileSync(counterFile,JSON.stringify(counter));}catch(e){}
  const count=counter[sessionId];

  if(isMax&&count===1){
    // max effort 第一次不打扰
    process.stderr.write('[subagent-retry] effort=max, 跳过首次注入\n');
    process.exit(0);return;
  }

  process.stderr.write('[subagent-retry] 放弃信号 ('+count+'/3): '+matched.toString().slice(0,40)+'\n');

  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'subagent-retry',count,tool:toolName,signal:matched.toString().slice(0,40)})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}

  let msg;
  if(count<3){
    msg='⚠ Hermes 铁律 6 (完成度证据): subagent "无能为力" 不算证据 ('+count+'/3)。\n'+
        '重试: ① 主 agent 实测一次命令看真实 stderr ② 是 permission 错就报具体规则 ③ 是子 agent 自限就接管，不推回用户';
  }else{
    msg='🛑 已重试 3 次。按铁律 6 接受失败 → 完整命令+stderr+尝试列表写入报告。';
  }

  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PostToolUse',
      additionalContext:msg
    }
  }));
  process.exit(0);
});
