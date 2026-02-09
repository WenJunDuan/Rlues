---
name: context7
description: |
  Intelligent library documentation fetcher using Context7 MCP tools.
  Auto-activates when: writing code with external libraries, needing API docs,
  setting up frameworks, or requesting code examples with specific packages.
  Fetches up-to-date, version-specific documentation to prevent hallucinated APIs.
---

# Context7 Documentation Skill

Fetch real-time, version-specific library documentation before implementing code.

## When to Use

This skill activates automatically when Claude detects:
- External library/framework usage (React, Next.js, Vue, FastAPI, etc.)
- API integration or documentation needs
- Framework setup or configuration
- Package-specific code examples

## Workflow

### Step 1: Resolve Library ID
```
Tool: mcp__context7__resolve-library-id
Input: { "libraryName": "<library-name>" }
Output: Context7-compatible library ID
```

### Step 2: Fetch Documentation
```
Tool: mcp__context7__get-library-docs
Input: { 
  "context7CompatibleLibraryID": "<resolved-id>",
  "topic": "<optional-topic-filter>",
  "tokens": 5000
}
```

### Step 3: Apply Documentation
- Base all code suggestions on retrieved documentation
- Use current API patterns, not training data

## Direct Library ID Syntax

Users can skip resolution with explicit IDs:
```
"use library /vercel/next.js for implementing app router"
"use library /supabase/supabase for authentication"
```

## Tool Limits

- Max 3 `resolve-library-id` calls per question
- Max 3 `get-library-docs` calls per question

## Common Libraries

| Library | Context7 ID |
|:---|:---|
| Next.js | /vercel/next.js |
| React | /facebook/react |
| Vue | /vuejs/vue |
| Supabase | /supabase/supabase |
| TailwindCSS | /tailwindlabs/tailwindcss |
