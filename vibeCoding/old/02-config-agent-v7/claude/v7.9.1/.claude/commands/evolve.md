---
name: evolve
description: Cluster related instincts into a skill
allowed-tools: ["Read", "Write"]
---

# evolve - Evolve Instincts into Skills

## Usage

```bash
evolve                           # Interactive evolution
evolve --tags=authentication     # Target specific cluster
evolve --preview                 # Preview without creating
evolve --min-instincts=3         # Minimum cluster size
```

## Evolution Process

### 1. Cluster Detection

```
Analyzing instincts...

Found clusters:

🔄 "authentication" (5 instincts, avg 0.85)
   - JWT token refresh [0.92]
   - Session management [0.88]
   - OAuth flow handling [0.82]
   - Password hashing [0.85]
   - 2FA implementation [0.78]

🔄 "nextjs" (8 instincts, avg 0.79)
   - App router patterns [0.85]
   - Server actions [0.82]
   - Middleware auth [0.78]
   ...

Select cluster to evolve: [1/2/skip]
```

### 2. Skill Generation

```
Generating skill from "authentication" cluster...

Draft SKILL.md:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
---
name: authentication-patterns
description: |
  Authentication patterns learned from project development.
  Covers JWT, sessions, OAuth, and 2FA implementations.
---

# Authentication Patterns

## JWT Token Management

### Refresh Flow
[Merged from: JWT token refresh instinct]
...

## Session Management
[Merged from: Session management instinct]
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions:
  1. Install skill to .claude/skills/
  2. Edit before installing
  3. Discard and keep instincts
  4. Save draft for later

Select: [1/2/3/4]
```

### 3. Skill Installation

```
Installing skill: authentication-patterns

✅ Created: .claude/skills/authentication-patterns/SKILL.md
✅ Updated: orchestrator.yaml
✅ Marked 5 instincts as "evolved"

Evolved instincts will be:
  - Hidden from active matching
  - Preserved in archive
  - Linked to new skill
```

## Cluster Criteria

Instincts cluster when:
- Same primary tag (≥3 instincts)
- Similar solution patterns
- Combined confidence > 0.7
- Not already evolved

## Manual Clustering

```bash
# Specify instincts to merge
evolve --instincts=inst_abc,inst_def,inst_ghi

# Or by ID pattern
evolve --pattern="inst_auth*"
```

## Best Practices

1. **Wait for Maturity** - Let instincts accumulate confidence
2. **Review Before Install** - Edit generated skill
3. **Test After Evolution** - Verify skill works
4. **Prune Duplicates** - Remove redundant instincts
5. **Document Lineage** - Keep link to source instincts
