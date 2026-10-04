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
const { treeSha, treeFiles, pathspec } = require('../lib/tree-sha.cjs');
const { reviewIgnore } = require('../core.cjs');
const h1 = require('../rules/h1-design.cjs');

const USAGE = `usage:
  athena review prepare [--scope implementation|design]
  athena review accept --run <id|latest> [--file <reviewer output> | stdin] [--reviewer-agent <id>] [--family anthropic|openai|xai|…] [--platform cc|cx|pi]
  athena review show [--run <id|latest>]`;
const VERDICTS = new Set(['PASS', 'CONCERNS', 'REWORK', 'FAIL']);
const DIMENSIONS = ['spec coverage (MISSING/EXTRA/DEVIATED per AC)', 'correctness', 'security', 'test risk', 'over-engineering'];
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');
// Every refusal of `accept` carries the corrected line format and the next command (10.1.5 S1):
// guidance in the tool output is read at the moment it is needed.
const SAMPLE = '- [P2] src/app.js:42 — <what is wrong>\n- [P3] evidence:<id> — <text>   (also packet:— / design:AC1)\nVERDICT: CONCERNS   (exactly one line, one of PASS|CONCERNS|REWORK|FAIL, no markup)';
const PREPARE = 'athena review prepare';
const acceptCmd = (run) => `athena review accept --run ${run || 'latest'} --file <reviewer output>`;

/** UsageError that names the next command (and, for contract errors, the sample lines). */
function refuse(message, next, sample) {
  return Object.assign(new UsageError(message), { next, sample });
}

function runsDir(ctx) { return path.join(ctx.runtime, 'review'); }

function resolveRun(ctx, id) {
  const dir = runsDir(ctx);
  if (!id || id === 'latest') {
    let runs = [];
    try {
      runs = fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory() && fs.existsSync(path.join(dir, d.name, 'files.json')))
        .map(d => ({ n: d.name, t: fs.statSync(path.join(dir, d.name)).mtimeMs })).sort((a, b) => b.t - a.t);
    } catch (_) { /* none */ }
    if (!runs.length) throw refuse('no prepared review run; run `athena review prepare` first', PREPARE);
    return runs[0].n;
  }
  if (!/^[0-9a-f-]{8,40}$/.test(id) || !fs.existsSync(path.join(dir, id))) throw refuse(`unknown review run ${id}`, acceptCmd('latest'));
  return id;
}

// The current tree omits .ai_state and review_ignore; diff the base through the same pathspec
// or every tracked .ai_state file reads as deleted (G-003).
function changed(ctx, base, tree, ignore) {
  if (!base) return { stat: '(design.md has no base_commit)', names: [] };
  const baseTree = git(ctx.root, ['rev-parse', `${base}^{tree}`]);
  if (!baseTree) return { stat: `(base_commit ${base} not found)`, names: [] };
  const spec = ['--', ...pathspec(ignore)];
  return {
    stat: git(ctx.root, ['diff-tree', '-r', '--stat=120', baseTree, tree, ...spec]) || '(no changes)',
    names: (git(ctx.root, ['diff-tree', '-r', '--name-status', baseTree, tree, ...spec]) || '').split('\n').filter(Boolean),
  };
}

// Commits made while this sprint is paused belong to the other active slice. Legacy
// logs without HEAD boundaries keep the inclusive diff: unknown ownership is never hidden.
function excludedCommits(ctx, base) {
  let log = '';
  try { log = fs.readFileSync(path.join(ctx.sprintDir, 'log.md'), 'utf8'); } catch (_) { return []; }
  const range = new Set((git(ctx.root, ['rev-list', `${base}..HEAD`]) || '').split('\n').filter(Boolean));
  const excluded = new Set();
  let paused = null;
  for (const line of log.split('\n')) {
    const m = line.match(/ (paused|resumed) at .*?\(head ([0-9a-f]{40,64})\)/);
    if (!m) continue;
    if (m[1] === 'paused') paused = m[2];
    else if (paused) {
      const commits = git(ctx.root, ['rev-list', `${paused}..${m[2]}`]);
      for (const commit of (commits || '').split('\n')) if (range.has(commit)) excluded.add(commit);
      paused = null;
    }
  }
  return [...excluded];
}

