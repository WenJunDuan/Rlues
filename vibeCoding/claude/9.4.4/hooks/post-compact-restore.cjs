#!/usr/bin/env node
'use strict';
// PostCompact hook (Claude Code v2.1.76+)
// 触发: compaction 完成后
// 作用: 重新注入 VibeCoding 核心规则 + 项目状态, 对抗 compaction 丢失
// 输出策略: 用 plain stdout + exit 0 注入 context (比 hookSpecificOutput.additionalContext 更兼容)
const fs=require('fs'),path=require('path');
const pd=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const sd=path.join(pd,'.ai_state');
const ep=path.join(pd,'.claude','skills','pace','context-essentials.md');
const lines=[];
let source='fallback';
try{const e=fs.readFileSync(ep,'utf8').trim();if(e){lines.push(e);source='context-essentials.md';}}
catch(e){lines.push('[VibeCoding] TDD · Review · Sisyphus · 设计先行\n[Get-bearings] 读 project.json → progress.md → lessons.md → git log → tasks.md → init.sh');}
try{const p=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));
  if(p.path&&p.stage)lines.push('\n[PACE] Path:'+p.path+' Stage:'+p.stage+' Sprint:'+(p.sprint||0));
  if(p.gotchas&&p.gotchas.length>0)lines.push('[Gotchas] '+p.gotchas.join(' | '));
}catch(e){}
try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  const pend=(t.match(/^- \[ \].*/gm)||[]),done=(t.match(/^- \[x\].*/gm)||[]);
  if(pend.length||done.length){lines.push('\n[任务] '+done.length+'完成 '+pend.length+'待办');
    if(pend.length>0&&pend.length<=5)pend.forEach(l=>lines.push('  '+l));
  }
}catch(e){}
if(lines.length>0){
  const payload=lines.join('\n');
  process.stderr.write('[compact-restore] injected '+payload.length+' chars ('+source+')\n');
  // plain stdout: exit 0 + 内容作为 developer context 追加
  process.stdout.write(payload);
}
process.exit(0);
