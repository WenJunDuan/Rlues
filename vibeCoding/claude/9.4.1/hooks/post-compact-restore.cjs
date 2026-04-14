#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','riper-pace','context-essentials.md');
const lines=[];
try{const e=fs.readFileSync(ep,'utf8').trim();if(e)lines.push(e);}
catch(e){lines.push('[VibeCoding] TDD · Review · Sisyphus · 设计先行\n[Get-bearings] 读 project.json → progress.md → git log → tasks.md → init.sh');}
try{const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
  if(p.path&&p.stage)lines.push('\n[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
  if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
}catch(e){}
try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const pend=(t.match(/^- \[ \].*/gm)||[]),done=(t.match(/^- \[x\].*/gm)||[]);
  if(pend.length||done.length){lines.push('\n[任务] '+done.length+'完成 '+pend.length+'待办');
    if(pend.length>0&&pend.length<=5)pend.forEach(l=>lines.push('  '+l));
  }
}catch(e){}
if(lines.length>0)process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PostCompact',additionalContext:lines.join('\n')}}));
process.exit(0);