function sprintChanges(ctx, base, tree, ignore, excluded) {
  if (!excluded.length) return changed(ctx, base, tree, ignore);
  const omit = new Set(excluded);
  const commits = (git(ctx.root, ['rev-list', '--reverse', '--first-parent', `${base}..HEAD`]) || '').split('\n').filter(c => c && !omit.has(c));
  const spec = ['--', ...pathspec(ignore)];
  const stats = [], names = new Set();
  // Per-commit patches retain this sprint's edits even when another slice touched the same file.
  const pairs = commits.map(c => [c + '^', c]);
  pairs.push(['HEAD', tree]); // staged, unstaged and untracked source are still reviewed
  for (const [from, to] of pairs) {
    const stat = git(ctx.root, ['diff-tree', '-r', '--stat=120', from, to, ...spec]);
    if (stat) stats.push(`${from} → ${to}\n${stat}`);
    for (const name of (git(ctx.root, ['diff-tree', '-r', '--name-status', from, to, ...spec]) || '').split('\n')) if (name) names.add(name);
  }
  return { stat: stats.join('\n') || '(no changes)', names: [...names] };
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
  const excluded = excludedCommits(ctx, base);
  const diff = sprintChanges(ctx, base, tree, ignore, excluded);
  const valid = evidence.valid(ctx, tree, { ignore });
  const claims = design.split('\n').filter(l => /转录|transcribed/i.test(l)).slice(0, 20);
  const packet = [
    `# Review packet — ${ctx.sprint} (${scope})`, '',
    `- source tree: ${tree} (base ${base || '—'}); .ai_state excluded`,
    `- review_ignore (also excluded from the tree — challenge it if it hides source): ${ignore.length ? ignore.join(', ') : 'none'}`,
    `- design: .ai_state/sprints/${ctx.sprint}/design.md`, '',
    ...(excluded.length ? ['## Excluded commits (paused intervals)', '', ...excluded.map(c => `- ${c} (committed while ${ctx.sprint} was paused)`), ''] : []),
    '## Acceptance', '', ...(ac.length ? ac.map(a => `- ${a.id}: ${a.text}`) : ['- (none found — that alone is a finding)']), '',
    '## Changes (base → current tree)', '', '```', diff.stat, '```', '', ...diff.names.slice(0, 200).map(n => `- ${n}`), '',
    '## Evidence on this tree', '', ...(valid.length ? valid.map(r => `- ${r.id} ${r.kind} exit ${r.exit} covers ${(r.covers || []).join(',') || '—'}: ${r.command}`) : ['- none yet (H2 will refuse ship)']), '',
    ...(claims.length ? ['## Transcribed claims (verify, do not trust)', '', ...claims, ''] : []),
    '## Dimensions', '', ...DIMENSIONS.map(d => `- ${d}`), '',
    '## Output contract', '', 'Follow the reviewer contract (agents/reviewer.md): findings lines `- [P0|P1|P2|P3] <file>:<line> or <evidence|packet|design>:<id|—> — <text>`, then exactly one line `VERDICT: PASS|CONCERNS|REWORK|FAIL`. No run id, no timestamps, no frontmatter.', '',
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
  if (fence) throw refuse('unterminated code fence in reviewer output', null, SAMPLE);
  const verdicts = [];
  const findings = [];
  for (const line of lines) {
    if (/^[\s>*_#`~<!-]*verdict\b/i.test(line)) { // a line that *opens* with VERDICT (any markup/case); prose mentions are fine
      const m = line.match(/^VERDICT: (PASS|CONCERNS|REWORK|FAIL)$/);
      if (!m) throw refuse(`malformed verdict line: "${line.trim().slice(0, 80)}" (must be exactly \`VERDICT: PASS|CONCERNS|REWORK|FAIL\`)`, null, SAMPLE);
      verdicts.push(m[1]);
    }
    if (/[[(]\s*p\d+\s*[\])]/i.test(line)) { // anything tag-like must be an exact [P0]–[P3] finding
      const m = line.match(/^- \[(P[0-3])\] (\S.*?) (?:—|–|--) (\S.*)$/);
      if (!m || (/^(?:evidence|packet|design):/.test(m[2]) && !/^(?:evidence|packet|design):(?:[^\s:]+|—)$/.test(m[2]))) throw refuse(`malformed finding line: "${line.trim().slice(0, 80)}" (must be \`- [Pn] <file>:<line> or <evidence|packet|design>:<id|—> — <text>\`)`, null, SAMPLE);
      findings.push({ sev: m[1], loc: m[2], text: m[3].trim() });
    }
  }
  if (verdicts.length !== 1) throw refuse(`reviewer output must hold exactly one \`VERDICT: PASS|CONCERNS|REWORK|FAIL\` line (found ${verdicts.length})`, null, SAMPLE);
  if (verdicts[0] === 'PASS' && findings.some(x => x.sev === 'P0' || x.sev === 'P1')) throw refuse('VERDICT: PASS with P0/P1 findings is contradictory (P0/P1 need REWORK or FAIL; a PASS carries P2/P3 only)', null, SAMPLE);
  return { verdict: verdicts[0], findings };
}

/** sha of the acceptance lines: a review covers these ACs; adding or changing one makes it stale. */
function acSha(designText) {
  return sha(JSON.stringify(h1.criteria(designText)));
}

function accept(argv, io) {
  const { flags: f } = flags(argv, { run: 'str', file: 'str', 'reviewer-agent': 'str', family: 'str', platform: 'str' });
  let ctx;
  try { ctx = requireCtx(io); } catch (error) { throw Object.assign(error, { next: 'athena init' }); }
  if (!ctx.sprintDir) throw refuse('no sprint in flight', 'athena status');
  const run = resolveRun(ctx, f.run || 'latest');
  const saved = JSON.parse(fs.readFileSync(path.join(runsDir(ctx), run, 'files.json'), 'utf8'));
  if (saved.sprint !== ctx.sprint) throw refuse(`run ${run} belongs to sprint ${saved.sprint}, not ${ctx.sprint}`, PREPARE);
  if (!f.file && process.stdin.isTTY) throw refuse('give the reviewer output with --file <path> (or pipe it on stdin)', acceptCmd(run));
  const packetPath = path.join(runsDir(ctx), run, 'packet.md');
  const again = `${acceptCmd(run)}   # after the reviewer has reviewed ${path.relative(io.cwd, packetPath)}`;
  if (f.file && !fs.existsSync(path.resolve(io.cwd, f.file))) throw refuse(`--file ${f.file} not found`, acceptCmd(run));
  if (f.file && fs.statSync(path.resolve(io.cwd, f.file)).mtimeMs < fs.statSync(packetPath).mtimeMs) {
    throw refuse(`${f.file} is older than the packet of run ${run}; it cannot be a review of it`, again);
  }
  const text = f.file ? fs.readFileSync(path.resolve(io.cwd, f.file), 'utf8') : fs.readFileSync(0, 'utf8');
  let parsed;
  try { parsed = parseOutput(text); } catch (error) {
    // The reviewer re-emits; the main agent does not rewrite its output (G-007).
    if (error instanceof UsageError) error.next = `${acceptCmd(run)}   # after the reviewer re-emits its output in the format above`;
    throw error;
  }
  // replay guard: one reviewer output is accepted for one run only (review S3 P1)
  const outputSha = sha(text);
  const ledger = path.join(runsDir(ctx), 'accepted.jsonl');
  const used = (() => { try { return fs.readFileSync(ledger, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)); } catch (_) { return []; } })();
  const reuse = used.find(u => u.output_sha === outputSha && u.run !== run);
  if (reuse) throw refuse(`this reviewer output was already accepted for run ${reuse.run}; a new run needs a new review`, again);
  const ignore = reviewIgnore(ctx);
  const tree = treeSha(ctx.root, ignore);
  if (tree !== saved.tree_sha || JSON.stringify(ignore) !== JSON.stringify(saved.ignore)) {
    const now = treeFiles(ctx.root, tree);
    const lines = [];
    for (const file of [...new Set([...Object.keys(saved.files), ...Object.keys(now)])].sort()) {
      if (saved.files[file] !== now[file]) lines.push(`  ${file}: expected ${saved.files[file] ? saved.files[file].slice(0, 12) : '(absent)'} actual ${now[file] ? now[file].slice(0, 12) : '(absent)'}`);
    }
    if (JSON.stringify(ignore) !== JSON.stringify(saved.ignore)) lines.push(`  review_ignore: expected ${JSON.stringify(saved.ignore)} actual ${JSON.stringify(ignore)}`);
    io.stderr.write(`athena review accept: source changed since prepare (run ${run}); the review covers the old tree:\n${lines.slice(0, 50).join('\n')}\nrun \`athena review prepare\` again and re-review.\nnext: ${PREPARE}\n`);
    return 4;
  }
  const packet = fs.readFileSync(packetPath, 'utf8');
  const design = fs.readFileSync(path.join(ctx.sprintDir, 'design.md'), 'utf8');
  if (saved.ac_sha && saved.ac_sha !== acSha(design)) {
    io.stderr.write(`athena review accept: design acceptance lines changed since prepare (run ${run}); prepare again so the reviewer sees them\nnext: ${PREPARE}\n`);
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
  if (parsed.verdict === 'PASS') return 0;
  io.stderr.write(`next: athena review show   # resolve each finding, re-run evidence (athena run --rebind), then ${PREPARE}\n`);
  return 3;
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
    if (error instanceof UsageError) {
      const next = error.next || (sub === 'accept' ? acceptCmd('latest') : null);
      io.stderr.write(`athena review ${sub}: ${error.message}\n${error.sample ? `expected lines:\n${error.sample}\n` : ''}${next ? `next: ${next}\n` : ''}`);
      return 2;
    }
    // Unexpected failure (unreadable run files, …): cli.cjs prints the message and exits 2.
    if (sub === 'accept') error.message += `\nnext: ${PREPARE}`;
    throw error;
  }
}

module.exports = { main, parseOutput, acSha };
