// v9.1.8 Stop: 质量门控+TDD
const fs=require('fs'),path=require('path'),{execSync}=require('child_process');
const S=path.join(process.cwd(),'.ai_state'),issues=[];
try{
  const pf=path.join(S,'plan.md');
  if(fs.existsSync(pf)){
    const n=(fs.readFileSync(pf,'utf8').match(/- \[ \]/g)||[]).length;
    if(n>0) issues.push(`plan.md 有 ${n} 个未完成任务`);
  }
  try{
    const d=execSync('git diff --cached --name-only 2>/dev/null||git diff --name-only 2>/dev/null',{encoding:'utf8'});
    // 源码: 代码文件排除测试/配置/文档/资源
    const codeExt=/\.(ts|tsx|js|jsx|py|rs|go|java|rb|php|swift|kt|cs|c|cpp|h)$/;
    const nonSrc=/\.test\.|\.spec\.|__test__|__spec__|\.config\.|\.d\.ts$|\/test\/|\/tests\/|\/docs\/|\/doc\/|README|CHANGELOG|LICENSE/;
    const src=d.split('\n').filter(f=>codeExt.test(f)&&!nonSrc.test(f));
    const tst=d.split('\n').filter(f=>f.match(/\.test\.|\.spec\.|__test__|__spec__|\/test\/|\/tests\//));
    if(src.length>0&&tst.length===0) issues.push(`${src.length} 个源码无测试`);
  }catch(e){}
  if(fs.existsSync(pf)&&!fs.existsSync(path.join(S,'quality.md'))) issues.push('缺 quality.md');
  try{
    const sec=execSync('git diff --cached -U0 2>/dev/null|grep -iE "(password|secret|api_key|token)\\s*[:=]\\s*[\\"\\x27][^\\"\\x27]{8,}"||true',{encoding:'utf8'});
    if(sec.trim()) issues.push('疑似硬编码密钥');
  }catch(e){}
}catch(e){process.exit(0);}
if(issues.length>0){process.stderr.write(`[delivery-gate] 阻断:\n${issues.map(i=>`  ✗ ${i}`).join('\n')}\n`);process.exit(2);}
process.exit(0);
