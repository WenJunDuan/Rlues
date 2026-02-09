---
name: instinct-status
description: View learned instincts with confidence scores and usage stats
allowed-tools: ["Read"]
---

# instinct-status - View Learned Instincts

## Usage

```bash
instinct-status                    # View all instincts
instinct-status --tags=react       # Filter by tag
instinct-status --min-confidence=0.8   # High confidence only
instinct-status --recent           # Last 7 days
```

## Output Format

```
📊 Instinct Status

Total: 47 instincts | Avg Confidence: 0.78

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High Confidence (>0.8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CORS handling in Next.js API routes
   Confidence: 0.92 | Uses: 15 | Last: 2d ago
   Tags: [nextjs, api, cors, debugging]

✅ Prisma transaction patterns  
   Confidence: 0.88 | Uses: 8 | Last: 5d ago
   Tags: [prisma, database, transactions]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Medium Confidence (0.5-0.8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Supabase RLS policies
   Confidence: 0.72 | Uses: 5 | Last: 1w ago
   Tags: [supabase, security, rls]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Low Confidence (<0.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Edge function cold starts
   Confidence: 0.45 | Uses: 2 | Last: 2w ago
   Tags: [vercel, edge, performance]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evolution Candidates (ready to become skills)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 "authentication" cluster: 5 instincts, avg 0.85
   Run: /evolve --tags=authentication

🔄 "nextjs" cluster: 8 instincts, avg 0.79
   Run: /evolve --tags=nextjs
```

## Workflow

1. Review instinct status regularly
2. Identify high-confidence patterns
3. Evolve clusters into skills
4. Prune low-confidence/stale instincts
