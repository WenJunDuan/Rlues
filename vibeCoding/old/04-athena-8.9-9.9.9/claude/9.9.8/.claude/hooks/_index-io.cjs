'use strict';
/**
 * VibeCoding Athena v9.9.6 · _index.md 并发安全读写 (CC)
 *
 * 背景: 同一 hook 事件上挂多个 hook 时, 平台不保证串行执行。
 * index-updater / design-change-detector / pace-continuator 都对 _index.md
 * 做 read-modify-write, 并发下后写覆盖先写 = lost update, 丢的是
 * design_changed_after_impl 这类门禁标记 —— 丢了不报错, 只静默放行。
 *
 * 方案: O_EXCL 锁文件 (含 stale 自动打破) + tmp/rename 原子替换。
 * 拿不到锁时退化为直接写并告警, 不阻塞 hook (门禁另有 ship 侧兜底)。
 */
const fs = require('fs');

const LOCK_STALE_MS = 10000;
const MAX_WAIT_MS = 800;
const SLEEP_MS = 25;

function lockPath(idxPath) { return `${idxPath}.lock`; }

function sleepSync(ms) {
  try { Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms); }
  catch (_) { const end = Date.now() + ms; while (Date.now() < end); }
}

function acquire(idxPath) {
  const lp = lockPath(idxPath);
  const deadline = Date.now() + MAX_WAIT_MS;
  for (;;) {
    try {
      fs.closeSync(fs.openSync(lp, 'wx'));
      process.on('exit', () => { try { fs.unlinkSync(lp); } catch (_) {} });
      return true;
    } catch (e) {
      if (e.code !== 'EEXIST') return false;
      try {
        if (Date.now() - fs.statSync(lp).mtimeMs > LOCK_STALE_MS) { fs.unlinkSync(lp); continue; }
      } catch (_) { continue; }
      if (Date.now() > deadline) {
        process.stderr.write('[_index-io] 锁等待超时, 退化为直接写 (可能丢更新)\n');
        return false;
      }
      sleepSync(SLEEP_MS);
    }
  }
}

function release(idxPath) { try { fs.unlinkSync(lockPath(idxPath)); } catch (_) {} }

function writeAtomic(idxPath, content) {
  const tmp = `${idxPath}.tmp.${process.pid}`;
  fs.writeFileSync(tmp, content, 'utf-8');
  fs.renameSync(tmp, idxPath);
}

/** 读-改-写全程持锁。mutate(content) 返回新内容, 返回 null/相同则不写。 */
function update(idxPath, mutate) {
  const locked = acquire(idxPath);
  try {
    const content = fs.readFileSync(idxPath, 'utf-8');
    const next = mutate(content);
    if (next != null && next !== content) writeAtomic(idxPath, next);
    return next;
  } finally { if (locked) release(idxPath); }
}

module.exports = { acquire, release, writeAtomic, update };
