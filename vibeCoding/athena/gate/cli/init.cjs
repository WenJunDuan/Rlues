'use strict';
// athena init: create .ai_state v2 (_index, issues, queue, sprints/, roadmap/, archive/) in the main
// checkout of a git repository, and ignore .ai_state/.runtime/. An existing _index.md is never
// overwritten: v1 state goes through `athena migrate --to 10.1`, v2 state is already initialised.
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { flags, VERSION } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');

function git(cwd, args) {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' } });
  return r.status === 0 ? r.stdout.trim() : null;
}

function main(argv, io) {
  let f;
  try { const parsed = flags(argv, { 'dry-run': 'bool' }); f = parsed.flags; if (parsed.rest.length) throw new Error(`unexpected argument ${parsed.rest[0]}`); } catch (error) { io.stderr.write(`athena init: ${error.message}\n`); return 2; }
  const top = git(io.cwd, ['rev-parse', '--show-toplevel']);
  if (!top) { io.stderr.write('athena init: not inside a git repository (run `git init` first)\n'); return 1; }
  const gitDir = git(io.cwd, ['rev-parse', '--absolute-git-dir']);
  const commonRaw = git(io.cwd, ['rev-parse', '--git-common-dir']);
  const common = commonRaw && path.resolve(io.cwd, commonRaw);
  if (!gitDir || !common) { io.stderr.write('athena init: cannot resolve the git directory\n'); return 1; }
  if (path.resolve(gitDir) !== common) {
    io.stderr.write(`athena init: this is a linked worktree; run it in the main checkout (${path.dirname(common)})\n`);
    return 1;
  }
  const A = path.join(top, '.ai_state');
  const index = path.join(A, '_index.md');
  if (fs.existsSync(index)) {
    const v2 = /^schema:\s*athena-state\/2\s*$/m.test(fs.readFileSync(index, 'utf8'));
    io.stderr.write(v2 ? 'athena init: already initialised — `athena status`\n' : 'athena init: .ai_state is v1 — `athena migrate --to 10.1 --dry-run` first\n');
    return 1;
  }
  const plan = ['_index.md', 'issues.md', 'queue.md', 'sprints/', 'roadmap/', 'archive/', '.gitignore: .ai_state/.runtime/'];
  if (f['dry-run']) { io.stdout.write(`would create in ${A}:\n${plan.map(p => `  ${p}`).join('\n')}\n`); return 0; }
  for (const dir of ['sprints', 'roadmap', 'archive']) {
    fs.mkdirSync(path.join(A, dir), { recursive: true });
    const keep = path.join(A, dir, '.gitkeep');
    if (!fs.readdirSync(path.join(A, dir)).length) fs.writeFileSync(keep, '');
  }
  for (const name of ['issues.md', 'queue.md']) {
    if (!fs.existsSync(path.join(A, name))) fs.copyFileSync(path.join(state.templatesDir(), name), path.join(A, name));
  }
  fs.writeFileSync(index, state.render('_index.md', { version: VERSION() })); // last: its presence means "initialised"
  const ignore = path.join(top, '.gitignore');
  let gi = fs.existsSync(ignore) ? fs.readFileSync(ignore, 'utf8') : '';
  if (!gi.split(/\r?\n/).includes('.ai_state/.runtime/')) fs.writeFileSync(ignore, `${gi}${gi && !gi.endsWith('\n') ? '\n' : ''}.ai_state/.runtime/\n`);
  io.stdout.write(`initialised ${A} (schema athena-state/2). Next: \`athena sprint start\` or \`athena status\`.\n`);
  return 0;
}

module.exports = { main };
