// v9.1.8 SessionStart
const fs=require('fs'),path=require('path');
const S=path.join(process.cwd(),'.ai_state');
try{
  if(fs.existsSync(S)){
    const st=path.join(S,'status.md');
    if(fs.existsSync(st)){
      console.log('[VibeCoding] 未完成会话，读 .ai_state/status.md 恢复。');
      const p=path.join(S,'plan.md');
      if(fs.existsSync(p)){
        const n=(fs.readFileSync(p,'utf8').match(/- \[ \]/g)||[]).length;
        if(n>0) console.log(`[VibeCoding] plan.md 有 ${n} 个未完成任务。`);
      }
    }
  } else console.log('[VibeCoding v9.1.8] 新项目。/vibe-init 或直接描述需求。');
}catch(e){}
