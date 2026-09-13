'use strict';
// Athena 9.9.9: owned lock, durable replace, no unlocked fallback.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const owned = new Map();
const LOCK_STALE_MS = 10000;
const lockPath = p => p + '.lock';
function legacyLockBlocks(idx) {
  const lp = lockPath(idx);
  try {
    const st = fs.statSync(lp);
    let pid = null;
    try {
      const data = JSON.parse(fs.readFileSync(lp, 'utf8'));
      if (data && Number.isInteger(data.pid)) pid = data.pid;
    } catch (_) { /* 9.9.8 locks are empty; fall through to mtime. */ }
    if (pid != null) {
      try { process.kill(pid, 0); return true; }
      catch (e) {
        if (e.code !== 'ESRCH') throw e;
        fs.unlinkSync(lp);
        return false;
      }
    }
    if (Date.now() - st.mtimeMs > LOCK_STALE_MS) {
      fs.unlinkSync(lp);
      return false;
    }
    return true;
  } catch (e) {
    if (e.code === 'ENOENT') return false;
    throw e;
  }
}
function contenders(idx) {
  const directory=path.dirname(idx), prefix=path.basename(idx)+'.lock.', result=[];
  for (const name of fs.readdirSync(directory)) {
    if (!name.startsWith(prefix) || !name.endsWith('.json')) continue;
    const tail=name.slice(prefix.length,-5).split('.');
    if (tail.length!==2 || !/^\d+$/.test(tail[0])) continue;
    const file=path.join(directory,name);
    try { process.kill(Number(tail[0]),0); }
    catch(e) { if(e.code==='ESRCH') { try {fs.unlinkSync(file);} catch(err) {if(err.code!=='ENOENT') throw err;} continue; } if(e.code!=='EPERM') throw e; }
    try { result.push([file,JSON.parse(fs.readFileSync(file,'utf8')).ticket,tail[1]]); }
    catch(e) { if(e.code==='ENOENT') continue; result.push([file,null,tail[1]]); }
  }
  return result;
}
function acquire(idx) {
  const key=path.resolve(idx); if(owned.has(key)) return true;
  const token=crypto.randomUUID().replaceAll('-',''), contender=idx+'.lock.'+process.pid+'.'+token+'.json', deadline=Date.now()+800;
  try {
    // Unique-attempt Lamport bakery tickets; dead files cannot alias a new owner.
    fs.writeFileSync(contender,'{}',{flag:'wx'});
    const numbers=contenders(idx).map(v=>v[1]).filter(Number.isInteger), ticket=Math.max(0,...numbers)+1;
    writeAtomic(contender,JSON.stringify({pid:process.pid,ticket}));
    for (;;) {
      let blocked=legacyLockBlocks(idx);
      for(const [file,number,other] of contenders(idx)) {
        if(file===contender) continue;
        if(number==null || number<ticket || (number===ticket && other<token)) blocked=true;
      }
      if(!blocked) { owned.set(key,contender); process.once('exit',()=>release(idx)); return true; }
      if(Date.now()>=deadline) { fs.unlinkSync(contender); process.stderr.write('[_index-io] lock timeout; update skipped, original preserved\n'); return false; }
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,25);
    }
  } catch(e) {
    try {fs.unlinkSync(contender);} catch(err) {if(err.code!=='ENOENT') throw err;}
    process.stderr.write('[_index-io] lock unavailable; update skipped: '+e.message+'\n'); return false;
  }
}
function release(idx) {
  const key=path.resolve(idx), contender=owned.get(key); if(!contender) return;
  owned.delete(key); try {fs.unlinkSync(contender);} catch(e) {if(e.code!=='ENOENT') throw e;}
}
function writeAtomic(file, content) {
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === content) return;
  const tmp = file + '.tmp.' + process.pid + '.' + crypto.randomUUID();
  try {
    const fd = fs.openSync(tmp, 'wx');
    try { fs.writeFileSync(fd, content, 'utf8'); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    fs.renameSync(tmp, file);
    const dir = fs.openSync(path.dirname(file), 'r');
    try { fs.fsyncSync(dir); } finally { fs.closeSync(dir); }
  } finally { try { fs.unlinkSync(tmp); } catch (e) { if (e.code !== 'ENOENT') throw e; } }
}
function update(idx, mutate) {
  if (!acquire(idx)) return null;
  try {
    const content = fs.readFileSync(idx, 'utf8'), next = mutate(content);
    if (next != null && next !== content) writeAtomic(idx, next);
    return next;
  } finally { release(idx); }
}
module.exports = {acquire, release, writeAtomic, update};
