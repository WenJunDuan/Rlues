'use strict';
// athena run [--covers AC1,AC2] [--env K=V] -- <cmd…>: run a check, record its real exit code as evidence (design §8, D5).
// athena run --rebind: after an edit, re-RUN the sprint's latest provable PASS test/typecheck
// commands (same argv, env, cwd, covers) on the current tree; never copies an old PASS.
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
const words = require('../lib/shell-words.cjs');
const evidence = require('../lib/evidence.cjs');
const { treeSha, treeFiles } = require('../lib/tree-sha.cjs');
const { reviewIgnore } = require('../core.cjs');

// Explicit overrides can replace runners, inject code or alter collection/plugins.
const { EXECUTION_ENV } = evidence;
const WRAPPERS = /^(?:(?:ba|z|da|k)?sh|eval|env|sudo|xargs|timeout|nice|nohup|time|exec|stdbuf|command|fish|pwsh|powershell|cmd)$/;
const REBIND_KINDS = new Set(['test', 'typecheck']);
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

const USAGE = 'run: usage: athena run [--covers AC1,AC2] [--env K=V] -- <cmd…> | athena run --rebind';

function parse(argv) {
  const opts = { covers: [], env: Object.create(null), cmd: [], rebind: false };
  const dash = argv.indexOf('--');
  const head = dash < 0 ? argv : argv.slice(0, dash);
  if (head.includes('--rebind')) {
    if (dash >= 0 || head.length !== 1) throw new Error('run: --rebind re-runs the recorded commands; it takes no --covers, --env or -- <cmd…>. sample: athena run --rebind');
    return { ...opts, rebind: true };
  }
  if (dash < 0) throw new Error(USAGE);
  opts.cmd = argv.slice(dash + 1);
  let rawCovers = '';
  for (let i = 0; i < head.length; i += 1) {
    if (head[i] === '--covers') {
      rawCovers = String(head[++i] || '');
      opts.covers = rawCovers.split(',').map(s => s.trim()).filter(Boolean);
    } else if (head[i] === '--env') {
      const match = String(head[++i] || '').match(/^([A-Za-z_][A-Za-z0-9_]*)=([\s\S]*)$/);
      if (!match) throw new Error('run: --env takes K=V. sample: athena run --env FOO=1 -- <cmd…>');
      const assignment = `${match[1]}=${quote(match[2])}`;
      if (evidence.credentialName(match[1]) || evidence.redact(assignment, { bounded: false }) !== assignment) {
        throw new Error(`run: --env ${match[1]} 像凭据；改走 env 文件，不写入证据`);
      }
      opts.env[match[1]] = match[2];
    } else throw new Error(`run: unknown option ${head[i]}`);
  }
  if (!opts.cmd.length) throw new Error('run: missing command after --');
  if (opts.covers.some(ac => !/^AC\d+$/.test(ac))) {
    // The corrected sample reuses the numbers the caller gave ("ac1 AC-2" → AC1,AC2).
    const ids = (rawCovers.match(/\d+/g) || ['1', '2']).map(n => `AC${Number(n)}`).join(',');
    throw new Error(`run: --covers takes AC ids like AC1,AC2 (got "${rawCovers}"). sample: athena run --covers ${ids} -- <cmd…>`);
  }
  return opts;
}

// Provable forms, one per unprovable reason. Each mirrors a rule enforced in execute() or in
// lib/evidence.cjs policy(): the fix travels with the refusal instead of living in a prompt.
const FORMS = {
  wrapped_command: 'argv[0] is a shell or wrapper (bash, sh, env, sudo, timeout, …): pass the tool itself `athena run -- npm test`, or one quoted shell line `athena run -- \'npm run build && npm test\'`; variables go in `--env K=V`',
  validation_backgrounded: 'drop the trailing `&`: `athena run -- npm test`',
  validation_may_not_run: 'nothing before the check may skip it (`||`, exit, return, exec): chain with `&&` only, e.g. `athena run -- \'npm run build && npm test\'`',
  validation_status_not_reported: 'the check must decide the exit code: put it last, or follow it with `&&` only (no `;`, `||` or newline after it), e.g. `athena run -- \'npm run build && npm test\'`',
  pipeline_without_pipefail: 'the pipe hides the check\'s exit code: drop it (`athena run -- npm test`; output is recorded anyway) or keep pipefail on, over ssh `ssh user@host \'set -o pipefail; npm test | tail -20\'`',
  validation_shadowable: 'the runner could be replaced: no trap/alias/function/source (in-repo `bin/activate` excepted) or `PATH=` before the check, and no execution-environment variable (PATH, HOME, NODE_*, PYTHON*, npm_config_*, *_OPTIONS, *_CONFIG*, *RC, …) inline or via --env — put those in project config; ordinary variables: `athena run --env FOO=1 -- npm test`',
  zero_tests: 'a runner reported 0 tests (or all skipped): run each package that has tests on its own, e.g. `athena run --covers AC1 -- npm test --workspace <pkg>` or `athena run -- python3 -m pytest <dir with tests>`',
  tree_changed_during_run: 'the source tree changed while the command ran (build output, snapshot, cache, or another writer): add generated paths to .gitignore, then run again on a quiet tree',
};
const SSH_FORM = 'ssh proves only in argv form, with a remote command, to a VM registered in ~/.athena/vm.json (host + user + port): `athena run -- ssh user@host \'npm run build && npm test\'`';
const KIND_FORM = 'only test / typecheck / build / docs commands are evidence, recognized by their first words: `athena run -- npm test`, `athena run -- python3 -m pytest -q`, `athena run -- npx tsc --noEmit`, `athena run -- npm run build`; docs: `athena run -- grep -F -q \'<text>\' docs/<file>.md`';

