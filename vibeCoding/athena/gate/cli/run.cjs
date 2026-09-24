'use strict';
// athena run -- <cmd…>: run a check and record its real exit code as evidence (design §8, D5).
// One argument = a shell line (bash -o pipefail -c); several = argv, executed without a shell.
// kind comes from the command words only (no override); a wrapped or shell argv[0], or a
// source tree that changed while the command ran, is recorded as unprovable.
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const context = require('../lib/context.cjs');
const evidence = require('../lib/evidence.cjs');
const { treeSha } = require('../lib/tree-sha.cjs');
const { reviewIgnore } = require('../core.cjs');

const WRAPPERS = /^(?:(?:ba|z|da|k)?sh|eval|env|sudo|xargs|timeout|nice|nohup|time|exec|stdbuf|command|fish|pwsh|powershell|cmd)$/;
const quote = (w) => (/^[A-Za-z0-9_@%+=:,./-]+$/.test(w) ? w : `'${w.replace(/'/g, "'\\''")}'`);

function parse(argv) {
  const opts = { covers: [], cmd: [] };
  const dash = argv.indexOf('--');
  if (dash < 0) throw new Error('run: usage: athena run [--covers AC1,AC2] -- <cmd…>');
  const head = argv.slice(0, dash);
  opts.cmd = argv.slice(dash + 1);
  for (let i = 0; i < head.length; i += 1) {
    if (head[i] === '--covers') opts.covers = String(head[++i] || '').split(',').map(s => s.trim()).filter(Boolean);
    else throw new Error(`run: unknown option ${head[i]}`);
  }
  if (!opts.cmd.length) throw new Error('run: missing command after --');
  if (opts.covers.some(ac => !/^AC\d+$/.test(ac))) throw new Error('run: --covers takes AC ids like AC1,AC2');
  return opts;
}

function main(argv, io) {
  const opts = parse(argv);
  const shell = opts.cmd.length === 1;
  const command = shell ? opts.cmd[0] : opts.cmd.map(quote).join(' ');
  const ctx = context.load(io.cwd);
  const recording = Boolean(ctx && ctx.sprint);
  const ignore = recording ? reviewIgnore(ctx) : [];
  const before = recording ? treeSha(ctx.root, ignore) : null;
  const options = { cwd: io.cwd, env: io.env, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 };
  const child = shell ? spawnSync('bash', ['-o', 'pipefail', '-c', command], options) : spawnSync(opts.cmd[0], opts.cmd.slice(1), options);
  if (child.stdout) io.stdout.write(child.stdout);
  if (child.stderr) io.stderr.write(child.stderr);
  if (child.error) io.stderr.write(`[athena run] ${child.error.message}\n`);
  const signal = child.signal ? (os.constants.signals[child.signal] || 0) : 0;
  const exit = Number.isInteger(child.status) ? child.status : (child.signal ? 128 + signal : 127);
  if (!recording) {
    io.stderr.write('[athena run] no active sprint: evidence not recorded\n');
    return exit;
  }
  const after = treeSha(ctx.root, ignore);
  let policy = shell ? evidence.policy(`set -o pipefail; ${command}`) : { provable: true, reason: null };
  if (!shell && WRAPPERS.test(path.basename(opts.cmd[0]))) policy = { provable: false, reason: 'wrapped_command' };
  if (before !== after) policy = { provable: false, reason: 'tree_changed_during_run' };
  const record = evidence.append(ctx, {
    source: 'run', command, kind: evidence.classify(command) || 'other', exit, policy, covers: opts.covers,
    tree_sha: after, ignore, output: `${child.stdout || ''}${child.stderr || ''}`,
  });
  io.stderr.write(`[athena run] exit=${exit} kind=${record.kind} provable=${record.provable}${record.reason ? ` (${record.reason})` : ''} tree=${String(after).slice(0, 12)} → evidence ${record.id}\n`);
  return exit;
}

module.exports = { main, parse };
