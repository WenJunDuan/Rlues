'use strict';
// athena review prepare | accept | show (design §6, D4): review binds to the source-tree sha.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { requireCtx, flags, today, UsageError } = require('./lib/common.cjs');
const archive = require('./lib/archive.cjs');
const evidence = require('../lib/evidence.cjs');
const frontmatter = require('../lib/frontmatter.cjs');
const { git } = require('../lib/context.cjs');
const { treeSha, treeFiles } = require('../lib/tree-sha.cjs');
const { reviewIgnore } = require('../core.cjs');
const h1 = require('../rules/h1-design.cjs');

const USAGE = `usage:
  athena review prepare [--scope implementation|design]
  athena review accept --run <id|latest> [--file <reviewer output> | stdin] [--reviewer-agent <id>] [--family anthropic|openai|xai|…] [--platform cc|cx|pi]
  athena review show [--run <id|latest>]`;
const VERDICTS = new Set(['PASS', 'CONCERNS', 'REWORK', 'FAIL']);
const DIMENSIONS = ['spec coverage (MISSING/EXTRA/DEVIATED per AC)', 'correctness', 'security', 'test risk', 'over-engineering'];
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');

function runsDir(ctx) { return path.join(ctx.runtime, 'review'); }

function resolveRun(ctx, id) {
  const dir = runsDir(ctx);
  if (!id || id === 'latest') {
    let runs = [];
    try {
      runs = fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory() && fs.existsSync(path.join(dir, d.name, 'files.json')))
        .map(d => ({ n: d.name, t: fs.statSync(path.join(dir, d.name)).mtimeMs })).sort((a, b) => b.t - a.t);
    } catch (_) { /* none */ }
    if (!runs.length) throw new UsageError('no prepared review run; run `athena review prepare` first');
    return runs[0].n;
  }
  if (!/^[0-9a-f-]{8,40}$/.test(id) || !fs.existsSync(path.join(dir, id))) throw new UsageError(`unknown review run ${id}`);
  return id;
}

function changed(ctx, base, tree) {
  if (!base) return { stat: '(design.md has no base_commit)', names: [] };
  const baseTree = git(ctx.root, ['rev-parse', `${base}^{tree}`]);
  if (!baseTree) return { stat: `(base_commit ${base} not found)`, names: [] };
  return {
    stat: git(ctx.root, ['diff-tree', '-r', '--stat=120', baseTree, tree]) || '(no changes)',
    names: (git(ctx.root, ['diff-tree', '-r', '--name-status', baseTree, tree]) || '').split('\n').filter(Boolean),
  };
}

function prepare(argv, io) {
  const { flags: f } = flags(argv, { scope: 'str' });
  const scope = f.scope || 'implementation';
  if (!['implementation', 'design'].includes(scope)) throw new UsageError('--scope implementation|design');
  const ctx = requireCtx(io);
  if (!ctx.sprintDir || !fs.existsSync(path.join(ctx.sprintDir, 'design.md'))) throw new UsageError('no sprint with a design.md in flight');
  const design = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8');
  const base = String(frontmatter.parse(design).base_commit || '');
  const ignore = reviewIgnore(ctx);
  const tree = treeSha(ctx.root, ignore);
  const run = crypto.randomUUID();
  const dir = path.join(runsDir(ctx), run);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'files.json'), `${JSON.stringify({ run, scope, sprint: ctx.sprint, base_commit: base, tree_sha: tree, ignore, ac_sha: acSha(design), files: treeFiles(ctx.root, tree) })}\n`);
  const ac = h1.criteria(design);
  const diff = changed(ctx, base, tree);
  const valid = evidence.valid(ctx, tree, { ignore });
  const claims = design.split('\n').filter(l => /转录|transcribed/i.test(l)).slice(0, 20);
  const packet = [
    `# Review packet — ${ctx.sprint} (${scope})`, '',
    `- source tree: ${tree} (base ${base || '—'}); .ai_state excluded`,
    `- review_ignore (also excluded from the tree — challenge it if it hides source): ${ignore.length ? ignore.join(', ') : 'none'}`,
    `- design: .ai_state/sprints/${ctx.sprint}/design.md`, '',
    '## Acceptance', '', ...(ac.length ? ac.map(a => `- ${a.id}: ${a.text}`) : ['- (none found — that alone is a finding)']), '',
    '## Changes (base → current tree)', '', '```', diff.stat, '```', '', ...diff.names.slice(0, 200).map(n => `- ${n}`), '',
    '## Evidence on this tree', '', ...(valid.length ? valid.map(r => `- ${r.id} ${r.kind} exit ${r.exit} covers ${(r.covers || []).join(',') || '—'}: ${r.command}`) : ['- none yet (H2 will refuse ship)']), '',
    ...(claims.length ? ['## Transcribed claims (verify, do not trust)', '', ...claims, ''] : []),
    '## Dimensions', '', ...DIMENSIONS.map(d => `- ${d}`), '',
    '## Output contract', '', 'Follow the reviewer contract (agents/reviewer.md): findings lines `- [P0|P1|P2|P3] <file>:<line> — <text>`, then exactly one line `VERDICT: PASS|CONCERNS|REWORK|FAIL`. No run id, no timestamps, no frontmatter.', '',
  ].join('\n');
  fs.writeFileSync(path.join(dir, 'packet.md'), packet);
  io.stdout.write(`run ${run}\npacket ${path.relative(io.cwd, path.join(dir, 'packet.md'))}\nnext: give the packet to an independent reviewer, then \`athena review accept --run ${run} --file <its output>\`\n`);
  return 0;
}