/** The provable-form line for an unprovable record, or null. */
function form(record, cmd) {
  if (!record || record.provable) return null;
  const known = FORMS[String(record.reason || '').split(':')[0]];
  if (known) return known;
  if (record.reason) return null; // exit_code_unknown etc.: nothing the caller can rephrase
  return /^\s*(?:\S*\/)?ssh(?:\s|$)/.test(cmd[0]) ? SSH_FORM : `kind=${record.kind}: ${KIND_FORM}`;
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

// Narrow read-only assertion grammar; all expanded targets must belong to the source tree.
function docsAssertion(command, cwd, ctx, tree) {
  const segments = words.commandSegments(command);
  if (segments.length !== 1 || segments[0].after || /[$`<>]/.test(command)) return false;
  const tokens = segments[0].words.map(t => t.value);
  if (!['grep', 'rg'].includes(tokens.shift())) return false;
  let fixed = false, pattern = null, endOptions = false;
  const files = [];
  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (!endOptions && token === '--') { endOptions = true; continue; }
    if (!endOptions && ['-e', '--regexp'].includes(token)) { if (pattern !== null || !tokens[i + 1]) return false; pattern = tokens[++i]; continue; }
    if (!endOptions && token.startsWith('-')) {
      if (/^-[Fqlni]+$/.test(token)) { fixed ||= token.includes('F'); continue; }
      if (['--fixed-strings', '--quiet', '--files-with-matches', '--line-number', '--ignore-case'].includes(token)) { fixed ||= token === '--fixed-strings'; continue; }
      return false;
    }
    if (pattern === null) pattern = token;
    else files.push(token);
  }
  if (!fixed || !pattern || !files.length) return false;
  const source = new Set(Object.keys(treeFiles(ctx.root, tree)));
  return files.every(file => {
    const abs = path.resolve(cwd, file);
    let targets = [abs];
    if (file.includes('*')) {
      if (!/^\*\.md$/.test(path.basename(file)) || path.dirname(file).includes('*')) return false;
      try { targets = fs.readdirSync(path.dirname(abs)).filter(n => n.endsWith('.md')).map(n => path.join(path.dirname(abs), n)); } catch (_) { return false; }
    }
    return targets.length > 0 && targets.every(target => {
      try {
        return target.endsWith('.md') && context.inside(target, ctx.root) && source.has(path.relative(ctx.root, target))
          && source.has(path.relative(ctx.root, fs.realpathSync(target))) && fs.statSync(target).isFile();
      } catch (_) { return false; }
    });
  });
}

/** Run opts.cmd in io.cwd and record it. Returns { exit, record } (record null without a sprint). */
function execute(opts, io) {
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
    return { exit, record: null };
  }
  const after = treeSha(ctx.root, ignore);
  const ssh = shell ? null : sshVm(opts.cmd, options.env);
  const docs = !ssh && docsAssertion(rawCommand, io.cwd, ctx, before);
  const kind = docs ? 'docs' : (evidence.classify(ssh ? ssh.remote : rawCommand) || 'other');
  const output = `${child.stdout || ''}${child.stderr || ''}`;
  let policy = shell ? evidence.policy(`set -o pipefail; ${rawCommand}`) : { provable: true, reason: null };
  if (!shell && WRAPPERS.test(path.basename(opts.cmd[0]))) policy = { provable: false, reason: 'wrapped_command' };
  if (ssh) policy = evidence.policy(ssh.remote);
  if (Object.keys(opts.env).some(name => EXECUTION_ENV.test(name))) policy = { provable: false, reason: 'validation_shadowable' };
  if (exit === 0 && kind === 'test' && zeroTests(output)) policy = { provable: false, reason: 'zero_tests: 零用例执行' };
  if (before !== after) policy = { provable: false, reason: 'tree_changed_during_run' };
  const record = evidence.append(ctx, {
    source: 'run', command, kind, exit, policy, covers: opts.covers, env: opts.env, argv: opts.cmd,
    tree_sha: after, ignore, output, ...(ssh || {}),
  });
  io.stderr.write(`[athena run] exit=${exit} kind=${record.kind} provable=${record.provable}${record.reason ? ` (${record.reason})` : ''} tree=${String(after).slice(0, 12)} → evidence ${record.id}\n`);
  const fix = form(record, opts.cmd);
  if (fix) io.stderr.write(`[athena run] provable form: ${fix}\n`);
  return { exit, record };
}

// Re-run commands with a historical PASS, carrying covers. Skip only if the latest attempt
// is already a provable PASS on this tree; any failed/unprovable replay makes rebind exit 1.
function rebind(io) {
  const ctx = context.load(io.cwd);
  if (!ctx || !ctx.sprint) { io.stderr.write('[athena run] --rebind: no active sprint, nothing to rebind\n'); return 2; }
  const ignore = reviewIgnore(ctx);
  const tree = treeSha(ctx.root, ignore);
  const latest = new Map();
  for (const row of evidence.read(ctx)) {
    if (row.source !== 'run') continue;
    // `command` is display text (bounded to 500 chars), not a replay identity.
    const key = JSON.stringify([row.argv || row.id, row.cwd, Object.entries(row.env || {}).sort()]);
    const passed = REBIND_KINDS.has(row.kind) && row.provable === true && row.exit === 0;
    if (!passed && !latest.has(key)) continue;
    // Retain later failed/unprovable attempts so they cannot reuse an older same-tree PASS.
    const covers = [...new Set([...((latest.get(key) || {}).covers || []), ...(passed ? row.covers || [] : [])])];
    latest.delete(key); // re-insert: iteration order = order of the latest record
    latest.set(key, { row, covers, passed });
  }
  if (!latest.size) {
    io.stderr.write('[athena run] --rebind: no provable PASS test/typecheck record in this sprint; run `athena run --covers AC1 -- <cmd…>` first\n');
    return 2;
  }
  const failed = [];
  let rerun = 0, kept = 0;
  for (const { row, covers, passed } of latest.values()) {
    if (passed && row.tree_sha === tree && JSON.stringify(row.ignore || []) === JSON.stringify(ignore)
        && covers.every(ac => (row.covers || []).includes(ac))) { kept += 1; continue; }
    const cwd = path.resolve(ctx.root, row.cwd || '.');
    if (!Array.isArray(row.argv) || !row.argv.length || !fs.existsSync(cwd)) {
      // No exact argv (recorded before 10.1.5, or redacted) or its cwd is gone: never guess a replay.
      io.stderr.write(`[athena run] rebind SKIPPED evidence ${row.id}: not replayable; run it again by hand: athena run${covers.length ? ` --covers ${covers.join(',')}` : ''} -- ${row.command}\n`);
      failed.push(row.command);
      continue;
    }
    io.stderr.write(`[athena run] rebind ${row.id} (${row.kind}${covers.length ? `, covers ${covers.join(',')}` : ''}): ${row.command}\n`);
    const { exit, record } = execute({ cmd: row.argv, env: { ...(row.env || {}) }, covers }, { ...io, cwd });
    rerun += 1;
    if (exit !== 0 || !record || record.provable !== true) {
      io.stderr.write(`[athena run] rebind FAILED (exit=${exit}${record ? ` provable=${record.provable}` : ''}; no PASS recorded): ${row.command}\n`);
      failed.push(row.command);
    }
  }
  io.stderr.write(`[athena run] rebind: ${rerun} re-run, ${kept} already on this tree, ${failed.length} failed → tree ${String(treeSha(ctx.root, ignore)).slice(0, 12)}\n`);
  if (failed.length) io.stderr.write('next: fix the failure, then `athena run --rebind`\n');
  return failed.length ? 1 : 0;
}

function main(argv, io) {
  const opts = parse(argv);
  return opts.rebind ? rebind(io) : execute(opts, io).exit;
}

module.exports = { main, parse, sshVm, zeroTests, form };
