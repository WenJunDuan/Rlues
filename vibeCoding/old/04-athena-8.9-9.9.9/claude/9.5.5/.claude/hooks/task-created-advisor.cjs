#!/usr/bin/env node
'use strict';
// TaskCreated hook (CC 2.1.116+, async:true)
// 检测主题与当前 PACE stage 不符时软提示, 不阻断
// 例: plan 阶段创建 "implement xxx" 任务 → 提示"当前是 plan, 建议先完成设计"
const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// stage → 不应出现的关键词
const STAGE_CONFLICTS={
  plan:[
    /\b(implement|build|create|write code|实现|写代码|开发)\b/i,
    /\b(deploy|release|ship|发布|部署)\b/i,
    /\b(refactor|重构)\b/i,
  ],
  design:[
    /\b(implement|实现|写代码)\b/i,
    /\b(deploy|发布|部署)\b/i,
  ],
  impl:[
    /\b(redesign|重新设计|重新规划)\b/i,
  ],
  review:[
    /\b(implement|new feature|新功能|新增)\b/i,
    /\b(redesign|重新设计)\b/i,
  ],
  ship:[
    /\b(implement|new feature|redesign|重做)\b/i,
  ],
};

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  // TaskCreated 输入: tool_input 含 description
  const desc=(event.tool_input&&(event.tool_input.description||event.tool_input.prompt))||'';
  if(!desc){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}

  const stage=p.stage||'';
  const conflicts=STAGE_CONFLICTS[stage]||[];
  const matched=conflicts.find(re=>re.test(desc));
  if(!matched){process.exit(0);return;}

  const msg='⚠ Hermes 阶段一致性提醒: 当前 '+p.path+'/'+stage+', 但任务主题"'+desc.slice(0,60)+'..." 看起来像下一阶段动作。建议先完成当前阶段。';
  process.stderr.write('[task-advisor] '+msg+'\n');

  // hook-trace
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'task-advisor',stage,signal:matched.toString().slice(0,40)})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}

  // 软提示, 不阻断
  process.stdout.write(JSON.stringify({systemMessage:msg}));
  process.exit(0);
});
