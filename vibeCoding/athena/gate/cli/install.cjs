'use strict';
// athena install --platform cc,cx[,pi] [--dry-run] [--home <dir>] [--dist <dist root>]
// Core → ~/.athena/<release>/ + ~/.athena/current; adapter files per platform; config files merged
// (user keys kept); 9.9.9 files 10.1 no longer ships are moved into the backup. See also rollback, doctor.
const os = require('os');
const path = require('path');
const { flags, UsageError } = require('./lib/common.cjs');
const { plan, distRoot, InstallError } = require('./lib/install-plan.cjs');
const { apply } = require('./lib/install-apply.cjs');

const PLATFORMS = new Set(['cc', 'cx', 'pi']);

function main(argv, io) {
  let f;
  try { f = flags(argv, { platform: 'str', 'dry-run': 'bool', home: 'str', dist: 'str' }).flags; }
  catch (error) { io.stderr.write(`athena install: ${error.message}\n`); return 2; }
  const platforms = String(f.platform || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!platforms.length || platforms.some(p => !PLATFORMS.has(p))) {
    io.stderr.write('usage: athena install --platform cc,cx[,pi] [--dry-run] [--home <dir>] [--dist <dist root>]\n');
    return 2;
  }
  const major = Number(process.versions.node.split('.')[0]);
  if (major < 22) { io.stderr.write(`athena install: node ≥22 required (found ${process.versions.node})\n`); return 1; }
  const home = path.resolve(f.home || os.homedir());
  let p;
  try { p = plan(home, platforms, distRoot(f.dist)); }
  catch (error) {
    if (error instanceof InstallError || error instanceof UsageError) { io.stderr.write(`athena install: ${error.message}\n`); return 1; }
    throw error;
  }
  const count = (k) => p.actions.filter(a => a.action === k).length;
  const summary = `athena ${p.version} → ${home}: write ${count('write')}, merge ${count('merge')} (${p.actions.filter(a => a.action === 'merge').map(a => a.dest).join(', ') || '—'}), retire ${count('retire')}`;
  if (f['dry-run']) {
    io.stdout.write(`${summary}\n`);
    for (const a of p.actions.filter(x => x.action !== 'write')) io.stdout.write(`  ${a.action} ${a.dest}\n`);
    io.stdout.write('(dry-run: nothing changed)\n');
    return 0;
  }
  for (const n of p.notes) io.stderr.write(`note: ${n}\n`);
  let record;
  try { record = apply(home, p, platforms); }
  catch (error) { io.stderr.write(`athena install: failed: ${error.message}\n`); return 1; }
  io.stdout.write(`${summary}\nbackup: ${path.join(home, '.athena/backups', record.ts)}\n` +
    `CLI: add ${path.join(home, '.athena/bin')} to PATH for \`athena\`; \`athena doctor\` checks the install; \`athena rollback\` undoes it.\n` +
    (platforms.includes('pi') ? `Pi: install the package with \`pi install ${path.join(home, '.athena/current/pi/plugin')}\` (待验证 on Pi 0.87).\n` : ''));
  return 0;
}

module.exports = { main };
