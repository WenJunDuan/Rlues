#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// hook-trace 写入辅助函数
function trace(event){
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'delivery-gate',...event})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}
}

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){}
  if(event.stop_hook_active){process.exit(0);return;}

  // 仅对主 agent 触发, 跳过 subagent (避免 codex-rescue 等触发)
  if(event.agent_type&&event.agent_type!=='main'){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}
  if(!p.sprint||!p.stage||p.path==='Hotfix'||p.stage!=='review'){process.exit(0);return;}

  const issues=[];
  const needsExtReview=['Feature','Refactor','System'].includes(p.path);

  try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
    const n=(t.match(/^- \[ \]/gm)||[]).length;
    if(n>0)issues.push(n+' Task 未完成');
  }catch(e){issues.push('tasks.md 不存在');}

  const rf=path.join(sd,'reviews','sprint-'+p.sprint+'.md');
  let rc='';
  try{rc=fs.readFileSync(rf,'utf8');}catch(e){issues.push('审查报告不存在');}

  if(needsExtReview&&rc&&!/\/codex:review|\/codex:adversarial|adversarial|ecc-agentshield|codex unavailable/i.test(rc)){
    issues.push('无外部审查记录');
  }
  if(rc&&!/test|测试|pass|通过|✅/i.test(rc))issues.push('无测试通过记录');

  let verdict='';
  if(rc){
    const m=rc.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
    if(m){
      verdict=m[1].toUpperCase();
      if(verdict==='REWORK')issues.push('VERDICT=REWORK');
      else if(verdict==='FAIL')issues.push('VERDICT=FAIL');
      else if(verdict==='CONCERNS')process.stderr.write('[delivery-gate] CONCERNS: 建议修复后重新评分\n');
    }
  }

  if(issues.length>0){
    process.stderr.write('[delivery-gate] 阻断 '+p.path+'/'+p.stage+': '+issues.join(', ')+'\n');
    trace({action:'block',path:p.path,stage:p.stage,sprint:p.sprint,issues});
    // 顶层 decision + reason (v9.4.5 协议修正)
    process.stdout.write(JSON.stringify({
      decision:'block',
      reason:'[delivery-gate] 阻断:\n'+issues.map(i=>'• '+i).join('\n')+'\n\n修复后再交付。'
    }));
    process.exit(0);return;
  }

  if(verdict==='PASS'){
    let compounded=false;
    try{const lm=fs.readFileSync(path.join(sd,'lessons.md'),'utf8');
      compounded=lm.includes('Sprint '+p.sprint);
    }catch(e){}
    if(!compounded){
      const msg='⚠ Sprint '+p.sprint+' 通过但 lessons.md 无条目, 建议运行 /compound 沉淀经验 (铁律 7)';
      process.stderr.write('[delivery-gate] PASS '+p.path+'/'+p.stage+' · '+msg+'\n');
      trace({action:'soft-warn',path:p.path,stage:p.stage,sprint:p.sprint,reason:'no compound'});
      process.stdout.write(JSON.stringify({systemMessage:'VibeCoding: '+msg}));
    }else{
      process.stderr.write('[delivery-gate] PASS '+p.path+'/'+p.stage+' · lessons ✓\n');
      trace({action:'pass',path:p.path,stage:p.stage,sprint:p.sprint});
    }
  }else{
    process.stderr.write('[delivery-gate] 放行 '+p.path+'/'+p.stage+'\n');
    trace({action:'pass',path:p.path,stage:p.stage,sprint:p.sprint,verdict});
  }
  process.exit(0);
});
