// v9.1.8 StopFailure: API错误保存状态
const fs=require('fs'),path=require('path');
const S=path.join(process.cwd(),'.ai_state');
try{
  if(fs.existsSync(S)){
    const sf=path.join(S,'status.md');
    if(fs.existsSync(sf)){
      let c=fs.readFileSync(sf,'utf8');
      c+=`\n\n## 异常中断\n${new Date().toISOString()} — API错误。下次自动恢复。\n`;
      fs.writeFileSync(sf,c);
    }
    console.log('[VibeCoding] API错误，状态已保存。');
  }
}catch(e){}
