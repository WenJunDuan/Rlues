'use strict';
// H2 evidence (design §5.3, §8): at ship, a provable PASS recorded against the current
// source tree. Stale (other tree), failing, unprovable or missing records do not count.
const evidence = require('../lib/evidence.cjs');

function check(ev, ctx, tree, ignore = []) {
  if (!ctx.sprint) return { rule: 'H2', reason: 'H2 evidence: stage=ship without a valid sprint slug in _index' };
  if (!tree) return { rule: 'H2', reason: 'H2 evidence: cannot compute the source tree sha (not a git work tree?)' };
  const hotfix = ctx.path === 'Hotfix';
  if (evidence.valid(ctx, tree, { anyProvableKind: hotfix, ignore }).length) return null;
  const rows = evidence.read(ctx);
  let why = 'no evidence recorded for this sprint';
  if (rows.length) {
    const last = rows[rows.length - 1];
    if (JSON.stringify(last.ignore || []) !== JSON.stringify(ignore)) why = `latest record ${last.id} was computed with a different review_ignore list`;
    else if (last.tree_sha !== tree) why = `latest record ${last.id} is for tree ${String(last.tree_sha).slice(0, 12)}, current tree is ${tree.slice(0, 12)} (source changed since)`;
    else if (last.exit !== 0) why = `latest record ${last.id} exited ${last.exit}`;
    else why = `latest record ${last.id} is not provable (${last.kind}${last.reason ? `, ${last.reason}` : ''})`;
  }
  return { rule: 'H2', reason: `H2 evidence: ${why}. Run the checks with \`athena run -- <test/typecheck/build command>\` on the final tree.` };
}

module.exports = { check };
