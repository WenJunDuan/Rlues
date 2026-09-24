#!/usr/bin/env node
'use strict';
// athena CLI (design §7.4). Each subcommand lives in cli/<name>.cjs and exports
// main(argv, io) → exit code. io = {cwd, stdout, stderr, env}.
const fs = require('fs');
const path = require('path');

const USAGE = `usage: athena <command> [args]
  run [--covers AC1,AC2] -- <cmd…>   run a check and record its exit code as evidence
Other commands appear as their slices land (review, status, sprint, ship, issue, tidy, migrate, install, doctor).`;

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
