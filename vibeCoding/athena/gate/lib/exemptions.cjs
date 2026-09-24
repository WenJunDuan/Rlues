'use strict';
// Exemptions (design §5.5): {key, until, reason[, by]} in _index frontmatter. Expired,
// unknown-key, reasonless or over-long (> 14 days ahead) entries are ignored. H2/H3 have no key.
const KEYS = new Set(['h4_worktree', 'skip_runtime_verify', 'skip_polish', 'skip_architecture_check', 'harness_target_outside_repo']);
const MAX_DAYS = 14;
const DAY = 24 * 60 * 60 * 1000;

/** End of the `until` day in UTC (a bare date is inclusive), or NaN. */
function untilMs(until) {
  const text = String(until || '').trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return Date.parse(`${text}T23:59:59.999Z`);
  return Date.parse(text);
}

/** Classify every declared exemption: {entry, status: active|expired|invalid, why}. */
function review(ctx, now = Date.now()) {
  return (ctx.exemptions || []).map(entry => {
    if (!entry || typeof entry !== 'object') return { entry, status: 'invalid', why: 'not a mapping' };
    if (!KEYS.has(entry.key)) return { entry, status: 'invalid', why: `unknown key ${entry.key}` };
    if (!String(entry.reason || '').trim()) return { entry, status: 'invalid', why: 'reason required' };
    const end = untilMs(entry.until);
    if (!Number.isFinite(end)) return { entry, status: 'invalid', why: 'until must be a date' };
    if (end < now) return { entry, status: 'expired', why: `expired ${entry.until}` };
    if (end - now > MAX_DAYS * DAY) return { entry, status: 'invalid', why: `until more than ${MAX_DAYS} days ahead` };
    return { entry, status: 'active', why: '', daysLeft: Math.floor((end - now) / DAY) };
  });
}

function active(ctx, key, now = Date.now()) {
  return review(ctx, now).find(item => item.status === 'active' && item.entry.key === key) || null;
}

module.exports = { review, active, KEYS, MAX_DAYS };
