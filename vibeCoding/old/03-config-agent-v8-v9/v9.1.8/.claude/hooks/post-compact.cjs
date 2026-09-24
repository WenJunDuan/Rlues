// v9.1.8 PostCompact: 状态保存+Sisyphus恢复
const fs=require('fs'),path=require('path');
const S=path.join(process.cwd(),'.ai_state');
try{
  if(fs.existsSync(S)){
    const sf=path.join(S,'status.md');
    if(fs.existsSync(sf)){
      let c=fs.readFileSync(sf,'utf8');
      const ts=new Date().toISOString();
      c=c.replace(/## 最后更新.*$/m,`## 最后更新\n${ts} (compact)`);
      if(c.includes('最后更新')) fs.writeFileSync(sf,c);
    }
    const pf=path.join(S,'plan.md');
    if(fs.existsSync(pf)){
      const n=(fs.readFileSync(pf,'utf8').match(/- \[ \]/g)||[]).length;
      if(n>0) console.log(`[VibeCoding] compact完成。${n} 个未完成任务。读 status.md+plan.md 继续。`);
      else console.log('[VibeCoding] compact完成，任务全完成。');
    } else console.log('[VibeCoding] compact完成。');
  }
}catch(e){}
