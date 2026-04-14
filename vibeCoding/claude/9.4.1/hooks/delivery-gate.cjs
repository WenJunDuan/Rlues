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
  if(!p.sprint||!p.stage||p.path==='A'||!(p.stage==='T'||p.stage==='V')){process.exit(0);return;}
  const issues=[];
  try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
    const n=(t.match(/^- \[ \]/gm)||[]).length;
    if(n>0)issues.push(n+' Task 未完成');
  }catch(e){issues.push('tasks.md 不存在');}
  const rf=path.join(sd,'reviews','sprint-'+p.sprint+'.md');
  let rc='';
  try{rc=fs.readFileSync(rf,'utf8');}catch(e){issues.push('审查报告不存在');}
  if(rc&&!/codex:review|codex:result|adversarial|ecc-agentshield/i.test(rc))issues.push('无外部审查记录');
  if(rc&&!/test|测试|pass|通过|✅/i.test(rc))issues.push('无测试通过记录');
  if(rc){const m=rc.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
    if(m){const v=m[1].toUpperCase();
      if(v==='REWORK')issues.push('VERDICT=REWORK');
      else if(v==='FAIL')issues.push('VERDICT=FAIL');
      else if(v==='CONCERNS')process.stderr.write('[delivery-gate] CONCERNS: 建议修复后重新评分\n');
    }
  }
  if(issues.length>0){
    process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'Stop',stopDecision:'block',
      stopDecisionReason:'[delivery-gate] 阻断:\n'+issues.map(i=>'• '+i).join('\n')+'\n\n修复后再交付。'}}));
  }
  process.exit(0);
});
