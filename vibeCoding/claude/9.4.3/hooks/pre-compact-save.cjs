#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const sd=path.join(process.env.CLAUDE_PROJECT_DIR||process.cwd(),'.ai_state');
if(!fs.existsSync(sd)){process.exit(0);}
const snap={timestamp:new Date().toISOString(),project:null,tasksSummary:null};
try{snap.project=JSON.parse(fs.readFileSync(path.join(sd,'project.json'),'utf8'));}catch(e){}
try{const t=fs.readFileSync(path.join(sd,'tasks.md'),'utf8');
  snap.tasksSummary={pending:(t.match(/^- \[ \]/gm)||[]).length,done:(t.match(/^- \[x\]/gm)||[]).length};
}catch(e){}
try{fs.writeFileSync(path.join(sd,'compact-snapshot.json'),JSON.stringify(snap,null,2));
  process.stderr.write('[compact-save] snapshot saved: '+(snap.project?snap.project.path+'/'+snap.project.stage:'no project')+'\n');
}catch(e){process.stderr.write('[compact-save] failed: '+e.message+'\n');}
process.exit(0);
