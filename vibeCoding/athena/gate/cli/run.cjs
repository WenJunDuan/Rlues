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

// Explicit overrides can replace runners, inject code or alter collection/plugins.
const EXECUTION_ENV = /^(?:(?:npm_config|XDG|NODE|PYTEST|LD|DYLD)_.*|PYTHON.*|HOME|USERPROFILE|BASH_ENV|ENV|SHELL|PATH|COMSPEC|.*_(?:OPTIONS|OPTS|ADDOPTS)|.*_CONFIG.*|.*RC)$/i;
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
  const opts = { covers: [], env: Object.create(null), cmd: [] };
  const dash = argv.indexOf('--');
  if (dash < 0) throw new Error('run: usage: athena run [--covers AC1,AC2] [--env K=V] -- <cmd…>');
  const head = argv.slice(0, dash);
  opts.cmd = argv.slice(dash + 1);
  for (let i = 0; i < head.length; i += 1) {
    if (head[i] === '--covers') opts.covers = String(head[++i] || '').split(',').map(s => s.trim()).filter(Boolean);
    else if (head[i] === '--env') {
      const match = String(head[++i] || '').match(/^([A-Za-z_][A-Za-z0-9_]*)=([\s\S]*)$/);
      if (!match) throw new Error('run: --env takes K=V');
      const assignment = `${match[1]}=${quote(match[2])}`;
      if (evidence.credentialName(match[1]) || evidence.redact(assignment, { bounded: false }) !== assignment) {
        throw new Error(`run: --env ${match[1]} 像凭据；改走 env 文件，不写入证据`);
      }
      opts.env[match[1]] = match[2];
    } else throw new Error(`run: unknown option ${head[i]}`);
  }
  if (!opts.cmd.length) throw new Error('run: missing command after --');
  if (opts.covers.some(ac => !/^AC\d+$/.test(ac))) throw new Error('run: --covers takes AC ids like AC1,AC2');
  return opts;
}

// Only explicit runner summaries; generic "0 tests" prose is not a count.
function zeroTests(output) {
  const plain = output.replace(/\x1b\[[0-9;]*m/g, '');
  let tests = null;
  for (const line of plain.split(/\r?\n/)) {
    const node = line.match(/^\s*[ℹ#]\s+tests\s+(\d+)\s*$/);
    if (node) {
      tests = Number(node[1]);
      if (tests === 0) return true;
      continue;
    }
    const skipped = line.match(/^\s*[ℹ#]\s+skipped\s+(\d+)\s*$/);
    if (skipped && tests !== null && tests === Number(skipped[1])) return true;
    const collected = line.match(/^\s*collected (\d+) items(?:\s[^\r\n]*)?\s*$/);
    if (collected) {
      tests = null;
      if (Number(collected[1]) === 0) return true;
      continue;
    }
    if (/^\s*(?:=+\s*)?no tests ran(?: in \d+(?:\.\d+)?s(?: \((?:\d+ days?, )?\d+:\d{2}:\d{2}\))?)?(?:\s*=+)?\s*$/.test(line)) return true;
    const summary = line.trim().replace(/^=+\s*|\s*=+$/g, '');
    if (/^\d+ (?:subtests? )?(?:passed|failed|skipped|deselected|xfailed|xpassed|errors?|warnings?)(?:, \d+ (?:subtests? )?(?:passed|failed|skipped|deselected|xfailed|xpassed|errors?|warnings?))* in \d+(?:\.\d+)?s(?: \((?:\d+ days?, )?\d+:\d{2}:\d{2}\))?$/.test(summary)) {
      tests = null;
      const counts = [...summary.matchAll(/(\d+) (subtests? )?(passed|failed|skipped|deselected|xfailed|xpassed|errors?|warnings?)\b/g)]
        .filter(([, , subtest, status]) => !subtest && !status.startsWith('warning'));
      // Subtest/plugin counts do not turn a fully skipped primary suite into execution.
      if (counts.length && !counts.some(([, count, , status]) => Number(count) > 0
        && /^(?:passed|failed|xfailed|xpassed|errors?)$/.test(status))) return true;
    }
  }
  // A later nonempty summary cannot erase an earlier zero/all-skipped run.
  return false;
}

function main(argv, io) {
  const opts = parse(argv);
  const shell = opts.cmd.length === 1;
  const rawCommand = shell ? opts.cmd[0] : opts.cmd.map(quote).join(' ');
  const assignments = Object.entries(opts.env).map(([k, v]) => `${k}=${quote(v)}`).join(' ');
  // For a shell line the env must cover all segments, and replay must retain pipefail.
  const command = assignments ? `env ${assignments} ${shell ? `bash -o pipefail -c ${quote(rawCommand)}` : rawCommand}` : rawCommand;
  const ctx = context.load(io.cwd);
  const recording = Boolean(ctx && ctx.sprint);
  const ignore = recording ? reviewIgnore(ctx) : [];
  const before = recording ? treeSha(ctx.root, ignore) : null;
  const options = { cwd: io.cwd, env: { ...(io.env || process.env), ...opts.env }, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 };
  const child = shell ? spawnSync('bash', ['-o', 'pipefail', '-c', rawCommand], options) : spawnSync(opts.cmd[0], opts.cmd.slice(1), options);
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
  const ssh = shell ? null : sshVm(opts.cmd, options.env);
  const kind = evidence.classify(ssh ? ssh.remote : rawCommand) || 'other';
  const output = `${child.stdout || ''}${child.stderr || ''}`;
  let policy = shell ? evidence.policy(`set -o pipefail; ${rawCommand}`) : { provable: true, reason: null };
  if (!shell && WRAPPERS.test(path.basename(opts.cmd[0]))) policy = { provable: false, reason: 'wrapped_command' };
  if (ssh) policy = evidence.policy(ssh.remote);
  if (Object.keys(opts.env).some(name => EXECUTION_ENV.test(name))) policy = { provable: false, reason: 'validation_shadowable' };
  if (exit === 0 && kind === 'test' && zeroTests(output)) policy = { provable: false, reason: 'zero_tests: 零用例执行' };
  if (before !== after) policy = { provable: false, reason: 'tree_changed_during_run' };
  const record = evidence.append(ctx, {
    source: 'run', command, kind, exit, policy, covers: opts.covers, env: opts.env,
    tree_sha: after, ignore, output, ...(ssh || {}),
  });
  io.stderr.write(`[athena run] exit=${exit} kind=${record.kind} provable=${record.provable}${record.reason ? ` (${record.reason})` : ''} tree=${String(after).slice(0, 12)} → evidence ${record.id}\n`);
  return exit;
}

module.exports = { main, parse, sshVm, zeroTests };
