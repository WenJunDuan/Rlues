---
name: instinct-import
description: Import instincts from team members or other projects
allowed-tools: ["Read", "Write"]
---

# instinct-import - Import Instincts

## Usage

```bash
instinct-import <file>                    # Import from file
instinct-import team-patterns.json        # Specific file
instinct-import --namespace=team <file>   # Add namespace
instinct-import --preview <file>          # Preview without saving
```

## Behavior

Imported instincts:
- Start with 0.5 confidence (neutral)
- Keep original tags + source namespace
- Adjust confidence based on local use
- Don't overwrite existing identical patterns

## Import Preview

```bash
instinct-import --preview team-patterns.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Import Preview: team-patterns.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source: project-alpha
Exported: 2026-01-25
Instincts: 15

New (will import):
  + CORS handling pattern [react, api]
  + Prisma error handling [prisma, database]
  + JWT refresh flow [auth, jwt]

Duplicate (will skip):
  ~ React hydration fix (exists locally)

Conflict (needs review):
  ! Database connection pattern
    Local:  "Use connection pooling with pg-pool"
    Import: "Use Prisma connection limit"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed with import? [y/n/review conflicts]
```

## Namespace Usage

```bash
# Import with namespace
instinct-import --namespace=team-alpha patterns.json

# View namespaced instincts
instinct-status --namespace=team-alpha

# Namespaced instincts show source
✅ [team-alpha] CORS handling pattern
   Confidence: 0.65 | Uses: 3 (local)
```

## Conflict Resolution

When pattern exists locally:

```
Options:
  1. keep    - Keep local version
  2. replace - Use imported version  
  3. merge   - Combine solutions
  4. both    - Keep both as separate
```

## Workflow

```bash
# 1. Preview import
instinct-import --preview team-share.json

# 2. Import with namespace
instinct-import --namespace=team team-share.json

# 3. Use in sessions
# (instincts applied automatically)

# 4. Check local performance
instinct-status --namespace=team

# 5. Promote successful ones
# (confidence increases with use)
```
