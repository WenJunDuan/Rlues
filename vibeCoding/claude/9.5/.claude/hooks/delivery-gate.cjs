#!/usr/bin/env node
'use strict';
// VibeCoding delivery-gate v9.5
// 升级: 状态机硬化, 全 stage 转换条件检查 (不止 review→ship)
//
// 协议: Stop hook
//   通过: exit 0 + 可选 systemMessage
//   不通过: exit 0 + {decision:"block", reason:<具体修复指令>}

const fs=require('fs'),path=require('path');
const {redact}=require('./_redact.cjs');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// === 状态机转换规则 (v9.5 核心) ===
// 每个 stage 的 "出口条件" - 想离开该 stage 必须满足
// 此处条件不达标 → block + reason
const STAGE_EXIT_RULES = {
  // plan 阶段出口: 想转 impl 必须有 design + tasks
  plan: {
    require: [
      {check: 'file', target: 'design.md', desc: 'design.md 不存在'},
      {check: 'file', target: 'tasks.md', desc: 'tasks.md 不存在'},
      {check: 'has-pending-task', desc: 'tasks.md 没有 - [ ] 待办'},
      {check: 'has-section', target: 'design.md', section: 'File Structure Plan', desc: 'design.md 缺 ## File Structure Plan 段'},
      // modify-existing 场景额外要求 change-plan.md
      {check: 'scenario-conditional', scenario: 'modify-existing', target: 'change-plan.md', desc: 'modify-existing 场景: change-plan.md 必须存在 (图 06: 改已有项目先勘察)'},
    ],
  },
  // design 阶段 (System only)
  design: {
    require: [
      {check: 'file', target: 'design.md'},
      {check: 'has-section', target: 'design.md', section: 'File Structure Plan'},
      {check: 'file', target: 'tasks.md'},
      {check: 'tasks-have-boundary', desc: 'tasks.md 中 task 缺 _Boundary:_ 标注 (cc-sdd 边界优先)'},
    ],
  },
  // impl 阶段出口: 想转 review 必须 tasks 全完成 + progress 有记录
  impl: {
    require: [
      {check: 'all-tasks-done', desc: 'tasks.md 还有 - [ ] 待办未完成'},
      {check: 'has-progress', desc: 'progress.md 没有本 sprint 的记录'},
    ],
  },
  // review 阶段出口: 想转 ship 必须 reviews 报告 + 测试 + (Feature+ 外部审查) + VERDICT
  review: {
    require: [
      {check: 'review-report', desc: 'reviews/sprint-N.md 不存在'},
      {check: 'review-has-test', desc: '审查报告无测试通过记录'},
      {check: 'review-has-external', desc: 'Feature+ 路径审查报告缺外部审查 (codex/reviewer)'},
      {check: 'verdict-ok', desc: 'VERDICT 不是 PASS 或 CONCERNS'},
    ],
  },
};

// === 辅助函数 ===

function trace(event){
  try{
    const line=JSON.stringify({ts:new Date().toISOString(),hook:'delivery-gate',...event})+'\n';
    fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
  }catch(e){}
}

function safeRead(p){
  try{return fs.readFileSync(p,'utf8');}catch(e){return null;}
}

