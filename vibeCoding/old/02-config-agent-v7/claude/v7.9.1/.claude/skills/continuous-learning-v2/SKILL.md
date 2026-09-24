---
name: continuous-learning-v2
description: |
  Instinct-based learning system with confidence scoring. Automatically learns
  patterns from sessions and evolves them into skills. Supports import/export
  for team sharing.
context: fork
---

# Continuous Learning v2 - Instinct System

## Overview

Instincts are micro-patterns learned from coding sessions. Unlike full skills,
instincts are:
- **Lightweight** - Single pattern, minimal context
- **Confidence-scored** - Track success rate
- **Evolvable** - Cluster into skills when mature

## Instinct Structure

```json
{
  "id": "inst_abc123",
  "pattern": "When encountering CORS errors in Next.js API routes...",
  "solution": "Add headers object with Access-Control-Allow-* fields",
  "confidence": 0.85,
  "uses": 12,
  "successes": 10,
  "created": "2026-01-15T10:30:00Z",
  "lastUsed": "2026-01-28T14:20:00Z",
  "tags": ["nextjs", "api", "cors", "debugging"],
  "context": {
    "framework": "next.js",
    "version": "15.x",
    "category": "debugging"
  }
}
```

## Commands

### `/instinct-status`
View learned instincts with confidence scores:

```
📊 Instinct Status

Total: 47 instincts | Avg Confidence: 0.78

High Confidence (>0.8):
  ✅ CORS handling in Next.js API [0.92] - 15 uses
  ✅ Prisma transaction patterns [0.88] - 8 uses
  ✅ React useEffect cleanup [0.85] - 23 uses

Medium Confidence (0.5-0.8):
  ⚡ Supabase RLS policies [0.72] - 5 uses
  ⚡ Tailwind responsive patterns [0.68] - 7 uses

Low Confidence (<0.5):
  ❓ Edge function cold starts [0.45] - 2 uses
```

### `/instinct-export`
Export instincts for sharing:

```bash
# Export all instincts
/instinct-export

# Export by tag
/instinct-export --tags=nextjs,react

# Export high confidence only
/instinct-export --min-confidence=0.8
```

Output: `.ai_state/instincts/export-2026-01-28.json`

### `/instinct-import <file>`
Import instincts from team:

```bash
/instinct-import shared-instincts.json
```

Imported instincts start with 0.5 confidence and adjust based on local use.

### `/evolve`
Cluster related instincts into a skill:

```bash
# Interactive evolution
/evolve

# Target specific tags
/evolve --tags=authentication
```

## Learning Triggers

Instincts are captured when:

1. **Successful Debugging** - Problem → Solution pattern
2. **Pattern Recognition** - Repeated similar solutions
3. **User Confirmation** - Explicit "remember this" signals
4. **Code Review Feedback** - Accepted improvements

## Confidence Scoring

```
confidence = successes / uses * decay_factor

where:
  decay_factor = 0.95^(days_since_last_use / 30)
```

Confidence increases with successful uses, decreases with failures or time.

## Storage

```
.ai_state/instincts/
├── instincts.json      # Main instinct database
├── index.md            # Human-readable index
├── exports/            # Export history
│   └── export-*.json
└── evolved/            # Evolved skills
    └── skill-*.md
```

## Evolution Process

When instincts cluster around a topic:

```
1. Identify Related Instincts
   - Same tags (>3 instincts)
   - Similar patterns
   - High combined confidence

2. Generate Skill Draft
   - Merge patterns
   - Synthesize solutions
   - Create SKILL.md

3. User Review
   - Present draft
   - Cunzhi confirmation
   - Install or iterate

4. Deprecate Instincts
   - Mark as "evolved"
   - Link to new skill
```

## Integration

### With Experience Skill
```
Instincts → lightweight, auto-captured
Experience → heavyweight, manually curated

Workflow:
1. Instinct captured automatically
2. High-confidence instincts → candidate for experience
3. User confirms → promote to experience
```

### With /learn Command
```
/learn               # Capture to instincts (default)
/learn --experience  # Capture to experience (manual)
/learn --dry-run     # Preview without saving
```

## Quality Filters

Instincts must meet criteria:
- **Non-trivial** - Not basic language features
- **Reusable** - Applies to multiple contexts
- **Specific** - Clear trigger and solution
- **Tested** - At least one successful use

## Team Sharing Best Practices

```bash
# Export team-relevant instincts
/instinct-export --min-confidence=0.7 --tags=our-stack

# Import with namespace
/instinct-import team-patterns.json --namespace=team

# Review imported before trusting
/instinct-status --namespace=team
```
