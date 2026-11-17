'use strict';
// athena doctor --context: bytes and estimated tokens each layer puts into every session, and which
// project rules are path-scoped. Estimate: CJK 1 char ≈ 1 token, other text 3.6 chars ≈ 1 token
// (±30%); budgets are checked in bytes (docs/research/2026-11-17-athena-progressive-disclosure.md).
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const CJK = /[　-〿぀-ヿ㐀-䶿一-鿿가-힯＀-￯]/gu;
const PLATFORMS = {
  cc: { constitution: '.claude/CLAUDE.md', rules: '.claude/rules', skills: '.claude/skills', agents: '.claude/agents', agentExt: '.md' },
  cx: { constitution: '.codex/AGENTS.md', rules: null, skills: '.agents/skills', agents: '.codex/agents', agentExt: '.toml' },
};

function tokens(text) {
  const cjk = (text.match(CJK) || []).length;
  return Math.round(cjk + (Array.from(text).length - cjk) / 3.6);
}

const read = (file) => { try { return fs.readFileSync(file, 'utf8'); } catch (_) { return null; } };
const entries = (dir) => { try { return fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1)); } catch (_) { return []; } };

function mdFiles(dir) {
  const out = [];
  for (const e of entries(dir)) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...mdFiles(full));
    else if (e.isFile() && e.name.endsWith('.md')) out.push(full);
  }
  return out;
}

function frontmatter(text) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---/.exec(text || '');
  return m ? m[1].split(/\r?\n/) : [];
}

/** `paths:` globs in a rule's frontmatter; [] = no paths = loaded every session. */
function rulePaths(text) {
  const out = [];
  let inPaths = false;
  for (const line of frontmatter(text)) {
    if (/^paths:\s*$/.test(line)) { inPaths = true; continue; }
    if (inPaths && /^\s+-\s*\S/.test(line)) { out.push(line.replace(/^\s+-\s*/, '').trim().replace(/^["']|["']$/g, '')); continue; }
    inPaths = false;
  }
  return out;
}

/** name + description of each skill / agent: what the platform lists every session. */
function listing(dir, kind) {
  const items = [];
  if (kind === 'skill') {
    for (const e of entries(dir)) {
      const text = e.isDirectory() ? read(path.join(dir, e.name, 'SKILL.md')) : null;
      if (text !== null) items.push(frontmatter(text).filter(l => /^(name|description):/.test(l)).join('\n'));
    }
  } else {
    for (const e of entries(dir)) {
      const text = e.isFile() && /\.(md|toml)$/.test(e.name) ? read(path.join(dir, e.name)) : null;
      if (text === null) continue;
      const lines = e.name.endsWith('.toml') ? text.split(/\r?\n/) : frontmatter(text);
      items.push(lines.filter(l => /^(name|description)\s*[:=]/.test(l)).join('\n'));
    }
  }
  return items;
}

function layer(name, texts, detail) {
  const joined = texts.join('\n');
  return { name, bytes: texts.reduce((n, t) => n + Buffer.byteLength(t), 0), tokens: tokens(joined), detail };
}

/** `**`, `*`, `?`, `{a,b}` glob → RegExp over repo-relative posix paths. */
function globRe(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === '*' && glob[i + 1] === '*') { re += glob[i + 2] === '/' ? '(?:.*/)?' : '.*'; i += glob[i + 2] === '/' ? 2 : 1; }
    else if (c === '*') re += '[^/]*';
    else if (c === '?') re += '[^/]';
    else if (c === '{') { const end = glob.indexOf('}', i); re += `(?:${glob.slice(i + 1, end).split(',').map(s => s.replace(/[.+^$()|[\]\\]/g, '\\$&')).join('|')})`; i = end; }
    else re += c.replace(/[.+^$()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${re}$`);
}

function report(home, cwd, platform) {
  const spec = PLATFORMS[platform];
  const top = spawnSync('git', ['rev-parse', '--show-toplevel'], { cwd, encoding: 'utf8' });
  const root = top.status === 0 ? top.stdout.trim() : cwd;
  const layers = [];
  const constitution = read(path.join(home, spec.constitution));
  layers.push(layer('constitution', constitution === null ? [] : [constitution], `~/${spec.constitution}${constitution === null ? ' (missing)' : ''}`));
  if (spec.rules) {
    const resident = mdFiles(path.join(home, spec.rules)).filter(f => !rulePaths(read(f)).length);
    layers.push(layer('rules without paths', resident.map(read), resident.map(f => path.relative(path.join(home, spec.rules), f)).join(', ') || '—'));
  } else layers.push(layer('rules without paths', [], 'none resident (read on demand from the index)'));
  const skills = listing(path.join(home, spec.skills), 'skill');
  layers.push(layer('skill list', skills, `${skills.length} skills in ~/${spec.skills}`));
  const agents = listing(path.join(home, spec.agents), 'agent');
  layers.push(layer('agent descriptions', agents, `${agents.length} agents in ~/${spec.agents}`));
  const projectRules = platform === 'cc' ? mdFiles(path.join(root, '.claude/rules')) : [];
  const instructions = (platform === 'cc' ? ['CLAUDE.md', '.claude/CLAUDE.md'] : ['AGENTS.md']).filter(f => read(path.join(root, f)) !== null);
  const residentRules = projectRules.filter(f => !rulePaths(read(f)).length);
  layers.push(layer('project rules', [...instructions.map(f => read(path.join(root, f))), ...residentRules.map(read)],
    [...instructions, ...residentRules.map(f => path.relative(root, f))].join(', ') || '—'));
  const tracked = spawnSync('git', ['ls-files'], { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  const files = tracked.status === 0 ? tracked.stdout.split('\n').filter(Boolean) : [];
  const coverage = projectRules.map(f => {
    const globs = rulePaths(read(f));
    const res = globs.map(globRe);
    return { rule: path.relative(root, f), bytes: fs.statSync(f).size, globs, matches: globs.length ? files.filter(x => res.some(r => r.test(x))).length : null };
  });
  return { platform, root, layers, coverage };
}

function format(r) {
  const out = [`context ${r.platform} (bytes; tokens ≈ CJK 1/char + other 1 per 3.6 chars, ±30%)`];
  for (const l of r.layers) out.push(`  ${l.name.padEnd(20)} ${String(l.bytes).padStart(7)} B  ≈${String(l.tokens).padStart(6)} tok  ${l.detail}`);
  const total = r.layers.reduce((a, l) => ({ bytes: a.bytes + l.bytes, tokens: a.tokens + l.tokens }), { bytes: 0, tokens: 0 });
  out.push(`  ${'resident total'.padEnd(20)} ${String(total.bytes).padStart(7)} B  ≈${String(total.tokens).padStart(6)} tok`);
  out.push(`project rules paths coverage (${r.root}):`);
  if (!r.coverage.length) out.push('  — no .claude/rules');
  for (const c of r.coverage) {
    out.push(c.globs.length ? `  ${c.rule}  ${c.bytes} B  paths ${c.globs.join(', ')} → ${c.matches} tracked file(s)`
      : `  ${c.rule}  ${c.bytes} B  no paths (every session)`);
  }
  return `${out.join('\n')}\n`;
}

module.exports = { report, format, tokens, rulePaths, globRe, PLATFORMS };
