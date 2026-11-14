'use strict';
// H2 evidence (design §5.3, §8): at ship, a provable PASS recorded against the current
// source tree. Stale (other tree), failing, unprovable or missing records do not count.
const evidence = require('../lib/evidence.cjs');

function check(ev, ctx, tree, ignore = []) {
  if (!ctx.sprint) return { rule: 'H2', reason: 'H2 evidence: stage=ship without a valid sprint slug in _index' };
  if (!tree) return { rule: 'H2', reason: 'H2 evidence: cannot compute the source tree sha (not a git work tree?)' };
  const hotfix = ctx.path === 'Hotfix';
  const rows = evidence.read(ctx);
  if (evidence.valid(ctx, tree, { anyProvableKind: hotfix, ignore }).length) {
    // G-021: a passing run elsewhere does not outweigh an AC whose latest check on this tree failed.
    const key = JSON.stringify(ignore);
    const latest = new Map();
    for (const row of rows) {
      if (row.tree_sha !== tree || JSON.stringify(row.ignore || []) !== key) continue;
      for (const ac of row.covers || []) latest.set(ac, row);
    }
    const failed = [...latest].filter(([, row]) => row.exit !== 0);
    if (!failed.length) return null;
    const list = failed.map(([ac, row]) => `${ac} (${row.id} exited ${row.exit})`).join(', ');
    return { rule: 'H2', reason: `H2 evidence: latest --covers check failed on this tree for ${list}. Fix it and re-run \`athena run --covers <AC> -- <cmd>\`.` };
  }
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
