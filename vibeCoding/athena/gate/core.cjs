'use strict';
// Gate core: one normalized AthenaEvent in, one decision out
// ({decision: allow|block|warn, reason?, context?, warnings[]}). Platform-free.
const fs = require('fs');
const path = require('path');
const context = require('./lib/context.cjs');
const ledger = require('./lib/ledger.cjs');
const evidence = require('./lib/evidence.cjs');
const exemptions = require('./lib/exemptions.cjs');
const issues = require('./lib/issues.cjs');
const frontmatter = require('./lib/frontmatter.cjs');
const { treeSha, usableGlob } = require('./lib/tree-sha.cjs');
const h1 = require('./rules/h1-design.cjs');
const h2 = require('./rules/h2-evidence.cjs');
const h3 = require('./rules/h3-review.cjs');
const h4 = require('./rules/h4-isolation.cjs');
const h5 = require('./rules/h5-shell.cjs');
const advisory = require('./rules/advisory.cjs');

const allow = (extra = {}) => ({ decision: 'allow', warnings: [], ...extra });
const block = (verdict, warnings = []) => ({ decision: 'block', rule: verdict.rule, reason: verdict.reason, warnings });

/** Hard rules fail closed: an exception is a block naming the rule. */
function hard(rule, fn) {
  try { return fn(); } catch (error) { return { rule, reason: `${rule} internal fail-closed error: ${error.message}` }; }
}

