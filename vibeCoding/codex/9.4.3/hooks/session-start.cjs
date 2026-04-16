#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const sd=path.join(process.cwd(),'.ai_state');
const lines=['[VibeCoding] TDD · Review · Sisyphus · 设计先行 · 自审先行'];
lines.push('[Get-bearings] 读 project.json → progress.md → git log → tasks.md');
try{const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
  if(p.path&&p.stage)lines.push('[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
  if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
}catch(e){}
try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const pend=(t.match(/^- \[ \]/gm)||[]).length,done=(t.match(/^- \[x\]/gm)||[]).length;
  if(pend||done)lines.push('[任务] '+done+'完成 '+pend+'待办');
}catch(e){}
if(lines.length>1){
  process.stderr.write('[session-start] injected '+lines.join('\n').length+' chars\n');
  process.stdout.write(JSON.stringify({systemMessage:lines.join('\n')}));
}
process.exit(0);
