#!/usr/bin/env node
'use strict';
// VibeCoding TaskCreated 软提示 hook (v9.5)
// 协议: TaskCreated event (CC v2.1.84+)
// 策略: 仅 systemMessage 不阻断 (避免死锁)
//
// 检测当前 stage 与 task subject 是否一致, 不一致只提醒不拦下:
//   stage="plan"  + task subject 含 "implement|write|create|build" → 提醒
//   stage="impl"  + task subject 含 "design|plan|architect" → 提醒
//   stage="review" + task subject 含 "implement|fix" → 提醒 (review 阶段不该改代码)

const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

function trace(event){
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'task-created-advisor',...event})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}
}

const STAGE_CONFLICT_PATTERNS = {
  'plan':   /\b(implement|write code|create code|build|coding|编码|实现|写代码)\b/i,
  'impl':   /\b(design|architect|plan|architecture|架构|规划|设计文档)\b/i,
  'review': /\b(implement|fix bug|add feature|new functionality|实现|修 bug|加功能)\b/i,
};

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  const subject=event.task_subject||'';
  if(!subject){process.exit(0);return;}

  // 读 project.json 拿当前 stage
  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}
  const stage=p.stage||'';
  if(!stage){process.exit(0);return;}

  const pattern=STAGE_CONFLICT_PATTERNS[stage];
  if(!pattern||!pattern.test(subject)){process.exit(0);return;}

  // 命中冲突 → 软提醒
  const msg=`Hermes 提醒: 当前 stage="${stage}", 即将创建 task "${subject.slice(0,60)}"。\n`+
            `这个 task 的语义不像 ${stage} 阶段该做的事。\n`+
            `如果你已完成本阶段想转下一阶段, 请先确认 .ai_state/ 文件齐全 (delivery-gate 会检查)。\n`+
            `如果是误判, 忽略此提示继续。`;

  process.stderr.write(`[task-created-advisor] stage=${stage} subject=${subject.slice(0,40)}: 语义不一致提醒\n`);
  trace({stage,subject:subject.slice(0,80),task_id:event.task_id});

  // 不阻断, 只发 systemMessage
  process.stdout.write(JSON.stringify({systemMessage:'VibeCoding: '+msg}));
  process.exit(0);
});
