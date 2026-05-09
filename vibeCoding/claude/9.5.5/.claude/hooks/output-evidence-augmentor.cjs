#!/usr/bin/env node
'use strict';
// PostToolUse hook (CC 2.1.121+): hookSpecificOutput.updatedToolOutput
// 在 review 阶段的 Edit/Write 后, 如果还没有 review-report.md, 在工具输出尾部追加软提示。
// 默认 DISABLED, 用户在 settings.json 显式开启。
//
// 启用方式 (~/.claude/settings.json):
//   "env": { ..., "VIBECODING_AUGMENTOR": "1" }
//
// 触发条件 (全部满足):
//   - env.VIBECODING_AUGMENTOR === "1"
//   - tool ∈ {Edit, Write, MultiEdit}
//   - .ai_state/project.json: stage === "review" && path ∈ {Feature, Refactor, System}
//   - .ai_state/reviews/sprint-{N}.md 不存在或为空

const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

if(process.env.VIBECODING_AUGMENTOR!=='1'){process.exit(0);}

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  const toolName=event.tool_name||'';
  if(!['Edit','Write','MultiEdit'].includes(toolName)){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}
  if(p.stage!=='review'||!['Feature','Refactor','System'].includes(p.path)){process.exit(0);return;}

  // 是否已有 review-report.md
  const rp=path.join(sd,'reviews','sprint-'+(p.sprint||0)+'.md');
  let hasReport=false;
  try{
    const st=fs.statSync(rp);
    if(st.size>20)hasReport=true;
  }catch(e){}
  if(hasReport){process.exit(0);return;}

  // 构造 mutation: 在工具输出尾部追加一行软提示
  const orig=event.tool_response||event.tool_output||'';
  const origStr=typeof orig==='string'?orig:JSON.stringify(orig);
  const augment='\n\n💡 Hermes 提示: 当前在 '+p.path+'/review 阶段，但 .ai_state/reviews/sprint-'+(p.sprint||0)+'.md 尚未生成。\n按审查协议: /review → /codex:review (Feature+) → @evaluator → 写入报告。';

  process.stderr.write('[output-augmentor] augmented '+toolName+' output (review/'+p.path+')\n');

  // hook-trace
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'output-augmentor',tool:toolName,path:p.path,stage:p.stage})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}

  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PostToolUse',
      updatedToolOutput:origStr+augment
    }
  }));
  process.exit(0);
});
