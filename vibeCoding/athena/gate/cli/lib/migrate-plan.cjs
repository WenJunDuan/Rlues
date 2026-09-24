'use strict';
// Plan for `athena migrate --to 10.1` (design §11.3, ai-state-v2 §7). Pure: reads, never writes.
// Every action is {kind, from, to, note}; paths are relative to .ai_state.
const fs = require('fs');
const path = require('path');
const frontmatter = require('../../lib/frontmatter.cjs');
const state = require('./state.cjs');

const V2_KEEP = ['path', 'stage', 'next_action', 'parallel_writers', 'exemptions', 'flags'];
const PROBE = ['platform_features', 'tools_available', 'cc_version', 'cx_version', 'ag_callable', 'platforms_enabled'];
const REPORTISH = /(report|acceptance|验收|audit|复盘|handoff|postmortem|review)/i;

const ls = (dir) => { try { return fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return []; } };
const monthOf = (slug, fallback) => (slug.match(/^(\d{4}-\d{2})-\d{2}/) || [])[1] || fallback;

function indexPlan(aiState) {
  const text = fs.readFileSync(path.join(aiState, '_index.md'), 'utf8');
  const fm = frontmatter.parse(text);
  if (String(fm.schema) === 'athena-state/2') return { already: true };
  const v2 = {};
  for (const key of V2_KEEP) if (key in fm) v2[key] = fm[key];
  v2.sprint = fm.sprint !== undefined ? fm.sprint : (fm.current_sprint_slug || '');
  v2.roadmap = fm.roadmap !== undefined ? fm.roadmap : (fm.current_roadmap_slug || '');
  const history = Array.isArray(fm.route_history) ? fm.route_history : [];
  v2.route = history.slice(0, 3).map(r => String(r).slice(0, 160));
  const probe = {};
  for (const key of PROBE) if (key in fm) probe[key] = fm[key];
  const notes = [];
  for (const key of ['skip_polish', 'skip_runtime_verify', 'skip_architecture_check']) {
    if (fm[key] === true) notes.push(`${key}: true dropped — re-declare as an exemption {key: ${key}, until, reason} if still needed`);
  }
  const dropped = Object.keys(fm).filter(k => !V2_KEEP.includes(k) && !PROBE.includes(k)
    && !['current_sprint_slug', 'current_roadmap_slug', 'route_history', 'sprint', 'roadmap', 'version', 'schema'].includes(k));
  return { already: false, v2, probe, dropped, notes, bytes: Buffer.byteLength(text) };
}

