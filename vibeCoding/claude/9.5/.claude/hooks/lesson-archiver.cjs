#!/usr/bin/env node
'use strict';
// lesson-archiver - 把 ~/.claude/lessons/draft-*.md 中超过 7 天的移到 archive/
// 不是独立 hook, 由 session-start.cjs 在每次 startup 时调用一次 (轻量)
// 也可以手动跑: node ~/.claude/hooks/lesson-archiver.cjs

const fs=require('fs'),path=require('path');
const home=process.env.HOME||require('os').homedir();
const lessonsDir=path.join(home,'.claude','lessons');
const archiveDir=path.join(lessonsDir,'archive');
const SEVEN_DAYS=7*24*60*60*1000;

if(!fs.existsSync(lessonsDir)){
  if(require.main===module)process.stderr.write('[lesson-archiver] ~/.claude/lessons/ 不存在, 跳过\n');
  process.exit(0);
}
fs.mkdirSync(archiveDir,{recursive:true});

const now=Date.now();
let archived=0;

try{
  const files=fs.readdirSync(lessonsDir);
  for(const f of files){
    if(!f.startsWith('draft-')||!f.endsWith('.md'))continue;
    const fpath=path.join(lessonsDir,f);
    let st;
    try{st=fs.statSync(fpath);}catch(e){continue;}
    if(!st.isFile())continue;
    const ageMs=now-st.mtimeMs;
    if(ageMs>SEVEN_DAYS){
      const dest=path.join(archiveDir,f);
      try{
        fs.renameSync(fpath,dest);
        archived++;
      }catch(e){
        process.stderr.write('[lesson-archiver] archive 失败 '+f+': '+e.message+'\n');
      }
    }
  }
}catch(e){
  process.stderr.write('[lesson-archiver] 读目录失败: '+e.message+'\n');
}

if(archived>0){
  process.stderr.write('[lesson-archiver] 归档 '+archived+' 个超期 draft\n');
}

if(require.main===module)process.exit(0);
module.exports={archived};
