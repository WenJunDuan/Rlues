#!/usr/bin/env node
'use strict';
// VibeCoding session-end-reminder (v9.5)
// SessionEnd hook (CC v2.1.116+)
// 当用户结束 session 时, 检查 sprint 是否有完成但未提交的 task, 软提醒不阻断

const fs=require('fs'),path=require('path');
const {execSync}=require('child_process');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){}

  // 只处理 clear / logout / quit, 不处理 prompt_input_submit 等无操作 reason
  const reason=event.reason||'';
  if(!/^(clear|logout|quit|prompt_input_submit)$/.test(reason)){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}
  if(!p.path||!p.stage){process.exit(0);return;}

  // 检查 tasks.md 有完成的 task
  let doneCount=0;
  try{
    const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
    doneCount=(t.match(/^- \[x\]/gm)||[]).length;
  }catch(e){}

  // 检查 git 状态: 有未提交的修改吗?
  let hasUncommitted=false;
  try{
    const status=execSync('git status --porcelain 2>/dev/null',{cwd:process.cwd(),encoding:'utf8'});
    hasUncommitted=status.trim().length>0;
  }catch(e){}

  if(doneCount>0&&hasUncommitted){
    const msg=`Sprint ${p.sprint} 已完成 ${doneCount} 个 task, 但有未提交的本地修改。\n`+
              `下次 session 建议: git status → 检查 → git commit (铁律 5: 文档即真相)。`;
    process.stderr.write(`[session-end-reminder] ${reason}: ${doneCount} done, uncommitted changes\n`);
    process.stdout.write(JSON.stringify({systemMessage:'VibeCoding: '+msg}));
  }
  process.exit(0);
});
