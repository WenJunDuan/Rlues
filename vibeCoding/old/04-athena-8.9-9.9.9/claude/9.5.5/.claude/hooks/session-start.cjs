#!/usr/bin/env node
'use strict';
// SessionStart hook v9.5
// 设计:
//   1. 删除全局 lessons INDEX 注入 (Hermes 不再做跨项目知识管理)
//   2. just-in-time 检索: 不预加载 tasks 内容, 只注入"文件存在 + 任务计数"轻量摘要
//   3. effort=max 时跳过 PACE 状态摘要 (高 effort 模型自己会探索)
// 输出协议: hookSpecificOutput.additionalContext
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','pace','context-essentials.md');
const home=process.env.HOME||require('os').homedir();
const globalEp=path.join(home,'.claude','skills','pace','context-essentials.md');

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){}
  const source=event.source||'unknown';
  // CC 2.1.133+ 输入 effort.level
  const effort=(event.effort&&event.effort.level)||process.env.CLAUDE_EFFORT||'';
  const isMax=effort==='max';

  const lines=[];

  // 1. 注入 context-essentials.md (优先项目级, 回落全局)
  let essentialsText='';
  for(const p of [ep,globalEp]){
    try{const t=fs.readFileSync(p,'utf8').trim();if(t){essentialsText=t;break;}}catch(e){}
  }
  if(essentialsText){
    lines.push(essentialsText);
  }else{
    lines.push('[VibeCoding v9.5] TDD · Review · Sisyphus · 设计先行 · 完成度证据 · 出处优先\n[Get-bearings] 读 .ai_state/project.json → 按需 read 其他状态文件');
  }

  // 2. effort=max 时不注入 PACE 状态 (高 effort 模型会自己探索)
  if(!isMax){
    try{
      const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
      if(p.path&&p.stage)lines.push('\n[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
      if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
    }catch(e){}

    // 3. just-in-time: 只给计数, 不粘内容
    try{
      const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
      const pend=(t.match(/^- \[ \].*/gm)||[]).length,done=(t.match(/^- \[x\].*/gm)||[]).length;
      if(pend||done)lines.push('[任务] '+done+'完成 '+pend+'待办 (详情 read .ai_state/tasks.md)');
    }catch(e){}
  }

  if(lines.length===0){process.exit(0);return;}

  const additionalContext=lines.join('\n');
  process.stderr.write('[session-start/'+source+(isMax?'/max':'')+'] injected '+additionalContext.length+' chars\n');
  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'SessionStart',
      additionalContext
    }
  }));
  process.exit(0);
});
