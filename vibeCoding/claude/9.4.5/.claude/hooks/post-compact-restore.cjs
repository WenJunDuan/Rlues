#!/usr/bin/env node
'use strict';
// PostCompact hook (CC v2.1.76+) - 作为 SessionStart compact matcher 的兜底
// 输出策略: plain stdout (不是 JSON), 因为 PostCompact "no decision control"
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','pace','context-essentials.md');
const home=process.env.HOME||require('os').homedir();
const globalEp=path.join(home,'.claude','skills','pace','context-essentials.md');

const lines=[];
let source='fallback';

let essentialsText='';
for(const p of [ep,globalEp]){
  try{const t=fs.readFileSync(p,'utf8').trim();if(t){essentialsText=t;source=p;break;}}catch(e){}
}
if(essentialsText){
  lines.push(essentialsText);
}else{
  lines.push('[VibeCoding] TDD · Review · Sisyphus · 设计先行 · 不懒惰 · 穷尽调研\n[Get-bearings] 扫 ~/.claude/lessons/INDEX.md → 项目 .ai_state/');
}

try{
  const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
  if(p.path&&p.stage)lines.push('\n[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
  if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
}catch(e){}

try{
  const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const pend=(t.match(/^- \[ \].*/gm)||[]),done=(t.match(/^- \[x\].*/gm)||[]);
  if(pend.length||done.length){
    lines.push('\n[任务] '+done.length+'完成 '+pend.length+'待办');
    if(pend.length>0&&pend.length<=5)pend.forEach(l=>lines.push('  '+l));
  }
}catch(e){}

if(lines.length>0){
  const payload=lines.join('\n');
  process.stderr.write('[compact-restore] injected '+payload.length+' chars ('+source+')\n');
  process.stdout.write(payload);
}
process.exit(0);
