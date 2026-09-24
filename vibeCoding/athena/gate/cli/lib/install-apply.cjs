'use strict';
// Transactional apply / rollback for `athena install` (design §11.1–11.2). Every file the install
// replaces, retires or creates — and every directory it creates — is recorded in
// ~/.athena/backups/<ts>/backup.json before it changes. A failure mid-way restores from that record;
// `athena rollback` uses the same record (found through installed.json, or the newest unrolled
// backup when an install died before writing installed.json). Symlinked targets are written through,
// so a dotfiles link survives install and rollback. Nothing is deleted without a copy in the backup.
const fs = require('fs');
const path = require('path');
const { sha } = require('./install-plan.cjs');

const STATE = '.athena/installed.json';

function readJson(file) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (_) { return null; } }
function linkTarget(file) { try { return fs.readlinkSync(file); } catch (_) { return null; } }
function lexists(file) { try { fs.lstatSync(file); return true; } catch (_) { return false; } }

/** The path a write should go to: through a symlink to its (existing) target. */
function writeTargetOf(abs) {
  try { if (fs.lstatSync(abs).isSymbolicLink()) return fs.realpathSync(abs); } catch (_) { /* absent or dangling */ }
  return abs;
}

function shim() {
  return '#!/bin/sh\n# athena CLI shim (athena install) — runs the current core with the node on PATH\nexec node "$HOME/.athena/current/cli.cjs" "$@"\n';
}

function stampNow() { return new Date().toISOString().replace(/[-:.]/g, ''); }

function apply(home, p, platforms) {
  const ts = stampNow();
  const backup = path.join(home, '.athena', 'backups', ts);
  const record = { ts, version: p.version, release: p.release, platforms, previous_current: linkTarget(path.join(home, '.athena/current')), entries: [], dirs: [] };
  const save = () => { fs.mkdirSync(backup, { recursive: true }); fs.writeFileSync(path.join(backup, 'backup.json'), `${JSON.stringify(record, null, 2)}\n`); };
  const ensureDir = (dir) => {
    const missing = [];
    for (let d = dir; d !== home && !lexists(d); d = path.dirname(d)) missing.unshift(d);
    for (const d of missing) { fs.mkdirSync(d); record.dirs.push(path.relative(home, d)); }
    if (missing.length) save();
  };
  const stash = (rel, how) => {
    const abs = path.join(home, rel);
    const real = writeTargetOf(abs);
    const existed = lexists(real);
    if (existed) {
      const copy = path.join(backup, 'files', rel);
      fs.mkdirSync(path.dirname(copy), { recursive: true });
      if (how === 'move') fs.renameSync(abs, copy); else fs.cpSync(real, copy, { recursive: true });
    }
    record.entries.push({ path: rel, real: real === abs ? undefined : real, existed, retired: how === 'move' });
    save();
    return real;
  };
  const write = (rel, content, mode) => {
    const real = stash(rel, 'copy');
    ensureDir(path.dirname(real));
    const tmp = `${real}.athena-tmp-${process.pid}`;
    record.entries[record.entries.length - 1].tmp = tmp; // a crash before the rename leaves nothing behind
    save();
    fs.writeFileSync(tmp, content, { mode });
    fs.chmodSync(tmp, mode);
    fs.renameSync(tmp, real);
    record.entries[record.entries.length - 1].sha256 = sha(content);
  };
  save();
  try {
    const versionDir = path.join(home, '.athena', p.release);
    if (lexists(versionDir)) {
      fs.mkdirSync(path.join(backup, 'core'), { recursive: true });
      fs.renameSync(versionDir, path.join(backup, 'core', p.release));
      record.core_replaced = true;
      save();
    }
    for (const a of p.actions) {
      if (a.action === 'retire') { stash(a.dest, 'move'); continue; }
      if (a.kind === 'core') {
        const abs = path.join(home, a.dest);
        ensureDir(path.dirname(abs));
        fs.writeFileSync(abs, a.content, { mode: a.mode });
        fs.chmodSync(abs, a.mode);
      } else write(a.dest, a.content, a.mode);
    }
    write('.athena/bin/athena', shim(), 0o755);
    const current = path.join(home, '.athena/current');
    try { fs.unlinkSync(current); } catch (_) { /* first install */ }
    fs.symlinkSync(p.release, current);
    const files = p.actions.filter(a => a.action !== 'retire').map(a => ({ path: a.dest, sha256: sha(a.content), kind: a.kind, merged: a.action === 'merge' }));
    write(STATE, `${JSON.stringify({ version: p.version, release: p.release, platforms, installed_at: new Date().toISOString(),
      backup: path.relative(home, backup), files, hooks: p.hooks || {} }, null, 2)}\n`, 0o644);
    return record;
  } catch (error) {
    const problems = restore(home, backup, record);
    if (problems.length) error.message += `; automatic restore incomplete (${problems.join('; ')}) — run \`athena rollback\``;
    throw error;
  }
}

