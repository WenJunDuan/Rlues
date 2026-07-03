---
name: context7
description: |
  Library documentation fetcher using Context7 CLI. Provides up-to-date,
  version-specific documentation for external libraries and frameworks.
  Uses `npx ctx7` CLI instead of MCP for lower context overhead.
context: fork
allowed-tools:
  - Bash(npx ctx7*)
  - Bash(npm *)
---

# Context7 Documentation Skill (CLI Version)

Fetch real-time, version-specific library documentation using Context7 CLI.

## When to Use

This skill activates automatically when detecting:
- External library/framework usage (React, Next.js, Vue, etc.)
- API integration or documentation needs
- Framework setup or configuration
- Package-specific code examples

## CLI Commands

### Search for Skills
```bash
npx ctx7 skills search <keyword>
```

### Install a Skill
```bash
npx ctx7 skills install /org/project <skill-name>
```

### Generate Custom Skill
```bash
npx ctx7 skills generate
```

### List Installed Skills
```bash
npx ctx7 skills list --claude
```

## Alternative: use context7 Prompt

If Context7 MCP is available, add to prompt:
```
Create a Next.js middleware for auth. use context7
```

Or specify exact library:
```
Implement Supabase auth. use library /supabase/supabase
```

## Common Library IDs

| Library | Context7 ID |
|:---|:---|
| Next.js | /vercel/next.js |
| React | /facebook/react |
| Vue | /vuejs/vue |
| Supabase | /supabase/supabase |
| TailwindCSS | /tailwindlabs/tailwindcss |
| Prisma | /prisma/prisma |
| tRPC | /trpc/trpc |

## Version-Specific Docs

Mention version in query:
```
How to set up Next.js 15 middleware? use context7
```

Context7 automatically matches the appropriate version.

## Workflow

1. **Identify Library** - Detect library from user query
2. **Search/Install** - Use CLI to get skill or search docs
3. **Apply Documentation** - Integrate docs into implementation
4. **Cite Source** - Reference Context7 ID used

## Fallback

If Context7 unavailable:
1. Check project's node_modules for types
2. Use official documentation links
3. Reference framework patterns from knowledge-base

## Integration with VibeCoding

- **vibe-plan**: Auto-fetch docs for planned libraries
- **design-mgr**: Get API patterns before design
- **impl-executor**: Reference docs during implementation
