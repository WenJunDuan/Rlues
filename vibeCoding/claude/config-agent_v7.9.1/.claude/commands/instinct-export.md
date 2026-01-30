---
name: instinct-export
description: Export instincts for sharing with team members
allowed-tools: ["Read", "Write"]
---

# instinct-export - Export Instincts

## Usage

```bash
instinct-export                           # Export all
instinct-export --tags=react,nextjs       # Filter by tags
instinct-export --min-confidence=0.7      # High confidence only
instinct-export --output=team-patterns    # Custom filename
```

## Output

Creates file at `.ai_state/instincts/exports/export-{date}.json`

```json
{
  "version": "1.0",
  "exported": "2026-01-28T14:30:00Z",
  "source": "project-name",
  "filters": {
    "tags": ["react", "nextjs"],
    "minConfidence": 0.7
  },
  "instincts": [
    {
      "id": "inst_abc123",
      "pattern": "When encountering hydration mismatch...",
      "solution": "Use dynamic import with ssr: false",
      "confidence": 0.88,
      "uses": 12,
      "tags": ["react", "nextjs", "ssr", "hydration"]
    }
  ],
  "stats": {
    "total": 15,
    "avgConfidence": 0.82
  }
}
```

## Workflow

```bash
# Export for team
instinct-export --min-confidence=0.8 --output=team-share

# Share file
# (via git, slack, etc.)

# Teammate imports
instinct-import team-share.json
```

## Best Practices

- Export high-confidence instincts (>0.7)
- Filter to relevant tags for recipient
- Include context about your stack
- Update exports periodically