/**
 * Undo one backup record. Files the user changed after the install, and anything left in the
 * release directory, are kept under <backup>/after-install/ before being replaced. Returns problems.
 */
function restore(home, backup, record) {
  const problems = [];
  const keep = (abs, rel) => {
    try {
      if (!lexists(abs)) return;
      const copy = path.join(backup, 'after-install', rel);
      fs.mkdirSync(path.dirname(copy), { recursive: true });
      fs.cpSync(abs, copy, { recursive: true });
    } catch (error) { problems.push(`keep ${rel}: ${error.code || error.message}`); }
  };
  for (const e of [...record.entries].reverse()) {
    const abs = e.real || path.join(home, e.path);
    try {
      if (e.tmp) fs.rmSync(e.tmp, { force: true });
      if (!e.retired && e.sha256 && lexists(abs) && !fs.lstatSync(abs).isDirectory() && sha(fs.readFileSync(abs)) !== e.sha256) keep(abs, e.path);
      if (e.existed) {
        const copy = path.join(backup, 'files', e.path);
        if (e.retired) {
          if (lexists(abs)) { keep(abs, e.path); fs.rmSync(abs, { recursive: true, force: true }); }
          fs.mkdirSync(path.dirname(abs), { recursive: true });
          fs.cpSync(copy, abs, { recursive: true });
        } else {
          fs.mkdirSync(path.dirname(abs), { recursive: true });
          fs.copyFileSync(copy, abs);
        }
      } else if (lexists(abs) && !fs.lstatSync(abs).isDirectory()) fs.rmSync(abs, { force: true });
    } catch (error) { problems.push(`${e.path}: ${error.code || error.message}`); }
  }
  const versionDir = path.join(home, '.athena', record.release);
  try {
    if (lexists(versionDir)) { keep(versionDir, `.athena/${record.release}`); fs.rmSync(versionDir, { recursive: true, force: true }); }
    if (record.core_replaced) fs.renameSync(path.join(backup, 'core', record.release), versionDir);
  } catch (error) { problems.push(`core: ${error.code || error.message}`); }
  try {
    const current = path.join(home, '.athena/current');
    if (lexists(current)) fs.unlinkSync(current);
    if (record.previous_current) fs.symlinkSync(record.previous_current, current);
  } catch (error) { problems.push(`current: ${error.code || error.message}`); }
  for (const d of [...(record.dirs || [])].reverse()) { try { fs.rmdirSync(path.join(home, d)); } catch (_) { /* not empty: user content */ } }
  // only a clean restore closes the record; otherwise `athena rollback` retries it (restore is idempotent)
  if (problems.length) record.restore_problems = problems;
  else { record.rolled_back = new Date().toISOString(); delete record.restore_problems; }
  try { fs.writeFileSync(path.join(backup, 'backup.json'), `${JSON.stringify(record, null, 2)}\n`); } catch (_) { /* best effort */ }
  return problems;
}

/** The backup to roll back: the newest record not yet rolled back (an interrupted install included). */
function pending(home) {
  const dir = path.join(home, '.athena', 'backups');
  let names = [];
  try { names = fs.readdirSync(dir).sort().reverse(); } catch (_) { return null; }
  const hit = names.find(n => { const r = readJson(path.join(dir, n, 'backup.json')); return r && !r.rolled_back; });
  return hit ? path.join(dir, hit) : null;
}

function rollback(home) {
  const backup = pending(home);
  if (!backup) throw new Error('nothing to roll back (no ~/.athena/installed.json and no pending backup)');
  const record = readJson(path.join(backup, 'backup.json'));
  if (!record) throw new Error(`backup record missing: ${backup}`);
  if (record.rolled_back) throw new Error(`already rolled back at ${record.rolled_back}`);
  const problems = restore(home, backup, record);
  return { record, problems, backup };
}

module.exports = { apply, rollback, restore, STATE, readJson };
