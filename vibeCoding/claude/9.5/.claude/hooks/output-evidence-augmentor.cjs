#!/usr/bin/env node
'use strict';
// VibeCoding output-evidence-augmentor (v9.5)
// PostToolUse hook, 利用 v2.1.117+ 的 hookSpecificOutput.updatedToolOutput 改写当前 tool 输出
//
// 策略 (修正后):
//   - 不读 transcript JSONL (太重)
//   - 自维护 ~/.claude/state/recent-tool-uses.jsonl (ring buffer 50 条)
//   - 每次 PostToolUse:
//       1. append 当前 tool_use 简短记录
//       2. 仅在 stage="review" 且 tool 是 Edit/Write 时, 检查 ring buffer 是否含 reviewer 调用证据
//       3. 没证据 → updatedToolOutput 在原输出后追加 "⚠ 提示" 行
//
// 注意: updatedToolOutput 是改写当前 tool 的输出, 不是 systemMessage. agent 看到带 ⚠ 提示的输出会响应。

const fs=require('fs'),path=require('path'),os=require('os');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');
const stateDir=path.join(os.homedir(),'.claude','state');
const ringFile=path.join(stateDir,'recent-tool-uses.jsonl');
const RING_SIZE=50;

// === ring buffer 维护 ===

function appendRing(entry){
  try{
    fs.mkdirSync(stateDir,{recursive:true});
    fs.appendFileSync(ringFile,JSON.stringify(entry)+'\n');
    // 截断: 超过 RING_SIZE 行就只保留尾部
    const lines=fs.readFileSync(ringFile,'utf8').split('\n').filter(Boolean);
    if(lines.length>RING_SIZE){
      const kept=lines.slice(-RING_SIZE);
      fs.writeFileSync(ringFile,kept.join('\n')+'\n');
    }
  }catch(e){}
}

function readRing(){
  try{
    return fs.readFileSync(ringFile,'utf8').split('\n').filter(Boolean).map(l=>{
      try{return JSON.parse(l);}catch(e){return null;}
    }).filter(Boolean);
  }catch(e){return [];}
}

// === 主逻辑 ===

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  const tool=event.tool_name||'unknown';

  // 1. 维护 ring buffer (所有 tool_use 都记一行)
  appendRing({
    ts:new Date().toISOString(),
    tool,
    has_error: !!(event.tool_response&&typeof event.tool_response==='string'&&/error|fail/i.test(event.tool_response)),
    is_subagent_tool: /Task|spawn|subagent|reviewer|evaluator|generator|codex/i.test(tool),
  });

  // 2. 仅 review 阶段 + Edit/Write 触发证据检查
  if(!/^(Edit|Write|MultiEdit)$/.test(tool)){process.exit(0);return;}

  let p={};
  try{p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){process.exit(0);return;}
  if(p.stage!=='review'){process.exit(0);return;}

  // Hotfix/Bugfix/Quick 不强制要求 reviewer 证据
  if(!['Feature','Refactor','System'].includes(p.path)){process.exit(0);return;}

  // 3. 检查 ring buffer 中近 30 条是否有 reviewer/codex/Task 调用
  const ring=readRing();
  const recent=ring.slice(-30);
  const hasReviewerEvidence=recent.some(e=>e.is_subagent_tool);

  if(hasReviewerEvidence){process.exit(0);return;}

  // 4. 没证据 → updatedToolOutput 改写
  const originalOutput=(typeof event.tool_response==='string')?event.tool_response:JSON.stringify(event.tool_response||'');
  const augmented=originalOutput+
    '\n\n---\n'+
    '💡 Hermes 提示 (review 阶段证据检查):\n'+
    '本次 Edit 在 review 阶段执行, 但近 30 个 tool_use 中未见 reviewer/codex 调用记录。\n'+
    `路径 "${p.path}" 要求外部审查 (Feature+ 必须). 完成度证据要求 (CLAUDE.md): 跨模型审查必须有 codex job ID 或命令输出片段。\n`+
    '建议: 完成本次 edit 后先 spawn /codex:review 或对位 reviewer subagent, 再写入 reviews/sprint-N.md。\n'+
    '此提示是 hint, 不阻止当前 tool 执行。';

  process.stdout.write(JSON.stringify({
    hookSpecificOutput:{
      hookEventName:'PostToolUse',
      updatedToolOutput:augmented,
    }
  }));
  process.stderr.write(`[output-evidence-augmentor] review 阶段 ${tool} 缺 reviewer 证据, 已追加提示\n`);
  process.exit(0);
});
