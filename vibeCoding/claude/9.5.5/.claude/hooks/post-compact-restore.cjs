#!/usr/bin/env node
'use strict';
// PostCompact hook v9.5
// 输出策略: plain stdout (PostCompact 没有 decision control)
// 设计: just-in-time, 不预加载 tasks 内容, 只给计数
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','pace','context-essentials.md');
const home=process.env.HOME||require('os').homedir();
const globalEp=path.join(home,'.claude','skills','pace','context-essentials.md');

const lines=[];

let essentialsText='';
for(const p of [ep,globalEp]){
  try{const t=fs.readFileSync(p,'utf8').trim();if(t){essentialsText=t;break;}}catch(e){}
}
if(essentialsText){
  lines.push(essentialsText);
}else{
  lines.push('[VibeCoding v9.5] TDD · Review · Sisyphus · 设计先行 · 完成度证据 · 出处优先\n[Get-bearings] 读 .ai_state/project.json → 按需 read 其他状态文件');
}

try{
  const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
  if(p.path&&p.stage)lines.push('\n[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
  if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
}catch(e){}

try{
  const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const pend=(t.match(/^- \[ \].*/gm)||[]).length,done=(t.match(/^- \[x\].*/gm)||[]).length;
  if(pend||done)lines.push('[任务] '+done+'完成 '+pend+'待办 (详情 read .ai_state/tasks.md)');
}catch(e){}

if(lines.length>0){
  const payload=lines.join('\n');
  process.stderr.write('[compact-restore] injected '+payload.length+' chars\n');
  process.stdout.write(payload);
}
process.exit(0);