/**
 * Contract parser (strict): outside code fences, every line that mentions VERDICT must be exactly
 * `VERDICT: X` and there must be one; every line carrying a [P0-3] tag must be a well-formed finding
 * `- [Pn] <loc> — <text>`. Anything looser is refused, so a PASS cannot be smuggled (review S3 P1).
 */
function parseOutput(text) {
  const lines = [];
  let fence = false;
  for (const line of String(text).split(/\r?\n/)) {
    if (/^\s*(```|~~~)/.test(line)) { fence = !fence; continue; }
    if (!fence) lines.push(line);
  }
  if (fence) throw new UsageError('unterminated code fence in reviewer output');
  const verdicts = [];
  const findings = [];
  for (const line of lines) {
    if (/^[\s>*_#`~<!-]*verdict\b/i.test(line)) { // a line that *opens* with VERDICT (any markup/case); prose mentions are fine
      const m = line.match(/^VERDICT: (PASS|CONCERNS|REWORK|FAIL)$/);
      if (!m) throw new UsageError(`malformed verdict line: "${line.trim().slice(0, 80)}" (must be exactly \`VERDICT: PASS|CONCERNS|REWORK|FAIL\`)`);
      verdicts.push(m[1]);
    }
    if (/[[(]\s*p\d+\s*[\])]/i.test(line)) { // anything tag-like must be an exact [P0]–[P3] finding
      const m = line.match(/^- \[(P[0-3])\] (\S.*?) (?:—|–|--) (\S.*)$/);
      if (!m) throw new UsageError(`malformed finding line: "${line.trim().slice(0, 80)}" (must be \`- [Pn] <file>:<line> — <text>\`)`);
      findings.push({ sev: m[1], loc: m[2], text: m[3].trim() });
    }
  }
  if (verdicts.length !== 1) throw new UsageError(`reviewer output must hold exactly one \`VERDICT: PASS|CONCERNS|REWORK|FAIL\` line (found ${verdicts.length})`);
  if (verdicts[0] === 'PASS' && findings.some(x => x.sev === 'P0' || x.sev === 'P1')) throw new UsageError('VERDICT: PASS with P0/P1 findings is contradictory');
  return { verdict: verdicts[0], findings };
}

/** sha of the acceptance lines: a review covers these ACs; adding or changing one makes it stale. */
function acSha(designText) {
  return sha(JSON.stringify(h1.criteria(designText)));
}

