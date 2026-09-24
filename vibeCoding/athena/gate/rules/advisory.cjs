'use strict';
// A1–A10 advisory checks (design §5.4): warn, never block. Each check is isolated; an internal
// error is itself a warning (allow + warn).
const fs = require('fs');
const path = require('path');
const frontmatter = require('../lib/frontmatter.cjs');
const exemptions = require('../lib/exemptions.cjs');
const issues = require('../lib/issues.cjs');
const evidence = require('../lib/evidence.cjs');
const ledger = require('../lib/ledger.cjs');
const { git } = require('../lib/context.cjs');
const { readReview, FAMILY } = require('./h3-review.cjs');

const GENERATOR_PATHS = new Set(['Feature', 'Refactor', 'System']);
const RED = new Set(['Refactor', 'System']);
const PROMISE = /(记|登|转|→)\s*`?(?:vm-pending|issues)(?!\.md)/;

const read = (file) => { try { return fs.readFileSync(file, 'utf8'); } catch (_) { return null; } };
const sprintFile = (ctx, name) => (ctx.sprintDir ? path.join(ctx.sprintDir, name) : null);
const designFm = (ctx) => frontmatter.parse(read(sprintFile(ctx, 'design.md')) || '');
const skipped = (ctx, key) => Boolean(exemptions.active(ctx, key)) || ctx.index[key] === true;
const logText = (ctx) => ['log.md', 'session-log.md'].map(n => read(sprintFile(ctx, n)) || '').join('\n');

const CHECKS = {
  /** A1 writer provenance (D1: was a hard gate). */
  A1(ctx) {
    if (!GENERATOR_PATHS.has(ctx.path) || !ctx.sprintDir) return null;
    if (fs.existsSync(sprintFile(ctx, 'external-writer.json'))) return null;
    const rows = ledger.readJsonl(path.join(ctx.runtime, 'subagents.jsonl'));
    if (rows.some(r => r.sprint === ctx.sprint && /generator|writer/i.test(String(r.type || '')))) return null;
    return 'no generator/external writer recorded for this sprint (main agent wrote the code?) — fine for small changes; otherwise note the writer in log.md';
  },
  /** A2 R/S runtime-verify and polish before review. */
  A2(ctx) {
    if (!RED.has(ctx.path) || !ctx.sprintDir) return null;
    const log = logText(ctx);
    const miss = [];
    if (!skipped(ctx, 'skip_runtime_verify') && !fs.existsSync(sprintFile(ctx, 'runtime-verify.md')) && !/runtime-verify/i.test(log)) miss.push('runtime-verify');
    if (!skipped(ctx, 'skip_polish') && !fs.existsSync(sprintFile(ctx, 'cleanup-pass.md')) && !/polish|cleanup/i.test(log)) miss.push('polish');
    return miss.length ? `${miss.join(' + ')} not recorded (log.md line or exemption)` : null;
  },
  /** A3 R/S: ≥5 files changed since design.base_commit and no architecture/ update (P17 anchor). */
  A3(ctx) {
    if (!RED.has(ctx.path) || skipped(ctx, 'skip_architecture_check')) return null;
    const base = String(designFm(ctx).base_commit || '').trim();
    if (!/^[0-9a-f]{7,40}$/i.test(base)) return 'design.md has no base_commit; architecture drift cannot be anchored';
    const committed = (git(ctx.root, ['diff', '--name-only', `${base}..HEAD`]) || '').split('\n');
    const working = (git(ctx.root, ['status', '--porcelain', '--untracked-files=all']) || '').split('\n').map(l => l.slice(3));
    const files = [...new Set([...committed, ...working].filter(Boolean))].filter(f => !f.startsWith('.ai_state/') || f.startsWith('.ai_state/architecture/'));
    if (files.length < 5 || files.some(f => /(^|\/)architecture\//.test(f))) return null;
    return `${files.length} files changed since ${base.slice(0, 7)} but no architecture/ update`;
  },
  /** A4 promise closure: "记 issues / vm-pending" written but no row mentions the sprint. */
  A4(ctx) {
    if (!ctx.sprintDir) return null;
    const design = read(sprintFile(ctx, 'design.md')) || '';
    if (ctx.path === 'Quick' && /vm-pending\.md|issues\.md/.test(design)) return null;
    const texts = ['design.md', 'log.md', 'session-log.md', 'runtime-verify.md', 'cleanup-pass.md'].map(n => read(sprintFile(ctx, n)) || '');
    if (!texts.some(t => PROMISE.test(t))) return null;
    const ledgers = [read(path.join(ctx.aiState, 'vm-pending.md')) || '', ...issues.list(ctx.aiState).map(r => `${r.found} ${r.next} ${r.text}`)];
    return ledgers.some(t => t.includes(ctx.sprint)) ? null : `a promise to log vm-pending/issues was written but no ledger row mentions ${ctx.sprint}`;
  },
  /** A5 design changed after implementation began (only when the baseline already had it). */
  A5(ctx) {
    if (!ctx.sprintDir) return null;
    const base = String(designFm(ctx).base_commit || '').trim();
    if (!base) return null;
    const owner = path.dirname(ctx.aiState); // the checkout that holds this .ai_state (main-first)
    const rel = path.relative(owner, path.join(ctx.sprintDir, 'design.md')).split(path.sep).join('/');
    if (git(owner, ['cat-file', '-e', `${base}:${rel}`]) === null) return null;
    const changed = git(owner, ['diff', '--name-only', base, '--', rel]);
    return changed ? 'design.md changed after implementation began; make sure the review covered the new acceptance lines' : null;
  },
  /** A6 _index pointers resolve. */
  A6(ctx) {
    const pointers = ctx.index.pointers && typeof ctx.index.pointers === 'object' ? ctx.index.pointers : {};
    const dead = [];
    for (const [key, value] of Object.entries(pointers)) {
      for (const target of (Array.isArray(value) ? value : [value])) {
        if (typeof target !== 'string' || !/\.(md|ya?ml|json)$/.test(target)) continue;
        const clean = target.replace(/#.*$/, '').replace(/^\.ai_state\//, '');
        if (!fs.existsSync(path.join(ctx.aiState, clean))) dead.push(`${key}→${target}`);
      }
    }
    return dead.length ? `dead _index pointers: ${dead.slice(0, 5).join(', ')}` : null;
  },
  /** A7 hygiene thresholds. */
  A7(ctx) {
    const notes = [];
    let hot = [];
    try { hot = fs.readdirSync(path.join(ctx.aiState, 'sprints'), { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'archive'); } catch (_) { /* none */ }
    if (hot.length > 3) notes.push(`${hot.length} hot sprints (>3)`);
    const open = issues.list(ctx.aiState).filter(r => !['closed', 'dropped'].includes(r.status));
    if (open.length > 40) notes.push(`${open.length} open issues (>40)`);
    if (ctx.schema === 2) {
      const size = Buffer.byteLength(read(path.join(ctx.aiState, '_index.md')) || '');
      if (size > 3072) notes.push(`_index.md ${size} B (>3 KB)`);
    }
    return notes.length ? `tidy due: ${notes.join('; ')} — run \`athena tidy\`` : null;
  },
  /** A8 exemptions expiring or invalid. */
  A8(ctx) {
    const notes = exemptions.review(ctx).filter(x => x.status !== 'active' || x.daysLeft <= 2)
      .map(x => `${x.entry && x.entry.key}: ${x.status === 'active' ? `expires ${x.entry.until}` : x.why}`);
    return notes.length ? `exemptions: ${notes.join('; ')}` : null;
  },
  /** A9 Bugfix: reproduction test modified after its red record (flag bugfix_test_lock). */
  A9(ctx) {
    if (ctx.path !== 'Bugfix' || !ctx.flags.bugfix_test_lock) return null;
    const repro = String(designFm(ctx).repro_test || '').trim();
    if (!repro) return null;
    const red = evidence.read(ctx).find(r => r.kind === 'test' && Number.isInteger(r.exit) && r.exit !== 0);
    if (!red) return `repro_test ${repro} has no failing (red) record yet`;
    let mtime;
    try { mtime = fs.statSync(path.resolve(ctx.root, repro)).mtimeMs; } catch (_) { return `repro_test ${repro} not found`; }
    return mtime > Date.parse(red.ts) ? `repro_test ${repro} was modified after its red record ${red.id}` : null;
  },
  /** A10 reviewer and author from the same model family. */
  A10(ctx, ev) {
    if (!ctx.sprintDir || ctx.flags.cross_family_review) return null;
    const { data } = readReview(ctx);
    const author = FAMILY[ev.platform];
    return data && author && data.reviewer && data.reviewer.family === author ? `reviewer family ${author} equals the author's` : null;
  },
};

const AT = {
  ship: ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A9', 'A10'],
  session: ['A7', 'A8'],
};

/** Run the named checks; returns [{rule, message}]. */
function run(ctx, ev, names) {
  const out = [];
  for (const name of names) {
    try {
      const message = CHECKS[name](ctx, ev);
      if (message) out.push({ rule: name, message });
    } catch (error) {
      out.push({ rule: name, message: `internal error (allowed): ${error.message}` });
    }
  }
  return out;
}

module.exports = { run, CHECKS, AT };
