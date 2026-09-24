'use strict';
// H1 design-first (design §5.3): an implementation write (inside the repository, outside
// .ai_state/) while a routed sprint is in plan/design/impl needs a design.md carrying at
// least one non-placeholder acceptance line.
const fs = require('fs');
const path = require('path');
const { inside, PATHS } = require('../lib/context.cjs');

const DESIGN_PATHS = new Set(['Bugfix', 'Quick', 'Feature', 'Refactor', 'System']);
const STAGES = new Set(['plan', 'design', 'impl']);
const PLACEHOLDER_PREFIXES = ['todo', 'tbd', 'fixme', 'wip', 'placeholder', '待定', '待补', '占位', '暂定', '...', '…'];
const PLACEHOLDER_PHRASES = ['works correctly', 'works as expected', '功能正常', '正常工作', 'n/a'];
const LINE = /^\s*[-*]\s+(?:\[[ xX]\]\s+)?\**AC(\d+)\**\s*[:：]\s*(.*)$/;
const LEGAL = '合法形态：行首 `- AC1: <可观测结果>`（或 `* AC1:`、`- [ ] AC1:`、表格行 `| AC1 | <结果> |`）；围栏内示例、TODO/待定/「功能正常」类占位不算';

function placeholder(text) {
  const t = String(text).trim().toLowerCase().replace(/[.。!！;；,，]+$/, '').trim();
  if (!t) return true;
  return PLACEHOLDER_PREFIXES.some(p => t.startsWith(p)) || PLACEHOLDER_PHRASES.some(p => t === p || t.includes(p));
}

/** Acceptance criteria of a design: [{id, text}] outside code fences. */
function criteria(text) {
  const out = [];
  let fence = false;
  for (const raw of String(text || '').split(/\r?\n/)) {
    if (/^\s{0,3}(```|~~~)/.test(raw)) { fence = !fence; continue; }
    if (fence) continue;
    const m = raw.match(LINE);
    if (m && !placeholder(m[2])) { out.push({ id: `AC${m[1]}`, text: m[2].trim() }); continue; }
    const cells = raw.trim().startsWith('|') ? raw.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim().replace(/^[*`]+|[*`]+$/g, '')) : [];
    if (cells.length > 1 && /^AC\d+$/i.test(cells[0]) && !placeholder(cells.slice(1).join(' '))) {
      out.push({ id: cells[0].toUpperCase(), text: cells.slice(1).join(' | ') });
    }
  }
  return out;
}

/** Write targets that count as implementation: inside a project root, not under its .ai_state. */
function implementationTargets(ev, ctx) {
  const roots = [...new Set([ctx.root, ctx.mainRoot].filter(Boolean))];
  if (!ev.paths || !ev.paths.length) return null; // unknown target → treat as implementation
  return ev.paths.filter(file => roots.some(root => inside(file, root) && !inside(file, path.join(root, '.ai_state'))));
}

function check(ev, ctx) {
  if (!ctx || (!ctx.invalid && !STAGES.has(ctx.stage))) return null;
  const targets = implementationTargets(ev, ctx);
  if (targets && !targets.length) return null;
  if (ctx.invalid) return { rule: 'H1', reason: `H1 design-first: project state unknown (${ctx.invalid}); fix .ai_state/_index.md (writes there are allowed)` };
  if (!PATHS.has(ctx.path)) return { rule: 'H1', reason: `H1 design-first: _index path "${ctx.path}" is not a known path while stage=${ctx.stage}` };
  if (!DESIGN_PATHS.has(ctx.path)) return null; // Hotfix
  if (!ctx.sprintDir) return { rule: 'H1', reason: `H1 design-first: stage=${ctx.stage} but no valid sprint slug in _index ("${ctx.rawSprint}")` };
  const design = path.join(ctx.sprintDir, 'design.md');
  let text;
  try { text = fs.readFileSync(design, 'utf8'); } catch (_) {
    return { rule: 'H1', reason: `H1 design-first: ${path.relative(ctx.mainRoot, design)} missing; write the design (with - ACn: lines) before implementation` };
  }
  if (!criteria(text).length) {
    return { rule: 'H1', reason: `H1 design-first: ${path.relative(ctx.mainRoot, design)} has no acceptance line. ${LEGAL}` };
  }
  return null;
}

module.exports = { check, criteria, placeholder, implementationTargets, LEGAL };
