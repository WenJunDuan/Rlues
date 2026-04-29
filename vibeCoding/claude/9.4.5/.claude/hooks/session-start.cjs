#!/usr/bin/env node
'use strict';
// SessionStart hook (CC v2.1.x)
// 4 matcher: startup / resume / clear / compact
// 输出协议: hookSpecificOutput.additionalContext (官方 SessionStart spec)
//   或 plain stdout (兼容路径)
// 这里用 hookSpecificOutput, 因为官方 schema 明确支持
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','pace','context-essentials.md');
const home=process.env.HOME||require('os').homedir();
const globalEp=path.join(home,'.claude','skills','pace','context-essentials.md');

// 顺手跑一次 lesson-archiver (7 天 draft 自动归档)
try{
  const archiver=path.join(home,'.claude','hooks','lesson-archiver.cjs');
  if(fs.existsSync(archiver)){
    const r=require(archiver);
    if(r&&r.archived>0)process.stderr.write('[session-start] '+r.archived+' draft 已归档\n');
  }
}catch(e){}

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){}
  const source=event.source||'unknown';

  const lines=[];
  let essentialsSource='fallback';

  // 1. 注入 context-essentials.md (优先项目级, 回落全局)
  let essentialsText='';
  for(const p of [ep,globalEp]){
    try{const t=fs.readFileSync(p,'utf8').trim();if(t){essentialsText=t;essentialsSource=p;break;}}catch(e){}
  }
  if(essentialsText){
    lines.push(essentialsText);
  }else{
    lines.push('[VibeCoding] TDD · Review · Sisyphus · 设计先行 · 不懒惰 · 穷尽调研\n[Get-bearings] 扫 ~/.claude/lessons/INDEX.md → 项目 .ai_state/');
  }

  // 2. 注入全局 lessons INDEX (R₀ 第 1 步要扫)
  const indexPath=path.join(home,'.claude','lessons','INDEX.md');
  try{
    const idx=fs.readFileSync(indexPath,'utf8');
    if(idx.length>0&&idx.length<3000){
      lines.push('\n--- ~/.claude/lessons/INDEX.md ---');
      lines.push(idx);
    }else if(idx.length>=3000){
      lines.push('\n[Global Lessons] INDEX.md 过长 ('+idx.length+' chars), 主动 cat 查看');
    }
  }catch(e){}

  // 3. 注入项目状态
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

  if(lines.length===0){process.exit(0);return;}

  const additionalContext=lines.join('\n');
  process.stderr.write('[session-start/'+source+'] injected '+additionalContext.length+' chars\n');
  // SessionStart 官方协议: hookSpecificOutput.additionalContext
  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'SessionStart',
      additionalContext
    }
  }));
  process.exit(0);
});
