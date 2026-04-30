#!/usr/bin/env node
'use strict';
// PostToolUse hook - 自动检测工具失败并起草 ~/.claude/lessons/draft-*.md
// 触发条件: exit_code != 0 + permission denied 字样 + subagent 放弃信号
// 输出: 写文件副作用, 不阻塞工作流 (无 stdout JSON)
// 安全: 写盘前过 redact (token/secret/key 脱敏)

const fs=require('fs'),path=require('path');
const {redact}=require('./_redact.cjs');
const home=process.env.HOME||require('os').homedir();
const lessonsDir=path.join(home,'.claude','lessons');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');

// 触发关键词
const FAILURE_PATTERNS=[
  {pattern:/permission\s+(denied|to use Bash has been denied)/i,topic:'permission'},
  {pattern:/command\s+not\s+found/i,topic:'tool-missing'},
  {pattern:/无\s*Bash\s*工具/i,topic:'subagent-bash'},
  {pattern:/请\s*(您|你)\s*(直接|手动)/,topic:'lazy-fallback'},
  {pattern:/Hook JSON output validation failed/i,topic:'hook-schema'},
  {pattern:/Skill .* is not listed as available/i,topic:'skill-hidden'},
  {pattern:/codex\s+could\s+not\s+run/i,topic:'codex-fail'},
];

let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let event={};
  try{event=JSON.parse(input);}catch(e){process.exit(0);return;}

  // 收集所有可能的输出文本
  const blob=[
    event.tool_response?(typeof event.tool_response==='string'?event.tool_response:JSON.stringify(event.tool_response)):'',
    event.tool_output?(typeof event.tool_output==='string'?event.tool_output:JSON.stringify(event.tool_output)):'',
    event.stderr||'',
  ].join('\n');

  if(!blob.trim()){process.exit(0);return;}

  // 找匹配
  const hit=FAILURE_PATTERNS.find(({pattern})=>pattern.test(blob));
  if(!hit){process.exit(0);return;}

  // 起草 draft (一次失败一个文件, 用时间戳避免覆盖)
  fs.mkdirSync(path.join(lessonsDir,'archive'),{recursive:true});
  const date=new Date().toISOString().slice(0,10);
  const time=new Date().toISOString().slice(11,19).replace(/:/g,'');
  const slug=hit.topic;
  const fname=path.join(lessonsDir,'draft-'+date+'-'+slug+'-'+time+'.md');

  // 取项目状态
  let projectInfo='';
  try{
    const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
    if(p.path)projectInfo=p.path+'/'+(p.stage||'-')+'/sprint'+(p.sprint||0);
  }catch(e){}

  const tool=event.tool_name||'unknown';
  const cmdRaw=(event.tool_input&&event.tool_input.command)||'(non-bash tool)';
  const cmd=redact(cmdRaw);
  const blobShortRaw=blob.length>2000?blob.slice(0,2000)+'\n...(truncated)':blob;
  const blobShort=redact(blobShortRaw);

  const content=`---
date: ${date}
context: ${hit.topic}
severity: warning
status: unresolved
auto_drafted: true
session_id: ${event.session_id||'unknown'}
project: ${projectInfo||'-'}
---

# 自动起草: ${hit.topic} 触发

## 触发场景

- 工具: ${tool}
- 命令/参数: \`${cmd.slice(0,200)}\`
- 时间: ${new Date().toISOString()}
- 当前 PACE: ${projectInfo||'(无)'}

## 完整输出

\`\`\`
${blobShort}
\`\`\`

## 现象
<!-- 用户补全: 看到的具体行为 -->

## 根因
<!-- 用户补全 / 待 Claude 后续调研 -->

## 已尝试方案
<!-- 用户补全: -->

## 当前 workaround
<!-- 用户补全 -->

## 相关
- VibeCoding 版本: 9.4.5
- 用 /lesson-curator 审阅本 draft 后改名落档 (改成 ${date}-{slug}.md 格式)
- 7 天未确认会自动归档到 archive/
`;

  try{
    fs.writeFileSync(fname,content);
    process.stderr.write('[lesson-drafter] 起草: '+path.basename(fname)+' ('+hit.topic+')\n');

    // hook-trace
    try{
      const line=JSON.stringify({ts:new Date().toISOString(),hook:'lesson-drafter',topic:hit.topic,draft:path.basename(fname)})+'\n';
      fs.appendFileSync(path.join(sd,'hook-trace.jsonl'),line);
    }catch(e){}
  }catch(e){
    process.stderr.write('[lesson-drafter] 起草失败: '+e.message+'\n');
  }

  process.exit(0);
});