function reviewIgnore(ctx) {
  if (!ctx.sprintDir) return [];
  let text = '';
  try { text = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8'); } catch (_) { return []; }
  const value = frontmatter.parse(text).review_ignore;
  return Array.isArray(value) ? value.filter(usableGlob).map(g => g.trim()).sort() : [];
}

/** Current source tree sha of ctx.root (memoized per event). */
function tree(ctx) {
  if (ctx.tree === undefined) ctx.tree = treeSha(ctx.root, reviewIgnore(ctx));
  return ctx.tree;
}

/** The evidence ledger and review.json are written only by athena itself (any stage). */
function ledgerWrite(ev, ctx) {
  const state = context.realExisting(ctx.aiState).toLowerCase();
  const guarded = (ev.paths || []).filter(file => {
    // Symlinks resolved and compared case-insensitively (APFS default) — review r3.
    const rel = path.relative(state, context.realExisting(file).toLowerCase()).split(path.sep).join('/');
    return !rel.startsWith('..') && (/^\.runtime\/evidence\//.test(rel) || /^sprints\/[^/]+\/review\.json$/.test(rel));
  });
  return guarded.length ? { rule: 'H2', reason: `H2 ledger: ${guarded.map(f => path.relative(ctx.mainRoot, f)).join(', ')} is written only by \`athena run\` / \`athena review accept\`` } : null;
}

function preTool(ev, ctx) {
  if (ev.tool === 'bash') {
    const verdict = hard('H5', () => h5.check(ev, ctx));
    return verdict ? block(verdict) : allow();
  }
  if (!ctx || context.idle(ctx)) return allow();
  if (ev.tool === 'write') {
    const verdict = hard('H2', () => ledgerWrite(ev, ctx)) || hard('H1', () => h1.check(ev, ctx));
    return verdict ? block(verdict) : allow();
  }
  if (ev.tool === 'agent') {
    let result;
    try { result = h4.check(ev, ctx); } catch (error) { result = { verdict: { rule: 'H4', reason: `H4 internal fail-closed error: ${error.message}` } }; }
    const warnings = result.warn ? [{ rule: 'H4', message: result.warn }] : [];
    return result.verdict ? block(result.verdict, warnings) : allow({ warnings });
  }
  return allow();
}

/** Fallback evidence collector: only recognized validation commands, only when a sprint is active. */
function postTool(ev, ctx) {
  if (!ctx || !ctx.sprint || ev.tool !== 'bash' || !ev.command || ev.via_athena_run) return allow();
  if (/(^|[\s;&|])athena(\.cjs)?\s+run\b|cli\.cjs\s+run\b/.test(ev.command)) return allow();
  const kind = evidence.classify(ev.command);
  if (!kind) return allow();
  try {
    evidence.append(ctx, { source: 'collector', platform: ev.platform, command: ev.command, kind, exit: ev.exit_code, tree_sha: tree(ctx), ignore: reviewIgnore(ctx) });
  } catch (error) {
    return allow({ warnings: [{ rule: 'evidence', message: `collector failed: ${error.message}` }] });
  }
  return allow();
}

/** Stop: read-only unless stage=ship; at ship H2 + H3 (+ advisories), with the circuit breaker. */
function stop(ev, ctx) {
  if (!ctx || context.idle(ctx)) return allow();
  // Unknown state: writes and pushes are already strict; a read-only Stop only warns (AC7).
  if (ctx.invalid) return allow({ warnings: [{ rule: 'state', message: `project state unknown (${ctx.invalid}); fix .ai_state/_index.md` }] });
  if (ctx.stage !== 'ship') return allow();
  const verdict = hard('H2', () => h2.check(ev, ctx, tree(ctx), reviewIgnore(ctx))) || hard('H3', () => h3.check(ev, ctx, tree(ctx), reviewIgnore(ctx)));
  const warnings = advisory.run(ctx, ev, advisory.AT.ship);
  if (!verdict) {
    ledger.pass(ctx, ev);
    return allow({ warnings });
  }
  if (ledger.breaker(ctx, ev, verdict.reason) === 'release') {
    return allow({ warnings: [...warnings, { rule: verdict.rule, message: `circuit breaker released a repeated block (issues.md gate row added): ${verdict.reason}` }] });
  }
  return block(verdict, warnings);
}

/** Context injected at session start / prompt / after compaction. */
function inject(ev, ctx) {
  if (!ctx) return allow();
  const lines = [];
  const i = ctx.index;
  if (context.idle(ctx)) lines.push('[athena] idle — no sprint in flight.');
  else lines.push(`[athena] path=${ctx.path || '?'} stage=${ctx.stage || '?'} sprint=${ctx.sprint || '?'}`);
  if (i.next_action) lines.push(`next_action: ${String(i.next_action).slice(0, 160)}`);
  const active = exemptions.review(ctx).filter(x => x.status === 'active');
  for (const x of active) lines.push(`exemption ${x.entry.key} until ${x.entry.until}: ${x.entry.reason}`);
  const warnings = ev.event === 'session_start' ? advisory.run(ctx, ev, advisory.AT.session) : [];
  const queued = ledger.drain(ctx);
  for (const w of [...warnings, ...queued].slice(0, 8)) lines.push(`advisory ${w.rule}: ${w.message}`);
  if (ev.event === 'session_start') {
    for (const q of issues.list(ctx.aiState).filter(r => r.type === 'question' && r.status === 'open').slice(0, 5)) {
      lines.push(`待裁定 ${q.id}: ${q.text}`);
    }
    try { // AC5 (S4): deferred / paused items whose `resume_when: after <item>` is satisfied
      const state = require('./cli/lib/state.cjs');
      const items = state.allItems(ctx.aiState);
      for (const it of items.filter(x => ['deferred', 'paused'].includes(String(x.data.status)))) {
        const when = it.data.deferred && it.data.deferred.resume_when;
        if (state.resumeReady(ctx.aiState, when, items) === true) lines.push(`resume ready ${it.roadmap}/${it.slug}: ${when}`);
      }
    } catch (_) { /* injection is best-effort */ }
  }
  const text = lines.join('\n');
  return allow({ context: ev.event === 'prompt' && !queued.length ? undefined : text.slice(0, 2000) });
}

function record(ctx, name, row) {
  if (!ctx) return allow();
  try { ledger.appendJsonl(path.join(ctx.runtime, name), { ts: new Date().toISOString(), sprint: ctx.sprint, ...row }); }
  catch (_) { /* telemetry is best-effort */ }
  return allow();
}

function handle(ev) {
  const ctx = context.load(ev.cwd);
  let result;
  switch (ev.event) {
    case 'pre_tool': result = preTool(ev, ctx); break;
    case 'post_tool': case 'post_tool_fail': result = postTool(ev, ctx); break;
    case 'stop': result = stop(ev, ctx); break;
    case 'session_start': case 'prompt': case 'compact': result = inject(ev, ctx); break;
    case 'subagent_start': case 'subagent_stop':
      result = record(ctx, 'subagents.jsonl', { event: ev.event, type: ev.agent && ev.agent.type, id: ev.agent && ev.agent.id, platform: ev.platform });
      break;
    case 'config': result = record(ctx, 'config-events.jsonl', { event: ev.raw_event, platform: ev.platform }); break;
    default: result = allow();
  }
  if (ctx && result.warnings.length && !['session_start', 'prompt', 'compact'].includes(ev.event)) {
    try { ledger.advise(ctx, result.warnings); } catch (_) { /* best-effort */ }
  }
  return result;
}

module.exports = { handle, tree, reviewIgnore };
