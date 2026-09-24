'use strict';
// Shared CLI plumbing: context, argument flags, dates.
const fs = require('fs');
const path = require('path');
const context = require('../../lib/context.cjs');

class UsageError extends Error {}

function requireCtx(io) {
  const ctx = context.load(io.cwd);
  if (!ctx) throw new UsageError('no .ai_state found (run `athena init` first)');
  if (!ctx.indexExists) throw new UsageError('.ai_state/_index.md missing');
  return ctx;
}

/** --key value / --flag parsing; returns {flags, rest}. */
function flags(argv, spec) {
  const out = {};
  const rest = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) { rest.push(arg); continue; }
    const [name, inline] = arg.slice(2).split(/=(.*)/s);
    if (!(name in spec)) throw new UsageError(`unknown option --${name}`);
    if (spec[name] === 'bool') { out[name] = true; continue; }
    const value = inline !== undefined ? inline : argv[++i];
    if (value === undefined) throw new UsageError(`--${name} needs a value`);
    out[name] = value;
  }
  return { flags: out, rest };
}

const today = () => new Date().toISOString().slice(0, 10);
const VERSION = () => { try { return fs.readFileSync(path.join(__dirname, '..', '..', 'VERSION'), 'utf8').trim(); } catch (_) { return '10.1'; } };

module.exports = { requireCtx, flags, today, UsageError, VERSION };