function accept(argv, io) {
  const { flags: f } = flags(argv, { run: 'str', file: 'str', 'reviewer-agent': 'str', family: 'str', platform: 'str' });
  const ctx = requireCtx(io);
  if (!ctx.sprintDir) throw new UsageError('no sprint in flight');
  const run = resolveRun(ctx, f.run || 'latest');
  const saved = JSON.parse(fs.readFileSync(path.join(runsDir(ctx), run, 'files.json'), 'utf8'));
  if (saved.sprint !== ctx.sprint) throw new UsageError(`run ${run} belongs to sprint ${saved.sprint}, not ${ctx.sprint}`);
  if (!f.file && process.stdin.isTTY) throw new UsageError('give the reviewer output with --file <path> (or pipe it on stdin)');
  const packetPath = path.join(runsDir(ctx), run, 'packet.md');
  if (f.file && fs.statSync(path.resolve(io.cwd, f.file)).mtimeMs < fs.statSync(packetPath).mtimeMs) {
    throw new UsageError(`${f.file} is older than the packet of run ${run}; it cannot be a review of it`);
  }
  const text = f.file ? fs.readFileSync(path.resolve(io.cwd, f.file), 'utf8') : fs.readFileSync(0, 'utf8');
  const parsed = parseOutput(text);
  // replay guard: one reviewer output is accepted for one run only (review S3 P1)
  const outputSha = sha(text);
  const ledger = path.join(runsDir(ctx), 'accepted.jsonl');
  const used = (() => { try { return fs.readFileSync(ledger, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)); } catch (_) { return []; } })();
  const reuse = used.find(u => u.output_sha === outputSha && u.run !== run);
  if (reuse) throw new UsageError(`this reviewer output was already accepted for run ${reuse.run}; a new run needs a new review`);
  const ignore = reviewIgnore(ctx);
  const tree = treeSha(ctx.root, ignore);
  if (tree !== saved.tree_sha || JSON.stringify(ignore) !== JSON.stringify(saved.ignore)) {
    const now = treeFiles(ctx.root, tree);
    const lines = [];
    for (const file of [...new Set([...Object.keys(saved.files), ...Object.keys(now)])].sort()) {
      if (saved.files[file] !== now[file]) lines.push(`  ${file}: expected ${saved.files[file] ? saved.files[file].slice(0, 12) : '(absent)'} actual ${now[file] ? now[file].slice(0, 12) : '(absent)'}`);
    }
    if (JSON.stringify(ignore) !== JSON.stringify(saved.ignore)) lines.push(`  review_ignore: expected ${JSON.stringify(saved.ignore)} actual ${JSON.stringify(ignore)}`);
    io.stderr.write(`athena review accept: source changed since prepare (run ${run}); the review covers the old tree:\n${lines.slice(0, 50).join('\n')}\nrun \`athena review prepare\` again and re-review.\n`);
    return 4;
  }
  const packet = fs.readFileSync(packetPath, 'utf8');
  const design = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8');
  if (saved.ac_sha && saved.ac_sha !== acSha(design)) {
    io.stderr.write(`athena review accept: design acceptance lines changed since prepare (run ${run}); prepare again so the reviewer sees them\n`);
    return 4;
  }
  const record = {
    schema: 1, run, scope: saved.scope, base_commit: saved.base_commit, tree_sha: tree, ignore, packet_sha: sha(packet),
    ac_sha: acSha(design), output_sha: outputSha,
    verdict: parsed.verdict, findings: parsed.findings,
    reviewer: { platform: f.platform || null, agent_id: f['reviewer-agent'] || null, family: f.family || process.env.ATHENA_REVIEWER_FAMILY || 'unknown' },
    accepted_at: new Date().toISOString(),
  };
  fs.writeFileSync(path.join(ctx.sprintDir, 'review.json'), `${JSON.stringify(record, null, 2)}\n`);
  fs.appendFileSync(ledger, `${JSON.stringify({ run, output_sha: outputSha, at: record.accepted_at })}\n`);
  fs.appendFileSync(path.join(ctx.sprintDir, 'log.md'), `- ${today()} review ${run.slice(0, 8)}: ${parsed.verdict} (${parsed.findings.length} findings)\n`);
  archive.stage(ctx, [`sprints/${ctx.sprint}/review.json`, `sprints/${ctx.sprint}/log.md`]);
  io.stdout.write(`review ${run}: ${parsed.verdict}, ${parsed.findings.length} finding(s) → sprints/${ctx.sprint}/review.json\n`);
  return parsed.verdict === 'PASS' ? 0 : 3;
}

function show(argv, io) {
  const { flags: f } = flags(argv, { run: 'str' });
  const ctx = requireCtx(io);
  if (f.run) {
    const run = resolveRun(ctx, f.run);
    io.stdout.write(fs.readFileSync(path.join(runsDir(ctx), run, 'packet.md'), 'utf8'));
    return 0;
  }
  const file = ctx.sprintDir && path.join(ctx.sprintDir, 'review.json');
  if (!file || !fs.existsSync(file)) { io.stdout.write('no review.json for the current sprint\n'); return 0; }
  const r = JSON.parse(fs.readFileSync(file, 'utf8'));
  const current = treeSha(ctx.root, reviewIgnore(ctx));
  const acNow = acSha(fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8'));
  const state = r.tree_sha !== current ? 'STALE: source changed' : (r.ac_sha && r.ac_sha !== acNow ? 'STALE: acceptance lines changed' : 'current');
  io.stdout.write(`${r.verdict} run ${r.run} tree ${String(r.tree_sha).slice(0, 12)} (${state}) reviewer ${r.reviewer && r.reviewer.family}\n`);
  for (const x of r.findings || []) io.stdout.write(`- [${x.sev}] ${x.loc} — ${x.text}\n`);
  return 0;
}

function main(argv, io) {
  const [sub, ...rest] = argv;
  const table = { prepare, accept, show };
  if (!table[sub]) { io.stderr.write(`${USAGE}\n`); return 2; }
  try { return table[sub](rest, io); } catch (error) {
    if (error instanceof UsageError) { io.stderr.write(`athena review ${sub}: ${error.message}\n`); return 2; }
    throw error;
  }
}

module.exports = { main, parseOutput, acSha };