function checkRule(rule,project){
  const sprint=project.sprint||0;
  switch(rule.check){
    case 'file':{
      return fs.existsSync(path.join(sd,rule.target));
    }
    case 'has-pending-task':{
      const t=safeRead(path.join(sd,'tasks.md'))||'';
      return /^- \[ \]/m.test(t);
    }
    case 'all-tasks-done':{
      const t=safeRead(path.join(sd,'tasks.md'))||'';
      const pending=(t.match(/^- \[ \]/gm)||[]).length;
      return pending===0;
    }
    case 'has-section':{
      const t=safeRead(path.join(sd,rule.target))||'';
      return new RegExp('^##+\\s+'+rule.section,'mi').test(t);
    }
    case 'has-progress':{
      const t=safeRead(path.join(sd,'progress.md'))||'';
      return new RegExp(`sprint/${sprint}|/sprint${sprint}|sprint ${sprint}`,'i').test(t);
    }
    case 'tasks-have-boundary':{
      const t=safeRead(path.join(sd,'tasks.md'))||'';
      const taskLines=t.match(/^- \[[ x]\] Task/gm)||[];
      if(taskLines.length===0)return true; // 没 task 不检查
      return /_Boundary:_/i.test(t);
    }
    case 'review-report':{
      return fs.existsSync(path.join(sd,'reviews',`sprint-${sprint}.md`));
    }
    case 'review-has-test':{
      const r=safeRead(path.join(sd,'reviews',`sprint-${sprint}.md`))||'';
      return /test|测试|pass|通过|✅/i.test(r);
    }
    case 'review-has-external':{
      const needsExt=['Feature','Refactor','System'].includes(project.path);
      if(!needsExt)return true;
      const r=safeRead(path.join(sd,'reviews',`sprint-${sprint}.md`))||'';
      return /\/codex:review|\/codex:adversarial|adversarial|ecc-agentshield|reviewer|codex unavailable|review unavailable/i.test(r);
    }
    case 'verdict-ok':{
      const r=safeRead(path.join(sd,'reviews',`sprint-${sprint}.md`))||'';
      const m=r.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
      if(!m)return false;
      const v=m[1].toUpperCase();
      return v==='PASS'||v==='CONCERNS';
    }
    case 'scenario-conditional':{
      const scenario=project.scenario||'';
      if(scenario!==rule.scenario)return true; // 不在该场景下视为通过
      return fs.existsSync(path.join(sd,rule.target));
    }
  }
  return true;
}

function describeRule(rule){
  if(rule.desc)return rule.desc;
  if(rule.check==='file')return `${rule.target} 不存在`;
  return rule.check;
}

// === 主逻辑 ===

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){}
  if(event.stop_hook_active){process.exit(0);return;}

  // 仅对主 agent 触发, 跳过 subagent
  if(event.agent_type&&event.agent_type!=='main'){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}

  // Hotfix/Bugfix 不走完整 PACE, 只在 review 时弱检查
  if(p.path==='Hotfix'||p.path==='Bugfix'){process.exit(0);return;}

  // 没有 stage 表示已完成 (sprint=N+1, stage="")
  if(!p.stage){process.exit(0);return;}

  // 查找当前 stage 的出口规则
  const rules=STAGE_EXIT_RULES[p.stage];
  if(!rules){process.exit(0);return;}

  // 检查所有规则
  const failed=[];
  for(const rule of rules.require){
    if(!checkRule(rule,p)){
      failed.push(describeRule(rule));
    }
  }

  if(failed.length===0){
    // 全部通过 → 检查 review 阶段额外的 lessons 提醒
    if(p.stage==='review'){
      const lm=safeRead(path.join(sd,'lessons.md'))||'';
      const compounded=new RegExp(`Sprint ${p.sprint}\\b`).test(lm);
      if(!compounded){
        const msg=`⚠ Sprint ${p.sprint} 通过但 lessons.md 无条目, 建议运行 /compound 沉淀经验 (铁律 7)`;
        process.stderr.write(`[delivery-gate] review->ship soft-warn: ${msg}\n`);
        trace({action:'soft-warn',path:p.path,stage:p.stage,sprint:p.sprint,reason:'no compound'});
        process.stdout.write(JSON.stringify({systemMessage:'VibeCoding: '+msg}));
        process.exit(0);return;
      }
    }
    process.stderr.write(`[delivery-gate] ${p.path}/${p.stage} 出口检查通过\n`);
    trace({action:'pass',path:p.path,stage:p.stage,sprint:p.sprint});
    process.exit(0);return;
  }

  // 有失败规则 → block + 具体修复指令
  const reason=`[delivery-gate] ${p.path}/${p.stage} 阶段出口条件未满足:\n`+
               failed.map(f=>'  • '+f).join('\n')+
               '\n\n请修复以上问题后再交付。如确认本阶段已完成, 检查 .ai_state/ 文件是否齐全。';

  process.stderr.write(`[delivery-gate] BLOCK ${p.path}/${p.stage}: ${failed.join(', ')}\n`);
  trace({action:'block',path:p.path,stage:p.stage,sprint:p.sprint,failed:failed});

  process.stdout.write(JSON.stringify({
    decision:'block',
    reason:reason
  }));
  process.exit(0);
});
