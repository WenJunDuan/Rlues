---
name: learn
description: |
  Extract reusable patterns from the current session. Analyzes conversation
  for successful solutions, debugging approaches, and architectural decisions
  worth preserving. Deposits patterns to experience/learned/ for future use.
---

# /learn - Extract Session Patterns

## Usage

```bash
/learn                      # Extract all patterns
/learn --type=debugging     # Specific type
/learn --dry-run            # Preview only
/learn --name="my-pattern"  # Custom name
```

## Workflow

1. **Analyze Session** - Scan for problems solved, solutions implemented
2. **Identify Patterns** - Filter reusable, non-trivial patterns
3. **Confirm with User** - Present findings for approval
4. **Store Patterns** - Save to `.ai_state/experience/learned/`
5. **Update Index** - Add to experience index for future matching

## Pattern Template

```markdown
# Pattern: [Name]
Created: [Date]
Type: [code|debugging|architecture|workflow]

## Trigger
[When to use]

## Problem
[What was being solved]

## Solution
[Code/approach]

## Notes
[Gotchas, variations]
```

## Example

```
✅ Extracted 2 patterns:
1. nextjs-hydration-fix.md (code)
2. prisma-singleton.md (debugging)

Index updated: .ai_state/experience/index.md
```
