'use strict';
// athena run -- <cmd…>: run a check and record its real exit code as evidence (design §8, D5).
// One argument = a shell line (bash -o pipefail -c); several = argv, executed without a shell.
// kind comes from the command words only (no override); a wrapped or shell argv[0], or a
// source tree that changed while the command ran, is recorded as unprovable.
// argv `ssh [opts] user@host <remote…>` to a VM in ~/.athena/vm.json (host+user+port match)
// is judged by the remote command under the local rules (G-002); any other ssh stays unprovable.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const context = require('../lib/context.cjs');
const evidence = require('../lib/evidence.cjs');
const { treeSha } = require('../lib/tree-sha.cjs');
const { reviewIgnore } = require('../core.cjs');

const WRAPPERS = /^(?:(?:ba|z|da|k)?sh|eval|env|sudo|xargs|timeout|nice|nohup|time|exec|stdbuf|command|fish|pwsh|powershell|cmd)$/;
const quote = (w) => (/^[A-Za-z0-9_@%+=:,./-]+$/.test(w) ? w : `'${w.replace(/'/g, "'\\''")}'`);

// ssh flags that keep "run <remote> on <destination>": no-arg / with-arg. Others (-f -N -s -W -G -O -F …) → no match.
const SSH_FLAGS = new Set('46AaCKkMnqTtvXxYy');
const SSH_ARGS = new Set('bcDEeiJLlmopRw');
const SSH_DENY = /^(?:hostname|proxycommand|remotecommand|localcommand|permitlocalcommand|sessiontype|forkafterauthentication)$/i;

/** { vm, remote } when argv is ssh to a registered VM with a remote command, else null. */
function sshVm(argv, env) {
  if (path.basename(argv[0]) !== 'ssh') return null;
  let user = null;
  let port = null;
  let i = 1;
  for (; i < argv.length && argv[i].startsWith('-') && argv[i] !== '-'; i += 1) {
    if (argv[i] === '--') { i += 1; break; }
    const flags = argv[i].slice(1);
    for (let j = 0; j < flags.length; j += 1) {
      const f = flags[j];
      if (SSH_FLAGS.has(f)) continue;
      if (!SSH_ARGS.has(f)) return null;
      const value = j + 1 < flags.length ? flags.slice(j + 1) : argv[++i];
      if (value === undefined) return null;
      if (f === 'l') user = value;
      if (f === 'p') port = value;
      if (f === 'o') {
        const [key, ...rest] = value.split(/[=\s]+/);
        if (SSH_DENY.test(key)) return null;
        if (/^user$/i.test(key)) user = rest.join(' ');
        if (/^port$/i.test(key)) port = rest.join(' ');
      }
      break;
    }
  }
  const dest = argv[i];
  const remote = argv.slice(i + 1).join(' ');
  if (!dest || !remote.trim()) return null;
  const at = dest.lastIndexOf('@');
  const host = at >= 0 ? dest.slice(at + 1) : dest;
  if (at >= 0) user = dest.slice(0, at);
  if (!user) return null;
  let vms = [];
  try { vms = JSON.parse(fs.readFileSync(path.join(env.HOME || os.homedir(), '.athena', 'vm.json'), 'utf8')).vms || []; } catch (_) { return null; }
  const vm = vms.find(v => v && typeof v.host === 'string' && v.host.toLowerCase() === host.toLowerCase()
    && v.user === user && String(v.port || 22) === String(port || 22));
  return vm ? { vm: String(vm.name || vm.host), remote } : null;
}

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
  const ssh = shell ? null : sshVm(opts.cmd, io.env || process.env);
  let policy = shell ? evidence.policy(`set -o pipefail; ${command}`) : { provable: true, reason: null };
  if (!shell && WRAPPERS.test(path.basename(opts.cmd[0]))) policy = { provable: false, reason: 'wrapped_command' };
  if (ssh) policy = evidence.policy(ssh.remote);
  if (before !== after) policy = { provable: false, reason: 'tree_changed_during_run' };
  const record = evidence.append(ctx, {
    source: 'run', command, kind: evidence.classify(ssh ? ssh.remote : command) || 'other', exit, policy, covers: opts.covers,
    tree_sha: after, ignore, output: `${child.stdout || ''}${child.stderr || ''}`, ...(ssh || {}),
  });
  io.stderr.write(`[athena run] exit=${exit} kind=${record.kind} provable=${record.provable}${record.reason ? ` (${record.reason})` : ''} tree=${String(after).slice(0, 12)} → evidence ${record.id}\n`);
  return exit;
}

module.exports = { main, parse, sshVm };
