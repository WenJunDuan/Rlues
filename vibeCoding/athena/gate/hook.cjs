#!/usr/bin/env node
'use strict';
// Athena gate — the one hook entry point (design §5).
//   node hook.cjs <NativeEvent> --platform cc|cx     (stdin: the platform's hook payload)
//   require('hook.cjs').run('pi', payload)           (Pi extension, in-process)
// An adapter or core crash is fail-closed for pre_tool (exit 2) and fail-open elsewhere.
const fs = require('fs');
const path = require('path');

const PLATFORMS = new Set(['cc', 'cx', 'pi']);

function adapter(platform) {
  if (!PLATFORMS.has(platform)) throw new Error(`unknown platform ${platform}`);
  return require(path.join(__dirname, 'platform', `${platform}.cjs`));
}

/** payload → {event, result, output}. output is the adapter's rendering. */
function run(platform, payload, argEvent) {
  const a = adapter(platform);
  const ev = a.normalize(payload, argEvent);
  const result = require('./core.cjs').handle(ev);
  return { event: ev, result, output: a.render(result, ev) };
}

function parseArgs(argv) {
  const args = { event: '', platform: 'cc' };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--platform') args.platform = argv[++i] || '';
    else if (!args.event) args.event = argv[i];
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  let payload = {};
  try {
    const input = fs.readFileSync(0, 'utf8');
    if (input.trim()) payload = JSON.parse(input);
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('payload is not an object');
  } catch (error) {
    // Unreadable payload: nothing to judge. A PreToolUse must not slip through on it.
    if (/^PreToolUse$/.test(args.event)) { process.stderr.write(`[athena] BLOCKED: unreadable hook payload: ${error.message}\n`); process.exitCode = 2; }
    return;
  }
  try {
    const { output } = run(args.platform, payload, args.event);
    if (output.stdout) process.stdout.write(output.stdout);
    if (output.stderr) process.stderr.write(output.stderr);
    process.exitCode = output.code;
  } catch (error) {
    const pre = ((payload && payload.hook_event_name) || args.event) === 'PreToolUse';
    process.stderr.write(`[athena] ${pre ? 'BLOCKED: gate internal error' : 'gate internal error (allowed)'}: ${error.stack || error.message}\n`);
    process.exitCode = pre ? 2 : 0;
  }
}

if (require.main === module) main();
module.exports = { run, adapter };