function moves(aiState, current = '') {
  const out = [];
  const add = (kind, from, to, note = '') => out.push({ kind, from, to, note });
  for (const e of ls(path.join(aiState, 'requirements'))) add('move', `requirements/${e.name}`, `docs/requirements/${e.name}`);
  for (const e of ls(path.join(aiState, 'docs'))) {
    if (['requirements', 'research', 'reports'].includes(e.name) || /^readme(\.md)?$/i.test(e.name)) continue;
    if (e.name === 'archive') { add('move', 'docs/archive', 'archive/docs'); continue; }
    add('move', `docs/${e.name}`, `docs/${REPORTISH.test(e.name) ? 'reports' : 'research'}/${e.name}`);
  }
  const lessons = [];
  for (const e of ls(path.join(aiState, 'compound'))) {
    const kind = (e.name.match(/^\d{4}-\d{2}-\d{2}-(decision|learning|trick|explore)-/) || [])[1] || '';
    if (kind === 'decision') add('move', `compound/${e.name}`, `decisions/${e.name}`);
    else if (kind === 'explore') add('move', `compound/${e.name}`, `docs/research/${e.name}`);
    else { add('move', `compound/${e.name}`, `archive/compound/${e.name}`); if (kind === 'learning' || kind === 'trick') lessons.push(`compound/${e.name}`); }
  }
  const items = state.allItems(aiState);
  const shipped = new Set(items.filter(it => state.DONE.has(String(it.data.status))).map(it => String(it.data.sprint || it.data.sprint_slug || '')));
  // v1 sprints without an item (Quick/Hotfix…): a PASS review or a recorded ship counts as shipped.
  const passed = (slug) => {
    const dir = path.join(aiState, 'sprints', slug);
    try { if (JSON.parse(fs.readFileSync(path.join(dir, 'review.json'), 'utf8')).verdict === 'PASS') return true; } catch (_) { /* v1 */ }
    const reviews = ls(path.join(dir, 'reviews')).map(e => { try { return fs.readFileSync(path.join(dir, 'reviews', e.name), 'utf8'); } catch (_) { return ''; } }).join('\n');
    const log = ['session-log.md', 'log.md'].map(n => { try { return fs.readFileSync(path.join(dir, n), 'utf8'); } catch (_) { return ''; } }).join('\n');
    // only the CLI's own ship line or an explicit "shipped:" record — not prose like "not shipped yet"
    return /VERDICT:\s*PASS|结论[:：]\s*\**PASS/.test(reviews) || /^- \d{4}-\d{2}-\d{2}\s+shipped \(|^\s*shipped:\s*\S/m.test(log);
  };
  for (const e of ls(path.join(aiState, 'sprints'))) {
    if (!e.isDirectory() || e.name === 'archive') continue;
    if (e.name === current) { add('keep', `sprints/${e.name}`, `sprints/${e.name}`, 'current sprint'); continue; }
    if (shipped.has(e.name)) add('move', `sprints/${e.name}`, `archive/sprints/${monthOf(e.name, 'undated')}/${e.name}`, 'shipped (items.yaml done)');
    else if (passed(e.name)) add('move', `sprints/${e.name}`, `archive/sprints/${monthOf(e.name, 'undated')}/${e.name}`, 'shipped (PASS review / ship recorded)');
    else add('pause', `sprints/${e.name}`, `sprints/${e.name}`, 'not shipped → design status: paused (resume_when to be written by a human)');
  }
  const walkArchive = (rel) => {
    for (const e of ls(path.join(aiState, rel))) {
      if (!e.isDirectory()) continue;
      if (/^\d{4}$/.test(e.name)) walkArchive(`${rel}/${e.name}`);
      else add('move', `${rel}/${e.name}`, `archive/sprints/${monthOf(e.name, 'undated')}/${e.name}`, 'cold');
    }
  };
  walkArchive('sprints/archive');
  if (fs.existsSync(path.join(aiState, '.snapshots'))) add('untrack', '.snapshots', '.runtime/snapshots', 'git rm --cached; files kept under .runtime');
  for (const name of ['index-overflow.md', 'harness-patches.md']) {
    if (fs.existsSync(path.join(aiState, name))) add('move', name, `archive/legacy/${name}`, 'retired in 10.1');
  }
  return { actions: out, lessons };
}

/** issues.md draft rows from proposals.md / vm-pending.md (human confirms before replacing). */
function issueDraft(aiState) {
  const rows = [];
  const read = (name) => { try { return fs.readFileSync(path.join(aiState, name), 'utf8'); } catch (_) { return null; } };
  const proposals = read('proposals.md');
  if (proposals) {
    for (const [i, line] of proposals.split('\n').entries()) {
      const m = line.match(/^#{2,3}\s+(.+)$/);
      if (m && /^(?:P\d+|[A-Z]{1,4}-?\d+)\b|·/.test(m[1].trim())) rows.push({ type: 'debt', text: m[1].trim(), found: `proposals.md:${i + 1}` });
    }
  }
  const vm = read('vm-pending.md');
  if (vm) {
    for (const [i, line] of vm.split('\n').entries()) {
      const bullet = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/);
      let text = bullet ? bullet[1].trim() : '';
      if (!bullet && /^\|/.test(line) && !/^\|[\s|:-]*\|?\s*$/.test(line)) {
        const cells = line.replace(/^\||\|\s*$/g, '').split('|').map(c => c.trim());
        text = cells.reduce((a, b) => (b.length > a.length ? b : a), '');
        if (i > 0 && /^\|[\s|:-]+$/.test(vm.split('\n')[i + 1] || '')) text = ''; // header row
      }
      if (text) rows.push({ type: 'env', text, found: `vm-pending.md:${i + 1}` });
    }
  }
  return rows;
}

function plan(aiState) {
  const index = indexPlan(aiState);
  const current = index.already ? String(frontmatter.parse(fs.readFileSync(path.join(aiState, '_index.md'), 'utf8')).sprint || '') : String(index.v2.sprint || '');
  const { actions, lessons } = moves(aiState, current);
  return { index, actions, lessons, issues: issueDraft(aiState) };
}

module.exports = { plan, indexPlan, PROBE };
