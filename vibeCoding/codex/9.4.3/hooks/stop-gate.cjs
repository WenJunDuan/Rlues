#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const sd=path.join(process.cwd(),'.ai_state');
let p={};
try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);}
if(!p.sprint||!p.stage||p.path==='Hotfix'||p.path==='Bugfix'||p.stage!=='review'){process.exit(0);}
const issues=[];
const needsExtReview=['Feature','Refactor','System'].includes(p.path);
try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const n=(t.match(/^- \[ \]/gm)||[]).length;
  if(n>0)issues.push(n+' Task 未完成');
}catch(e){issues.push('tasks.md 不存在');}
const rf=path.join(sd,'reviews','sprint-'+p.sprint+'.md');
let rc='';
try{rc=fs.readFileSync(rf,'utf8');}catch(e){issues.push('审查报告不存在');}
if(needsExtReview&&rc&&!/review|adversarial|security.scan/i.test(rc))issues.push('无外部审查记录');
if(rc&&!/test|测试|pass|通过|✅/i.test(rc))issues.push('无测试通过记录');
if(rc){const m=rc.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
  if(m){const v=m[1].toUpperCase();
    if(v==='REWORK')issues.push('VERDICT=REWORK');
    else if(v==='FAIL')issues.push('VERDICT=FAIL');
    else if(v==='CONCERNS')process.stderr.write('[stop-gate] CONCERNS: 建议修复后重新评分\n');
  }
}
if(issues.length>0){
  process.stderr.write('[stop-gate] 阻断 '+p.path+'/'+p.stage+': '+issues.join(', ')+'\n');
  process.exit(2);
}
process.stderr.write('[stop-gate] 放行 '+p.path+'/'+p.stage+'\n');
process.exit(0);
