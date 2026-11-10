'use strict';
// Docs evidence (`athena run -- grep -F -q '<text>' <file>.md`): a read-only assertion on markdown in
// the source tree, or in .ai_state/docs/ (G-037).
const fs = require('fs');
const path = require('path');
const context = require('../../lib/context.cjs');
const words = require('../../lib/shell-words.cjs');
const { treeFiles } = require('../../lib/tree-sha.cjs');

/** The governing .ai_state/docs and the checked-out copy in this worktree. */
function stateDocs(ctx) {
  return [...new Set([path.join(ctx.aiState, 'docs'), path.join(ctx.root, '.ai_state', 'docs')])];
}

// Narrow read-only assertion grammar; all expanded targets must belong to the source tree or .ai_state/docs/.
function docsAssertion(command, cwd, ctx, root, tree) {
  const segments = words.commandSegments(command);
  if (segments.length !== 1 || segments[0].after || /[$`<>]/.test(command)) return false;
  const tokens = segments[0].words.map(t => t.value);
  if (!['grep', 'rg'].includes(tokens.shift())) return false;
  let fixed = false, pattern = null, endOptions = false;
  const files = [];
  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (!endOptions && token === '--') { endOptions = true; continue; }
    if (!endOptions && ['-e', '--regexp'].includes(token)) { if (pattern !== null || !tokens[i + 1]) return false; pattern = tokens[++i]; continue; }
    if (!endOptions && token.startsWith('-')) {
      if (/^-[Fqlni]+$/.test(token)) { fixed ||= token.includes('F'); continue; }
      if (['--fixed-strings', '--quiet', '--files-with-matches', '--line-number', '--ignore-case'].includes(token)) { fixed ||= token === '--fixed-strings'; continue; }
      return false;
    }
    if (pattern === null) pattern = token;
    else files.push(token);
  }
  if (!fixed || !pattern || !files.length) return false;
  const source = new Set(Object.keys(treeFiles(root, tree)));
  return files.every(file => {
    const abs = path.resolve(cwd, file);
    let targets = [abs];
    if (file.includes('*')) {
      if (!/^\*\.md$/.test(path.basename(file)) || path.dirname(file).includes('*')) return false;
      try { targets = fs.readdirSync(path.dirname(abs)).filter(n => n.endsWith('.md')).map(n => path.join(path.dirname(abs), n)); } catch (_) { return false; }
    }
    return targets.length > 0 && targets.every(target => {
      try {
        if (!target.endsWith('.md') || !fs.statSync(target).isFile()) return false;
        // G-037: research notes under .ai_state/docs/ are outside the source tree but are docs evidence too.
        if (stateDocs(ctx).some(dir => context.inside(target, dir))) return true;
        return context.inside(target, root) && source.has(path.relative(root, target))
          && source.has(path.relative(root, fs.realpathSync(target)));
      } catch (_) { return false; }
    });
  });
}

module.exports = { docsAssertion };
