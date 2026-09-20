---
schema_version: 1
sprint_slug: "2026-09-20-index-overflow-root-transaction"
mode: "design"
generated_from: "design.md"
source_design_sha256: "a5fa8c5905386787cfb2999c597fb02afa105f09f62416df16d74aa3042486e5"
---

# Review Packet

Derived from design.md. Review the contract and proposed boundary; do not edit files.

## Contract

| ID | Must hold | Anchor |
|---|---|---|
| AC1 | CC/CX always spill to root and never create sprint overflow | `_index-bounds.cjs`, `_index_bounds.py`, behavior tests |
| AC2 | Route/current-state/history/body pointers are project-relative and resolve to matching root headings | pointer methods and four branch tests |
| AC3 | Concurrent CC+CX bounds preserve both originals with unique headings; crash/raw/no-op semantics remain intact | new concurrent bounds regression plus existing StateBehavior regressions |
| AC4 | All shipped templates and architecture describe root overflow; Git continues tracking it | three templates, architecture, ignore assertion |

## Allowed write set

- `vibeCoding/claude/9.9.9/.claude/hooks/_index-bounds.cjs`
- `vibeCoding/codex/9.9.9/.codex/hooks/_index_bounds.py`
- `vibeCoding/claude/9.9.9/.claude/skills/pace/templates/_index.md`
- `vibeCoding/codex/9.9.9/.codex/skills/pace/templates/_index.md`
- `vibeCoding/pi-agent/plugin/skills/pace/templates/_index.md`
- `vibeCoding/scripts/tests/athena999/test_state_review.py`
- `.ai_state/architecture/athena-9.9.8.md` during polish
- current sprint evidence/review/state artifacts

## Attack list

1. Concurrent CC/CX root-level ID allocation collides, overwrites or loses an overflow section.
2. Pointer text changes while a route/status/body branch still emits the old bare pointer.
3. `readSlug/read_slug` or slug parameters survive as dead routing plumbing.
4. The no-op path rewrites the tracked root file on every hook execution.
5. CC and CX diverge on path or pointer format.
6. Tests pass by moving expectations while failing to assert the old sprint file is absent.
7. A template or architecture document continues teaching the obsolete sprint path.
8. `.gitignore` or packaging excludes the root overflow despite passing unit tests.
