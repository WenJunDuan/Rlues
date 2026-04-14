#!/usr/bin/env node
'use strict';
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',d=>input+=d);
process.stdin.on('end',()=>{
  let data={};try{data=JSON.parse(input);}catch(e){process.exit(0);return;}
  const reason=data.denial_reason||'';
  const retry=!/security|forbidden|denied|block/i.test(reason);
  process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PermissionDenied',retry}}));
  process.exit(0);
});
