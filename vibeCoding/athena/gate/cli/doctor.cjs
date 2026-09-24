'use strict';
// athena doctor [--home <dir>]: installed files vs their recorded sha (drift / missing), the current
// link, node on PATH, leftover 9.9.9 files, and (inside a project) expired or invalid exemptions.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { flags } = require('./lib/common.cjs');
const { STATE, readJson } = require('./lib/install-apply.cjs');
const { sha } = require('./lib/install-plan.cjs');
const LEGACY = require('./lib/legacy-999.cjs');
const context = require('../lib/context.cjs');
const exemptions = require('../lib/exemptions.cjs');

function main(argv, io) {
  let f;
  try { f = flags(argv, { home: 'str' }).flags; } catch (error) { io.stderr.write(`athena doctor: ${error.message}\n`); return 2; }
  const home = path.resolve(f.home || os.homedir());
  const problems = [];
  const notes = [];
  const state = readJson(path.join(home, STATE));
  if (!state) problems.push('not installed (no ~/.athena/installed.json)');
  else {
    notes.push(`athena ${state.version} for ${state.platforms.join(',')} (installed ${state.installed_at})`);
    for (const file of state.files) {
      const abs = path.join(home, file.path);
      if (!fs.existsSync(abs)) { problems.push(`missing ${file.path}`); continue; }
      if (file.path.endsWith('config.toml')) {
        const heads = fs.readFileSync(abs, 'utf8').split(/\r?\n/).map(l => l.trim()).filter(l => /^\[[^\]]+\]\s*(#.*)?$/.test(l)).map(l => l.replace(/\s*#.*$/, '').replace(/\s+/g, ''));
        const dup = heads.find((h, i) => heads.indexOf(h) !== i);
        if (dup) problems.push(`${file.path}: table ${dup} declared twice — Codex will not load it`);
      }
      if (sha(fs.readFileSync(abs)) !== file.sha256) (file.merged ? notes : problems).push(`${file.merged ? 'changed since install (config file, user edits allowed)' : 'drift'} ${file.path}`);
    }
    for (const [file, commands] of Object.entries(state.hooks || {})) {
      let data = null;
      try { data = JSON.parse(fs.readFileSync(path.join(home, file), 'utf8')); } catch (error) { problems.push(`${file} unreadable or not JSON — hooks disabled`); continue; }
      const present = new Set(Object.values(data.hooks || {}).flat().flatMap(g => (g && g.hooks) || []).map(h => h.command));
      const lost = commands.filter(c => !present.has(c));
      if (lost.length) problems.push(`${file}: ${lost.length} Athena hook(s) missing (e.g. ${lost[0]}) — gates are off`);
    }
    const current = (() => { try { return fs.readlinkSync(path.join(home, '.athena/current')); } catch (_) { return null; } })();
    if (current !== state.release) problems.push(`~/.athena/current → ${current || '(missing)'}, expected ${state.release}`);
    const installed = new Set(state.files.map(x => x.path));
    const leftovers = LEGACY.filter(rel => !installed.has(rel) && fs.existsSync(path.join(home, rel))
      && ((rel.startsWith('.claude/') && state.platforms.includes('cc')) || (!rel.startsWith('.claude/') && state.platforms.includes('cx'))));
    if (leftovers.length) problems.push(`9.9.9 leftovers: ${leftovers.slice(0, 5).join(', ')}${leftovers.length > 5 ? ', …' : ''}`);
  }
  const node = spawnSync('sh', ['-c', 'command -v node && node --version'], { encoding: 'utf8' });
  if (node.status !== 0) problems.push('node not on PATH (hooks run `node ~/.athena/current/hook.cjs`)');
  else {
    const version = node.stdout.trim().split('\n').pop();
    if (Number(version.replace(/^v/, '').split('.')[0]) < 22) problems.push(`node ${version} < 22`);
    else notes.push(`node ${version} at ${node.stdout.split('\n')[0]}`);
  }
  const ctx = context.load(io.cwd);
  if (ctx) for (const x of exemptions.review(ctx).filter(e => e.status !== 'active')) problems.push(`exemption ${x.entry && x.entry.key}: ${x.why}`);
  for (const n of notes) io.stdout.write(`ok   ${n}\n`);
  for (const p of problems) io.stdout.write(`FAIL ${p}\n`);
  io.stdout.write(problems.length ? `${problems.length} problem(s)\n` : 'doctor: no drift\n');
  return problems.length ? 1 : 0;
}

module.exports = { main };
