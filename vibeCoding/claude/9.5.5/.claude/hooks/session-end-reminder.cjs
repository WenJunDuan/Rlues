#!/usr/bin/env node
'use strict';
// SessionEnd hook (CC 2.1.116+, async:true)
// 退出时检查: tasks 未完成 + git 未提交 → systemMessage 软提示
// 不阻塞退出, 仅打印到 stderr/log
const fs=require('fs'),path=require('path');
const {execSync}=require('child_process');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  // 1. tasks 是否有未完成
  let pendingTasks=0;
  try{
    const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
    pendingTasks=(t.match(/^- \[ \]/gm)||[]).length;
  }catch(e){}

  // 2. git 是否有未提交变更
  let dirtyGit=false;
  try{
    const out=execSync('git status --porcelain 2>/dev/null',{encoding:'utf8',timeout:3000});
    if(out.trim().length>0)dirtyGit=true;
  }catch(e){}

  if(pendingTasks===0&&!dirtyGit){process.exit(0);return;}

  const msgs=[];
  if(pendingTasks>0)msgs.push(pendingTasks+' 个 task 未完成');
  if(dirtyGit)msgs.push('git 工作区有未提交变更');
  const msg='⏰ Hermes 退出提醒: '+msgs.join(', ')+'。下次 /vibe-dev 继续。';
  process.stderr.write('[session-end] '+msg+'\n');

  // hook-trace
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'session-end',pendingTasks,dirtyGit})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}

  // SessionEnd: stdout 输出会作为 systemMessage 显示
  process.stdout.write(JSON.stringify({systemMessage:msg}));
  process.exit(0);
});
