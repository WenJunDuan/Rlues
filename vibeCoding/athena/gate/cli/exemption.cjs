'use strict';
// Audited exemptions; validation shared with the hooks. H2/H3 have no key.
const fs = require('fs');
const { isDeepStrictEqual } = require('util');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const state = require('./lib/state.cjs');
const archive = require('./lib/archive.cjs');
const exemptions = require('../lib/exemptions.cjs');
const issues = require('../lib/issues.cjs');

const USAGE = `usage:
  athena exemption add --key <key> --until <YYYY-MM-DD> --reason "<why>"
  athena exemption list
  athena exemption remove --key <key>`;

function key(value) {
  if (!exemptions.KEYS.has(value)) throw new UsageError(`--key must be one of ${[...exemptions.KEYS].join(', ')}`);
}

function write(ctx, entries, action, entry) {
  const { file } = state.readIndex(ctx.aiState);
  const before = fs.readFileSync(file);
  try {
    state.setFields(file, { exemptions: entries });
    if (!isDeepStrictEqual(state.readIndex(ctx.aiState).fm.exemptions, entries)) throw new Error('exemption readback mismatch');
    issues.add(ctx.aiState, {
      type: 'gate', text: `exemption ${action} ${entry.key} until ${entry.until}`,
      found: `${today()} ${ctx.sprint || 'idle'}`, next: `reason: ${entry.reason}`, status: 'closed',
    });
  } catch (error) {
    fs.writeFileSync(file, before);
    throw error;
  }
  archive.stage(ctx, ['_index.md', 'issues.md']);
}

function add(argv, io) {
  const { flags: f, rest } = flags(argv, { key: 'str', until: 'str', reason: 'str' });
  if (rest.length) throw new UsageError('add takes --key, --until and --reason');
  key(f.key);
  const date = /^\d{4}-\d{2}-\d{2}$/.test(f.until || '') ? Date.parse(`${f.until}T00:00:00Z`) : NaN;
  if (!Number.isFinite(date) || new Date(date).toISOString().slice(0, 10) !== f.until) throw new UsageError('--until must be YYYY-MM-DD');
  const entry = { key: f.key, until: f.until, reason: String(f.reason || '').trim() };
  const check = exemptions.review({ exemptions: [entry] })[0];
  if (check.status !== 'active') throw new UsageError(check.why);
  const ctx = requireCtx(io);
  write(ctx, [...ctx.exemptions.filter(e => !e || e.key !== entry.key), entry], 'add', entry);
  io.stdout.write(`exemption ${entry.key} until ${entry.until}\n`);
  return 0;
}

function list(argv, io) {
  if (argv.length) throw new UsageError('list takes no arguments');
  const rows = exemptions.review(requireCtx(io));
  for (const { entry, status, why } of rows) {
    io.stdout.write(`${entry && entry.key} until ${entry && entry.until} [${status}] ${entry && entry.reason || ''}${why ? ` — ${why}` : ''}\n`);
  }
  if (!rows.length) io.stdout.write('(no exemptions)\n');
  return 0;
}

function remove(argv, io) {
  const { flags: f, rest } = flags(argv, { key: 'str' });
  if (rest.length) throw new UsageError('remove takes --key');
  if (f.key === undefined) throw new UsageError('remove takes --key');
  const ctx = requireCtx(io);
  const entry = ctx.exemptions.find(e => e && e.key === f.key);
  if (!entry) throw new UsageError(`${f.key} not found`);
  write(ctx, ctx.exemptions.filter(e => !e || e.key !== f.key), 'remove', entry);
  io.stdout.write(`exemption ${f.key} removed\n`);
  return 0;
}

function main(argv, io) {
  const [sub, ...rest] = argv;
  const table = { add, list, remove };
  if (!table[sub]) { io.stderr.write(`${USAGE}\n`); return 2; }
  try { return table[sub](rest, io); } catch (error) {
    if (error instanceof UsageError) { io.stderr.write(`athena exemption ${sub}: ${error.message}\n`); return 2; }
    throw error;
  }
}

module.exports = { main };
