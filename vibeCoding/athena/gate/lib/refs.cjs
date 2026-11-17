'use strict';
// Where a blocked agent reads the rule behind each hard gate. Paths are skill-relative because the
// skills directory differs per platform (~/.claude/skills, ~/.agents/skills, the Pi / plugin roots).
// The hard constraints themselves are spelled out so they are visible at the block, not only in a skill.
const REFS = {
  H1: 'ref: skill pace references/gates.md',
  H2: 'Each check is one `athena run --covers ACn -- <cmd>` (a `sh -c "a && b"` wrapper is unprovable); ref: skill athena-session references/verify.md, skill pace references/gates.md',
  H3: 'From `athena review prepare` until accept the main tree takes no commit and no new untracked file; ref: skill athena-session references/merge-review.md, skill pace references/gates.md',
  H4: 'ref: skill pace references/execution.md',
  H5: 'ref: skill pace references/gates.md',
};

/** The verdict with the rule's reference appended to its reason (unchanged for an unknown rule). */
function withRef(verdict) {
  const ref = verdict && REFS[verdict.rule];
  return ref ? { ...verdict, reason: `${verdict.reason} — ${ref}` } : verdict;
}

module.exports = { REFS, withRef };
