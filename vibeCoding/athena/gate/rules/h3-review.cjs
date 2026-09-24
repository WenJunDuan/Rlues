'use strict';
// H3 independent review (design §5.3, §6): review.json PASS bound to the current source tree.
const fs = require('fs');
const path = require('path');

const REVIEW_PATHS = new Set(['Bugfix', 'Feature', 'Refactor', 'System']);
const FAMILY = { cc: 'anthropic', cx: 'openai', grok: 'xai' };

function readReview(ctx) {
  const file = path.join(ctx.sprintDir, 'review.json');
  try { return { file, data: JSON.parse(fs.readFileSync(file, 'utf8')) }; }
  catch (error) { return { file, error: error.code === 'ENOENT' ? 'missing' : `unreadable (${error.message})` }; }
}

function check(ev, ctx, tree, ignore = []) {
  if (!REVIEW_PATHS.has(ctx.path)) return null;
  if (!ctx.sprintDir) return { rule: 'H3', reason: 'H3 review: stage=ship without a valid sprint slug in _index' };
  const { file, data, error } = readReview(ctx);
  const rel = path.relative(ctx.mainRoot, file);
  if (error) return { rule: 'H3', reason: `H3 review: ${rel} ${error}; run \`athena review prepare\`, dispatch a reviewer, then \`athena review accept\`` };
  if (data.verdict !== 'PASS') return { rule: 'H3', reason: `H3 review: verdict is ${data.verdict || 'absent'}; fix the findings and review again` };
  if (!tree || data.tree_sha !== tree || JSON.stringify(data.ignore || []) !== JSON.stringify(ignore)) {
    return { rule: 'H3', reason: `H3 review: reviewed tree ${String(data.tree_sha).slice(0, 12)} ≠ current tree ${String(tree).slice(0, 12)}; source changed after review — \`athena review prepare\` a new run` };
  }
  if (ctx.flags.cross_family_review) {
    const author = FAMILY[ev.platform];
    const reviewer = data.reviewer && data.reviewer.family;
    if (author && reviewer === author) return { rule: 'H3', reason: `H3 review: cross_family_review is on and reviewer family ${reviewer} equals the author's` };
  }
  return null;
}

module.exports = { check, readReview, REVIEW_PATHS, FAMILY };
