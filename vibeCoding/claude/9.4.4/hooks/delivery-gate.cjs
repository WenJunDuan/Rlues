#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  try{if(JSON.parse(input).stop_hook_active){process.exit(0);return;}}catch(e){}
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
  if(needsExtReview&&rc&&!/\/codex:review|\/codex:adversarial|adversarial|ecc-agentshield/i.test(rc))issues.push('无外部审查记录');
  if(rc&&!/test|测试|pass|通过|✅/i.test(rc))issues.push('无测试通过记录');
  let verdict='';
  if(rc){const m=rc.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
    if(m){verdict=m[1].toUpperCase();
      if(verdict==='REWORK')issues.push('VERDICT=REWORK');
      else if(verdict==='FAIL')issues.push('VERDICT=FAIL');
      else if(verdict==='CONCERNS')process.stderr.write('[delivery-gate] CONCERNS: 建议修复后重新评分\n');
    }
  }
  if(issues.length>0){
    process.stderr.write('[delivery-gate] 阻断 '+p.path+'/'+p.stage+': '+issues.join(', ')+'\n');
    process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'Stop',stopDecision:'block',
      stopDecisionReason:'[delivery-gate] 阻断:\n'+issues.map(i=>'• '+i).join('\n')+'\n\n修复后再交付。'}}));
    process.exit(0);return;
  }
  // Gate PASS: 检查本 Sprint 是否已沉淀经验 (soft warn, 不阻塞)
  if(verdict==='PASS'){
    let compounded=false;
    try{const lm=fs.readFileSync(path.join(sd,'lessons.md'),'utf8');
      const tag='Sprint '+p.sprint;
      compounded=lm.includes(tag);
    }catch(e){}
    if(!compounded){
      process.stderr.write('[delivery-gate] PASS '+p.path+'/'+p.stage+' · ⚠ lessons.md 无 Sprint '+p.sprint+' 条目, 建议运行 /compound 沉淀经验 (铁律 7)\n');
    }else{
      process.stderr.write('[delivery-gate] PASS '+p.path+'/'+p.stage+' · lessons ✓\n');
    }
  }else{
    process.stderr.write('[delivery-gate] 放行 '+p.path+'/'+p.stage+'\n');
  }
  process.exit(0);
});
