#!/usr/bin/env node
'use strict';
// athena CLI (design §7.4). Each subcommand lives in cli/<name>.cjs and exports
// main(argv, io) → exit code. io = {cwd, stdout, stderr, env}.
const fs = require('fs');
const path = require('path');

const USAGE = `usage: athena <command> [args]
  init [--dry-run]                     create .ai_state v2 in a new project
  status [--json]                      route, hot sprints, queue, waiting items, issues, exemptions
  sprint start|stage|pause|resume|drop open and move sprints (athena sprint for details)
  run [--covers AC1,AC2] -- <cmd…>     run a check and record its exit code as evidence
  review prepare|accept|show           bind an independent review to the source tree
  ship [--dry-run]                     H2/H3, archive, items done, _index idle (stages, never commits)
  issue add|close|list                 the issues.md ledger
  tidy [--dry-run]                     month-close, packing, hot-layer limit, .runtime retention
  migrate --to 10.1 [--dry-run]        v1 → v2 state migration
  install|rollback|doctor              install into ~/.athena and the platform homes; undo; check`;

function commands() {
  const dir = path.join(__dirname, 'cli');
  try { return fs.readdirSync(dir).filter(f => f.endsWith('.cjs')).map(f => f.slice(0, -4)).sort(); } catch (_) { return []; }
}

function main(argv, io = { cwd: process.cwd(), stdout: process.stdout, stderr: process.stderr, env: process.env }) {
  const [name, ...rest] = argv;
  if (!name || name === '-h' || name === '--help' || name === 'help') {
    io.stdout.write(`${USAGE}\navailable: ${commands().join(', ')}\n`);
    return name ? 0 : 1;
  }
  if (!/^[a-z][a-z-]*$/.test(name) || !commands().includes(name)) {
    io.stderr.write(`athena: unknown command "${name}"\n${USAGE}\n`);
    return 2;
  }
  return require(path.join(__dirname, 'cli', `${name}.cjs`)).main(rest, io);
}

if (require.main === module) {
  try { process.exitCode = main(process.argv.slice(2)); }
  catch (error) { process.stderr.write(`athena: ${error.message}\n`); process.exitCode = 2; }
}
module.exports = { main };
